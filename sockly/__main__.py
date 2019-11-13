from sockly.app import Sockly
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
win = Sockly()
win.show()
sys.exit(app.exec())
