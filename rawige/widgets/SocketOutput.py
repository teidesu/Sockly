from __future__ import annotations
from PyQt5 import QtWidgets, QtGui, QtCore
from rawige.utils.helpers import iter_skip, MONOSPACE, get_font
from rawige.utils.highlighters import JsonHighlighter, SystemHighlighter, HexdumpHighlighter
from rawige.structs import MessageContent, MessageTypes


class SideArea(QtWidgets.QWidget):
    """
    Class representing a side area of an output widget.
    Contains block information and line numbers for each block

    Should only be used with SocketOutputText
    """
    def __init__(self, output: SocketOutputText):
        super().__init__()
        self.output = output
        self.output.blockCountChanged.connect(self.update_width)
        self.output.updateRequest.connect(self.update_on_scroll)
        self.update_width(1)

        self.font = get_font(MONOSPACE, 9)
        self.setFont(self.font)

    def update_width(self, num):
        """
        Update widget width for given number of lines (blocks)

        :param num: Number of lines
        """
        width = max(
            self.fontMetrics().width(str(num)),
            self.fontMetrics().width(' ->>')
        ) + 16
        if self.width() != width:
            self.setFixedWidth(width)

    def update_on_scroll(self, _, scroll):
        """
        Update widget for scrolled content

        :param scroll: Scroll amount
        """
        if self.isVisible():
            if scroll:
                self.scroll(0, scroll)
            else:
                self.update()

    @staticmethod
    def _create_items_iterator(items):
        """
        Creates side bar lines iterator for given items

        :param items: Block items
        :return: Side bar lines iterator
        """
        for i, it in enumerate(items):
            if i != 0 and it.type != MessageTypes.SYSTEM:
                yield ''
            pref = ['', 'J', 'X', 'B'][it.content.value]
            yield pref + ['<~>', '->>', '<<-'][it.type.value]
            yield from range(2, len(it.lines) + 1)

    def paintEvent(self, ev):
        block = self.output.firstVisibleBlock()
        height = self.fontMetrics().height()
        number = block.blockNumber()
        painter = QtGui.QPainter(self)
        painter.fillRect(ev.rect(), self.palette().color(QtGui.QPalette.Window))
        font = self.font
        bar = self._create_items_iterator(self.output.items)
        bar = iter_skip(bar, block.blockNumber())

        while block.isValid():
            offset = self.output.contentOffset()
            block_geometry = self.output.blockBoundingGeometry(block)
            block_top = block_geometry.translated(offset).top()
            number += 1

            rect = QtCore.QRect(0, block_top + 2, self.width() - 5, height)

            try:
                text = next(bar)
            except StopIteration:
                break

            painter.setFont(font)
            painter.drawText(rect, QtCore.Qt.AlignRight, str(text))

            if block_top > ev.rect().bottom():
                break

            block = block.next()
        painter.end()


class SocketOutputText(QtWidgets.QPlainTextEdit):
    def __init__(self, parent):
        super().__init__()

        self.font = get_font(MONOSPACE, 9)
        self.setFont(self.font)
        self.setReadOnly(True)
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.parent = parent

    @property
    def items(self):
        return self.parent.items


class SocketOutput(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.layt = QtWidgets.QHBoxLayout(self)
        self.setLayout(self.layt)

        self.text = SocketOutputText(self)
        self.side = SideArea(self.text)
        self.layt.addWidget(self.side)
        self.layt.addWidget(self.text)
        self.layt.setSpacing(0)
        self.layt.setContentsMargins(4, 4, 4, 4)

        self.items = []

        self._lazy_highlighters = {}
        self._lazy_formatters = {}

    def _get_highlighter(self, kind, typ):
        if (kind, typ) not in self._lazy_highlighters:
            hl = None
            if typ == MessageTypes.SYSTEM:
                hl = SystemHighlighter()
            if kind in (MessageContent.JSON, MessageContent.BSON):
                hl = JsonHighlighter()
            if kind == MessageContent.BINARY:
                hl = HexdumpHighlighter()
            self._lazy_highlighters[(kind, typ)] = hl
        return self._lazy_highlighters[(kind, typ)]

    def notify_set_changed(self):
        text = ''
        highlight = []

        for i, it in enumerate(self.items):
            if i != 0:
                text += '\n\n' if it.type != MessageTypes.SYSTEM else '\n'
            part = '\n'.join(it.lines)
            hl = self._get_highlighter(it.content, it.type)
            if hl:
                highlight.append((hl, part, len(text)))
            text += part

        self.text.setPlainText(text)
        for i, (hl, part, offy) in enumerate(highlight):
            hl.highlight(part, self.text.document(), offy, i == 0)

        self.side.update()
        self.text.verticalScrollBar().setValue(self.text.verticalScrollBar().maximum())