from PyQt5.QtGui import QTextCharFormat, QTextCursor, QFont, QColor
from collections import namedtuple
from PyQt5.QtCore import Qt
import re

HighlightingRule = namedtuple('HighlightingRule', 'pattern format group')


class SimpleHighlighter:
    def __init__(self):
        self.rules = []
        self.init()

    def init(self):
        raise NotImplemented()

    def set_rule(self, pattern, fmt, group=0):
        rule = HighlightingRule(pattern, fmt, group)
        self.rules.append(rule)

    def highlight(self, text, document, offset=0, reset=True):
        if reset:
            self.reset(document)
        for pattern, fmt, group in self.rules:
            for m in re.finditer(pattern, text):
                s, e = m.span(group)
                if s == e:
                    continue
                cur = QTextCursor(document)
                cur.setPosition(offset + s, QTextCursor.MoveAnchor)
                cur.setPosition(offset + e, QTextCursor.KeepAnchor)
                cur.setCharFormat(fmt)
                # self.setFormat(index, length, fmt)
                # index = expression.indexIn(text, index + length)

    @staticmethod
    def reset(document):
        cur = QTextCursor(document)
        cur.select(QTextCursor.Document)
        cur.setCharFormat(QTextCharFormat())


class JsonHighlighter(SimpleHighlighter):
    def init(self):
        key_fmt = QTextCharFormat()
        key_fmt.setForeground(Qt.blue)
        self.set_rule(re.compile(r'("(?:[^"\\]|\\.)*?")\s*?:'), key_fmt, 1)

        val_str_fmt = QTextCharFormat()
        val_str_fmt.setForeground(Qt.red)
        self.set_rule(re.compile(r':\s*?("(?:[^"\\]|\\.)*?")'), val_str_fmt, 1)

        val_num_fmt = QTextCharFormat()
        val_num_fmt.setForeground(Qt.darkGreen)
        self.set_rule(re.compile(r':\s*?(\b(\d+(?:\.\d+)?)\b)'), val_num_fmt, 1)

        val_bool_fmt = QTextCharFormat()
        val_bool_fmt.setForeground(Qt.darkBlue)
        val_bool_fmt.setFontWeight(QFont.Bold)
        self.set_rule(re.compile(r':\s*?(\b(true|false)\b)'), val_bool_fmt, 1)

        val_null_fmt = QTextCharFormat()
        val_null_fmt.setForeground(Qt.darkMagenta)
        val_null_fmt.setFontWeight(QFont.Bold)
        self.set_rule(re.compile(r':\s*?(\b(null)\b)'), val_null_fmt, 1)

        escaped_fmt = QTextCharFormat()
        escaped_fmt.setForeground(QColor('#6e3803'))
        self.set_rule(re.compile(r'\\u[0-f]{4}|\\x[0-f]{2}|\\.'), escaped_fmt)


class SystemHighlighter(SimpleHighlighter):
    def init(self):
        base_fmt = QTextCharFormat()
        base_fmt.setFontWeight(QFont.DemiBold)
        self.set_rule(re.compile(r'.*'), base_fmt)

        err_fmt = QTextCharFormat()
        err_fmt.setForeground(Qt.red)
        err_fmt.setFontWeight(QFont.Bold)
        self.set_rule(re.compile(r'^(Error|Rejected): '), err_fmt)
        self.set_rule(re.compile(r'^HTTP/\d+(?:\.\d+)?\s*(\d+.*?)$', re.M), err_fmt, 1)

        conn_fmt = QTextCharFormat()
        conn_fmt.setForeground(Qt.darkGreen)
        conn_fmt.setFontWeight(QFont.Bold)
        self.set_rule(re.compile(r'\bConnected\b'), conn_fmt)

        dconn_fmt = QTextCharFormat()
        dconn_fmt.setForeground(Qt.darkRed)
        dconn_fmt.setFontWeight(QFont.Bold)
        self.set_rule(re.compile(r'\bDisconnected\b'), dconn_fmt)

        pconn_fmt = QTextCharFormat()
        pconn_fmt.setForeground(Qt.darkYellow)
        pconn_fmt.setFontWeight(QFont.Bold)
        self.set_rule(re.compile(r'\b(Re)?[cC]onnecting(?: in \d+(?:\.\d+)?)?\b'), pconn_fmt)

        welcome_fmt = QTextCharFormat()
        welcome_fmt.setForeground(QColor('#ff8324'))
        welcome_fmt.setFontWeight(QFont.ExtraBold)
        self.set_rule(re.compile(r'^Welcome to (Rawige)$'), welcome_fmt, 1)


class HexdumpHighlighter(SimpleHighlighter):
    def init(self):
        grp_fmt = QTextCharFormat()
        grp_fmt.setForeground(Qt.darkCyan)
        grp_fmt.setFontWeight(QFont.Bold)
        self.set_rule(re.compile(r'^[0-f]*', re.M), grp_fmt)

        dat_fmt = QTextCharFormat()
        dat_fmt.setFontWeight(QFont.DemiBold)
        self.set_rule(re.compile(r' ( [0-f]{2})+ {2}'), dat_fmt)
