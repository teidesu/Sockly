from rawige.app import Rawige
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
win = Rawige()
win.show()
sys.exit(app.exec())
