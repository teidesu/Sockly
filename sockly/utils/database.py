import os
import os.path
from sockly.utils.db_versions import DB_VERSIONS
from sockly.utils.sqlite import Database
from platform import system as __platform
platform = __platform()


def _db_path():
    if platform == 'Windows':
        return os.path.join(os.environ['APPDATA'], 'sockly.db')
    elif platform == 'Linux':
        return os.path.expanduser('~/.config/sockly.db')
    else:
        return os.path.expanduser('~/sockly.db')


class SocklyDB(Database):
    def __init__(self, path=_db_path(), v=1):
        super().__init__(path, v, DB_VERSIONS)

    def get_int(self, key, default=0):
        ret = self.get(key, None)
        if ret is None:
            return default
        try:
            return int(ret)
        except:
            return default

    def set_int(self, key, value):
        self.set(key, int(value))

    def get_blob(self, key, default=b''):
        ret = self.query('select v from config_blobs where k = ?', str(key))
        if not ret:
            return default
        return bytes(ret[0]['v'])

    def set_blob(self, key, value):
        self.query('insert into config_blobs (k, v) values (?, ?) on conflict(k) do update set v = excluded.v',
                   str(key), value)

    def get(self, key, default=None):
        ret = self.query('select v from config where k = ?', str(key))
        if not ret:
            return default
        return ret[0]['v']

    def set(self, key, value):
        self.query('insert into config (k, v) values (?, ?) on conflict(k) do update set v = excluded.v',
                   str(key), str(value))
