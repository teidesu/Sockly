import pickle
import traceback

from rawige.structs import SocketMessage


def assert_(predicate):
    if not predicate:
        raise AssertionError()


def validate_session(filename):
    try:
        with open(filename, 'rb') as f:
            data = pickle.load(f)
            for key, typ in (
                    ('name', str),
                    ('url', str),
                    ('headers', str),
                    ('proxy_enabled', bool),
                    ('proxy', str),
                    ('compression', bool),
                    ('reconnect', bool),
                    ('input', str),
                    ('mode', str),
                    ('msg_compression', bool),
            ):
                assert_(key in data)
                assert_(type(data[key]) is typ)
            for key, validate in (
                    ('history', lambda t: type(t) is str),
                    ('favourites', lambda t: type(t) is dict and
                                             'name' in t and
                                             'value' in t and
                                             type(t['name']) is str and
                                             type(t['value']) is str),
                    ('output', lambda t: type(t) is SocketMessage),
            ):
                assert_(key in data)
                assert_(type(data[key]) is list)
                assert_(all((validate(t) for t in data[key])))
            return True, data
    except AssertionError:
        return False, 'Session is broken: \n' + traceback.format_exc()
    except pickle.PickleError:
        return False, 'Session parse failed'
    except PermissionError:
        return False, 'Permission denied'
    except FileNotFoundError:
        return False, 'File not found'


def create_session(tab):
    return {
        'name': tab.tabname_input.text(),
        'url': tab.url_input.text(),
        'headers': tab.headers_input.toPlainText(),
        'proxy_enabled': tab.proxy_enabled.isChecked(),
        'proxy': tab.proxy_input.text(),
        'compression': tab.conn_use_compression.isChecked(),
        'reconnect': tab.conn_persist.isChecked(),
        'history': tab.history,
        'favourites': tab.fav,
        'output': tab.output.items,
        'input': tab.input.toPlainText(),
        'mode': tab.current_send_mode,
        'msg_compression': tab.use_compression.isChecked()
    }


def apply_session(tab, d):
    for key, attr in (
            ('name', 'tabname_input'),
            ('url', 'url_input'),
            ('proxy', 'proxy_input'),
            ('name', 'tabname_input'),
    ):
        getattr(tab, attr).setText(d[key])
    tab.headers_input.setPlainText(d['headers'])
    tab.input.setPlainText(d['input'])
    tab.fav = d['favourites']
    tab.output.items = d['output']
    tab.history = d['history']

    for key, attr in (
            ('proxy_enabled', 'proxy_enabled'),
            ('compression', 'conn_use_compression'),
            ('reconnect', 'conn_persist'),
            ('msg_compression', 'use_compression'),
    ):
        getattr(tab, attr).setChecked(d[key])

    for i in (
            'plain_text',
            'binary',
            'hex',
            'base64',
            'json',
            'bson',
    ):
        getattr(tab, 'send_{}_radio'.format(i)).setChecked(i == d['mode'])

    tab.update_title()
    tab.update_history()
    tab.update_favs()
    tab.output.notify_set_changed()
