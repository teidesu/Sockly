import base64
import os
import os.path
import pickle

import bson
from PyQt5 import QtWidgets, QtCore
from sockly.layouts.sockly_tab import layout_tab
from sockly.structs import SocketMessage, MessageTypes, MessageContent
from sockly.utils.SocketThread import SocketThread
from sockly.utils.database import SocklyDB
from sockly.utils.helpers import hexdump, ellipsize, debounce
from sockly.utils.session_manager import validate_session, apply_session, create_session

try:
    import ujson as json
except ImportError:
    import json


class SocklyTab(QtWidgets.QWidget):
    title_changed = QtCore.pyqtSignal(str)
    broadcast = QtCore.pyqtSignal(str, dict, int)

    def __init__(self, parent, uid):
        super().__init__(parent)
        self.parent = parent
        self.uid = uid
        self.history = []
        self.fav = []
        self.broadcast.connect(self.on_broadcast)
        self.state = 'idle'
        self.worker = None
        self.selected_fav = None
        self.filename = None
        self.database = SocklyDB()
        self._internal_splitter_update = False
        layout_tab(self)
        self.input.fileDropped.connect(self._input_file_dropped)
        self.clear_output()
        self.load_settings()

    def _broadcast(self, kind, data):
        self.parent.broadcast.emit(kind, data, self.uid)

    def load_settings(self):
        for k in ('main', 'right'):
            wid = getattr(self, k + '_splitter')
            wid.splitterMoved.connect(lambda _, __: self._on_splitter_update())
            r = self.database.get_blob(k + '_splitter', None)
            if r is not None:
                wid.restoreState(r)

        for attr in ('show_http', 'show_alive_checks', 'decode_bson'):
            wid = getattr(self, attr)
            wid.setChecked(bool(self.database.get_int(attr, 1)))
            wid.stateChanged.connect(lambda t, a=attr: (
                self.database.set_int(a, int(t)),
                self._broadcast('checkbox', {'attr': a, 'val': t})
            ))

    @debounce(0.25)
    def _on_splitter_update(self):
        main_val = self.main_splitter.saveState()
        right_val = self.right_splitter.saveState()

        self._broadcast('splitters', {
            'main': main_val,
            'right': right_val,
        })

        self.database.set_blob('main_splitter', bytes(main_val))
        self.database.set_blob('right_splitter', bytes(right_val))

    def error_state_changed(self, err):
        self.toggle_connect_btn.setEnabled(not err)

    def cleanup(self):
        if self.worker:
            self.worker.close()
            self.worker.terminate()

    def set_input(self, data):
        self.input.setPlainText(data)

    def clear_hist(self):
        self.history.clear()
        self.update_history()

    def add_history_item(self, text):
        if text in self.history:
            self.history.remove(text)
        self.history.insert(0, text)
        self.update_history()

    def save(self):
        if not self.filename:
            self.filename = self.save_as()
        else:
            with open(self.filename, 'wb') as f:
                pickle.dump(create_session(self), f)

    def on_broadcast(self, kind, data, sender):
        if sender == self.uid:
            return
        if kind == 'splitters':
            self.main_splitter.restoreState(data['main'])
            self.right_splitter.restoreState(data['right'])
        if kind == 'checkbox':
            getattr(self, data['attr']).setChecked(data['val'])

    def save_as(self):
        fname, ok = QtWidgets.QFileDialog().getSaveFileName(self, 'Choose file', filter='Sockly session (*.sly);;'
                                                                                        ' All files (*.*)')
        if not ok:
            return None
        with open(fname, 'wb') as f:
            pickle.dump(create_session(self), f)
        return fname

    def open(self):
        fname, ok = QtWidgets.QFileDialog().getOpenFileName(self, 'Choose file', filter='Sockly session (*.sly);;'
                                                                                        ' All files (*.*)')
        if not ok:
            return
        self._load_session(fname, True)

    def dragEnterEvent(self, ev):
        if ev.mimeData().text().startswith('file://'):
            ev.accept()
        else:
            ev.reject()

    def dropEvent(self, ev):
        self._load_session(ev.mimeData().text()[7:].strip(), True)

    def _load_session(self, filename, error_window=False):
        ok, res = validate_session(filename)
        if not ok:
            if error_window:
                a = QtWidgets.QMessageBox(self)
                a.setWindowTitle("Session failed to load")
                a.setIcon(QtWidgets.QMessageBox.Warning)
                a.setText("%s does not seem to be a valid Sockly session." % os.path.split(filename)[-1])
                a.setDetailedText(res)
                a.show()
        else:
            self.filename = filename
            apply_session(self, res)

    def toggle_connect(self):
        if self.state == 'idle':
            self.worker = SocketThread(self._create_worker_config())
            self.worker.signal.connect(self.on_worker_event)
            self.worker.start()
        elif self.state == 'connected':
            self.worker.close()
        elif self.state in ('connecting', 'backoff'):
            self.on_disconnect()
            self.add_system('Connection dropped by user')
            self.worker.terminate()

    def on_worker_event(self, ev):
        if ev.name == 'connecting':
            self.send_button.setEnabled(False)
            self.toggle_connect_btn.setText('Cancel')
            self.toggle_controls(False)
            self.state = 'connecting'
            self.add_system('Connecting...')
            self.open_btn.setEnabled(False)
            self.update_title()
        elif ev.name == 'ready':
            self.send_button.setEnabled(True)
            self.toggle_connect_btn.setText('Disconnect')
            self.state = 'connected'
            self.add_system('Connected!', *(format_response(ev.response) if self.show_http.isChecked() else []))
        elif ev.name == 'back_off':
            self.state = 'backoff'
            self.send_button.setEnabled(False)
            self.toggle_connect_btn.setText('Cancel')
            self.add_system('Reconnecting in ' + str(round(ev.delay, 1)))
        elif ev.name == 'rejected':
            self.add_error('Rejected: ' + ev.reason,
                           *(format_response(ev.response) if self.show_http.isChecked() else []))
        elif ev.name == 'connect_fail':
            self.on_disconnect()
            self.add_error(ev.reason)
        elif ev.name == 'poll' and self.show_alive_checks.isChecked():
            self.add_system('->> Poll')
        elif ev.name == 'pong' and self.show_alive_checks.isChecked():
            self.add_system('<<- Pong: ' + str(ev.data))
        elif ev.name == 'ping' and self.show_alive_checks.isChecked():
            self.add_system('<<- Ping: ' + str(ev.data))
        elif ev.name == 'text' or ev.name == 'binary':
            self.add_incoming(ev.text if ev.name == 'text' else ev.data)
        elif ev.name == 'disconnected':
            self.on_disconnect()
            self.add_system('Disconnected ({}), {}'.format(ev.reason, 'graceful' if ev.graceful else 'failure'))

    def on_disconnect(self):
        self.send_button.setEnabled(False)
        self.toggle_connect_btn.setEnabled(True)
        self.toggle_connect_btn.setText('Connect')
        self.open_btn.setEnabled(True)
        self.state = 'idle'
        self.toggle_controls(True)
        self.update_title()

    def clear_output(self):
        self.output.items.clear()
        self.output.notify_set_changed()
        self.add_system('Welcome to Sockly')

    def toggle_controls(self, val):
        for i in (
                'conn_use_compression',
                'conn_persist',
                'url_input',
                'headers_input',
                'proxy_input'
        ):
            getattr(self, i).setEnabled(val)

    def _create_headers(self):
        ret = {}
        for line in self.headers_input.toPlainText().split('\n'):
            if line:
                k, *v = line.split(': ')
                ret[k] = ': '.join(v)
        return ret

    def _create_worker_config(self):
        return {
            'url': self.url_input.text(),
            'headers': self._create_headers(),
            'proxy': self.proxy_input.text() if self.proxy_enabled.isChecked() else None,
            'compress': self.conn_use_compression.isChecked(),
            'persist': self.conn_persist.isChecked()
        }

    @property
    def current_send_mode(self):
        for i in (
                'plain_text',
                'binary',
                'hex',
                'base64',
                'json',
                'bson',
        ):
            if getattr(self, 'send_{}_radio'.format(i)).isChecked():
                return i
        return None

    def send(self):
        if not self.worker or not self.worker.conn.is_active:
            return self.add_error('connection is not active')
        data = self.input.toPlainText()
        res = self._validate(data)
        if isinstance(res, ValueError):
            return self.add_error(res.args[0])
        self.add_history_item(data)
        self.worker.send(res)
        sm = self.current_send_mode
        if sm == 'plain_text':
            content = MessageContent.PLAIN
            data = data.split('\n')
        elif sm == 'json':
            content = MessageContent.JSON
            data = json.dumps(json.loads(data), indent=2).split('\n')
        elif sm == 'bson':
            content = MessageContent.BSON
            data = json.dumps(json.loads(data), indent=2).split('\n')
        else:
            content = MessageContent.BINARY
            data = hexdump(res)
        self.output.items.append(SocketMessage(
            MessageTypes.OUTGOING,
            data,
            content
        ))
        self.output.notify_set_changed('append')

    def _validate(self, data):
        sm = self.current_send_mode
        if sm == 'plain_text':
            return data
        if sm == 'binary':
            return data.encode()
        if sm == 'hex':
            try:
                return bytes.fromhex(data)
            except ValueError:
                return ValueError('Invalid hex!')
        if sm == 'base64':
            try:
                return base64.b64decode(data.encode())
            except:
                return ValueError('Invalid Base64!')
        if sm == 'json':
            try:
                return json.dumps(json.loads(data))  # validate and minify
            except:
                return ValueError('Invalid JSON!')
        if sm == 'bson':
            try:
                return bson.dumps(json.loads(data))
            except:
                return ValueError('Invalid JSON!')

    def add_system(self, text, *additional):
        self.output.items.append(SocketMessage(
            MessageTypes.SYSTEM,
            [text, *additional],
            MessageContent.PLAIN
        ))
        self.output.notify_set_changed('append')

    def add_error(self, text, *additional):
        self.add_system('Error: ' + text, *additional)

    def add_incoming(self, data):
        self.output.items.append(SocketMessage(
            MessageTypes.INCOMING,
            *self.parse_data(data)
        ))
        self.output.notify_set_changed('append')

    def on_json(self, enabled):
        if enabled:
            self.input.jhl.highlight(self.input.toPlainText(), self.input.document())
        else:
            self.input.jhl.reset(self.input.document())

    def on_bson(self, enabled):
        self.on_json(enabled)

    def add_fav(self):
        d = self.input.toPlainText()
        if not d:
            return
        name, ok = QtWidgets.QInputDialog.getText(self, "Creating favourite entry", "Please enter entry name")
        if not ok:
            return
        self.fav.insert(0, {
            'name': name,
            'value': d
        })
        self.update_favs()

    def del_fav(self):
        if not self.selected_fav:
            return
        self.fav.remove({
            'name': self.selected_fav.text(),
            'value': self.selected_fav.value
        })
        self.del_fav_btn.setEnabled(False)
        self.set_fav_btn.setEnabled(False)
        self.selected_fav = None
        self.update_favs()

    def set_fav(self):
        if not self.selected_fav:
            return
        self.set_input(self.selected_fav.value)

    def on_fav_item_click(self, item):
        self.selected_fav = item
        self.del_fav_btn.setEnabled(True)
        self.set_fav_btn.setEnabled(True)

    def update_favs(self):
        self.favourites_list.clear()
        for item in self.fav:
            it = QtWidgets.QListWidgetItem(item['name'])
            it.value = item['value']
            self.favourites_list.addItem(it)

    def update_history(self):
        self.history_list.clear()
        self.history_list.addItems(self.history)

    def update_title(self):
        self.title_changed.emit(self.generate_title())

    def generate_title(self):
        url = self.url_input.text()
        name = self.tabname_input.text()
        if url == '' and name == '':
            return '[I] New tab'
        pref = '[I] ' if self.state == 'idle' else '[A] '
        ret = ''
        if url.startswith('ws://'):
            self.error_state_changed(False)
            ret = pref + ellipsize(url[5:], 30)
        if url.startswith('wss://'):
            self.error_state_changed(False)
            ret = pref + ellipsize(url[6:], 30)
        if not ret:
            self.error_state_changed(True)
            ret = '-- ERROR --'
        if name != '':
            ret = pref + ellipsize(name, 30)
        return ret

    def _input_file_dropped(self, filename):
        with open(filename, 'rb') as f:
            data = f.read()
            sm = self.current_send_mode
            if sm in ('plain_text', 'binary'):
                try:
                    self.input.insertPlainText(data.decode('U8'))
                except:
                    pass
            elif sm == 'hex':
                self.input.insertPlainText(data.hex())
            elif sm == 'base64':
                self.input.setPlainText(base64.b64encode(data).decode())
            elif sm == 'json':
                try:
                    self.input.insertPlainText(json.dumps(json.loads(data, encoding='U8'), indent=2))
                except:
                    pass
            elif sm == 'bson':
                try:
                    self.input.insertPlainText(json.dumps(bson.loads(data), indent=2))
                except:
                    pass

    def parse_data(self, data):
        text = []
        typ = None

        if type(data) is bytes:
            try:
                if not self.decode_bson.isChecked():
                    raise Exception()
                text = json.dumps(bson.loads(data), indent=2).split('\n')
                typ = MessageContent.BSON
            except:
                text = hexdump(data)
                typ = MessageContent.BINARY
        else:
            try:
                text = json.dumps(json.loads(data), indent=2).split('\n')
                typ = MessageContent.JSON
            except:
                text = data.split('\n')
                typ = MessageContent.PLAIN

        return text, typ


def format_response(rsp):
    return rsp.raw.decode().replace('\r\n', '\n').split('\n')
