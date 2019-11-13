from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtCore import Qt, pyqtSignal

TAB_SIZE = 2


class BetterPlainTextEdit(QPlainTextEdit):
    fileDropped = pyqtSignal(str)
    textEdited = pyqtSignal()

    def __init__(self, *args):
        super().__init__(*args)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        text = e.mimeData().text()
        if text.startswith('file://'):
            filename = text[7:]
            self.fileDropped.emit(filename.strip())
        else:
            self.insertPlainText(text)

    def keyPressEvent(self, ev):
        key = ev.key()
        if key == Qt.Key_Tab:
            self.insertPlainText(' ' * TAB_SIZE)
        else:
            super().keyPressEvent(ev)
        self.textEdited.emit()
