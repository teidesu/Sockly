from PyQt5.QtCore import QThread, pyqtSignal
import lomond
from lomond.persist import persist


class SocketThread(QThread):
    signal = pyqtSignal(lomond.websocket.events.Event)

    def __init__(self, config: dict):
        super().__init__()
        self.conn: lomond.WebSocket = None
        self.config = config

    def run(self):
        self.conn = lomond.WebSocket(self.config['url'], proxies={
            'http': self.config['proxy'],
            'https': self.config['proxy']
        } if self.config['proxy'] else None, compress=self.config['compress'])
        for k, v in self.config['headers'].items():
            self.conn.add_header(k.encode(), v.encode())
        conn = persist(self.conn) if self.config['persist'] else self.conn
        for ev in conn:
            self.signal.emit(ev)

    def send(self, data, compressed=False):
        if type(data) is bytes:
            self.conn.send_binary(data, compress=compressed)
        else:
            self.conn.send_text(data, compress=compressed)

    def close(self, code=1000, reason='goodbye'):
        self.conn.close(code, reason)
