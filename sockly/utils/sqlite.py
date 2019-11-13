"""
Dead simple thread-safe synchronous sqlite wrapper with minimum overhead and versioning support

Versioning is executed one-by-one starting from DB version to app version.
E.g. upgrade 1 -> 3 means executing 2nd, then 3rd versions' rulesets
When database is just created or first used with wrapper v0 is implied.

Database object handles multiple threads, so no need to re-create it for each.

Usage:
versions = {
  1: [
    'create table foo (bar int)'
  ]
}
db = Database('file.db')
db.query('insert into foo (bar) values (?)', 42)
db.query('insert into foo (bar) values (?)', 8)
db.query('select * from foo')
# [Row(bar=42), Row(bar=8)]
db.query('select * from foo', one=True)
# Row(bar=42)
def foo():
  db.query('delete from foo')
from threading import Thread
Thread(target=foo).start()
# no error!

(c) teidesu 2019. This file is licensed under GPLv3
"""
import sqlite3
import threading


class BetterRow(sqlite3.Row):
    def dict(self):
        if not hasattr(self, '__dict_cache'):
            d = {}
            for k in self.keys():
                d[k] = self[k]
            self.__dict_cache = d
        return self.__dict_cache

    def items(self):
        return self.dict().items()

    def values(self):
        return self.dict().values()

    def __repr__(self):
        if not hasattr(self, '__repr_cache'):
            items = []
            for k, v in self.items():
                items.append(k + '=' + repr(v))
            self.__repr_cache = f'Row({", ".join(items)})'
        return self.__repr_cache


# noinspection SqlNoDataSourceInspection
class Database:
    def __init__(self, filename=":memory:", v=1, init=None, rsp_dict=True):
        self.filename = filename
        self.init = init
        self.v = v
        self.rsp_dict = rsp_dict
        self.connections = {}

        self.query('create table if not exists __desu_wrapper__ (k text, v text)')
        self.query('create unique index if not exists __desu_wrapper_uindex__ on __desu_wrapper__ (k)')
        self._perform_update()

    def _perform_update(self):
        current_v = int(self._internal_store_get('version', 0))
        if current_v < self.v:
            for new in range(current_v + 1, self.v + 1):
                if new not in self.init:
                    raise ValueError('Cannot perform upgrade from {} to {}: no ruleset given'.format(new - 1, new))
                for q in self.init[new]:
                    self.query(q)
        self._internal_store_set('version', self.v)

    def _internal_store_get(self, key, default=None):
        ret = self.query('select v from __desu_wrapper__ where k = ?', str(key))
        if not ret:
            return default
        return ret[0]['v']

    def _internal_store_set(self, key, value):
        self.query('insert into __desu_wrapper__ (k, v) values (?, ?) on conflict(k) do update set v = excluded.v',
                   str(key), str(value))

    def _prepare_connection(self):
        tid = threading.get_ident()
        if tid not in self.connections:
            conn = sqlite3.connect(self.filename, check_same_thread=False)
            if self.rsp_dict:
                conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            self.connections[tid] = (conn, cur)
        return self.connections[tid]

    def __del__(self):
        for conn, cur in self.connections.values():
            cur.close()
            conn.close()

    def query(self, q, *params, one=False):
        conn, cur = self._prepare_connection()
        cur.execute(q, params)
        conn.commit()
        if one:
            return cur.fetchone()
        else:
            return cur.fetchall()

    def query_many(self, q):
        conn, cur = self._prepare_connection()
        cur.executemany(q, ())
        conn.commit()

    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d


export = Database
