from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtCore import Qt, pyqtSignal

TAB_SIZE = 2


class BetterPlainTextEdit(QPlainTextEdit):
    textEdited = pyqtSignal()

    def keyPressEvent(self, ev):
        key = ev.key()
        if key == Qt.Key_Tab:
            self.insertPlainText(' ' * TAB_SIZE)
        else:
            super().keyPressEvent(ev)
        self.textEdited.emit()
