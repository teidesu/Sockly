from functools import lru_cache
from threading import Timer
from PyQt5.QtGui import QFontDatabase, QFont
from PyQt5.QtWidgets import QLabel, QPushButton


def iter_skip(itr, skip=0):
    """
    Returns an iterator that skips `skip` items in `itr` iterator
    """
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
def get_font(fonts, *args):
    """
    Get first available font from available.
    Idk how but it works at least for monospaced fonts
    """
    db = QFontDatabase()
    for it in fonts:
        if len(db.writingSystems(it)) > 0:
            return QFont(it, *args)
    return None


def ellipsize(string, max_chars=60):
    """
    Ellipsize a string by char count
    """
    if len(string) <= max_chars:
        return string
    return string[:max_chars - 3] + '...'


def label(text, *args):
    """
    Alias for creating a label
    """
    widget = QLabel(*args)
    widget.setText(text)
    return widget


def button(text, onclick):
    """
    Alias for creating a button
    """
    widget = QPushButton()
    widget.setText(text)
    widget.clicked.connect(onclick)
    return widget


def hexdump(src, length=16, sep='.'):
    """
    Took from some gist and edited a bit. Hexdumps a binary data from `src`

    :param src:
    :param length:
    :param sep:
    :return:
    """
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


def debounce(wait):
    """
    Took from some gist, idr. Does exactly the same as lodash's debounce

    :param wait: number of seconds to debounce
    :return: decorator
    """
    def decorator(fn):
        def debounced(*args, **kwargs):
            def call_it():
                fn(*args, **kwargs)
            try:
                debounced.t.cancel()
            except AttributeError:
                pass
            debounced.t = Timer(wait, call_it)
            debounced.t.start()
        return debounced
    return decorator
