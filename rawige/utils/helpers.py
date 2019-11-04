from functools import lru_cache

from PyQt5.QtGui import QFontDatabase, QFont
from PyQt5.QtWidgets import QLabel, QPushButton


def iter_skip(itr, skip=0):
    i = 0
    while i < skip:
        next(itr)
        i += 1
    yield from itr


MONOSPACE = (
    'Fira Code',
    'Fira Mono',
    'Source Code Pro',
    'Hack',
    'Noto Mono',
    'Ubuntu Mono',
    'Consolas',
    'Courier',
    'monospace'
)


@lru_cache()
def get_font(ar, *args):
    db = QFontDatabase()
    for it in ar:
        if len(db.writingSystems('monospace')) > 0:
            return QFont(it, *args)
    return None


def ellipsize(string, max_chars=60):
    if len(string) <= max_chars:
        return string
    return string[:max_chars - 3] + '...'


def label(text, *args):
    el = QLabel(*args)
    el.setText(text)
    return el


def button(text, onclick):
    b = QPushButton()
    b.setText(text)
    b.clicked.connect(onclick)
    return b


def hexdump(src, length=16, sep='.'):
    filter_ = ''.join(
        [(len(repr(chr(x))) == 3) and chr(x) or sep for x in range(256)]
    )
    lines = []
    for c in range(0, len(src), length):
        chars = src[c:c + length]
        hexstr = ' '.join(["%02x" % ord(x) for x in chars]) if type(chars) is str else ' '.join(
            ['{:02x}'.format(x) for x in chars])
        printable = ''.join(["%s" % ((ord(x) <= 127 and filter_[ord(x)]) or sep) for x in chars]) if type(
            chars) is str else ''.join(['{}'.format((x <= 127 and filter_[x]) or sep) for x in chars])
        lines.append("%08x:  %-*s  |%s|" % (c, length * 3, hexstr, printable))
    return lines
