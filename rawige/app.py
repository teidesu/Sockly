from PyQt5 import QtWidgets, QtGui, QtCore
from rawige.widgets.RawigeTab import RawigeTab


class Rawige(QtWidgets.QMainWindow):
    broadcast = QtCore.pyqtSignal(str, dict, int)

    def __init__(self):
        super().__init__()
        self.widget = QtWidgets.QWidget(self)
        self.layout = QtWidgets.QVBoxLayout(self.widget)

        self.tabs_widget = QtWidgets.QTabWidget(self.widget)
        self.layout.addWidget(self.tabs_widget)

        self.add_tab_btn = QtWidgets.QToolButton(self.widget)
        self.add_tab_btn.setText('+')
        self.add_tab_btn.clicked.connect(self.add_tab)
        self.tabs_widget.setCornerWidget(self.add_tab_btn)
        self.uid = 0
        self.broadcast.connect(self.on_broadcast)
        self.add_tab()

        copyright = QtWidgets.QLabel()
        copyright.setText('by teidesu')
        copyright.setAlignment(QtCore.Qt.AlignRight)
        self.layout.addWidget(copyright)

        self.setCentralWidget(self.widget)
        self.resize(1500, 800)
        self.setWindowTitle('Rawige — the WebSocket client')

    def add_tab(self):
        page = RawigeTab(self, self.uid)
        self.uid += 1
        i = self.tabs_widget.addTab(page, '[I] New tab')

        page.title_changed.connect(lambda s: self.tabs_widget.setTabText(i, s))
        self.tabs_widget.setCurrentIndex(i)
        self.update_close_buttons()

    def update_close_buttons(self):
        c = self.tabs_widget.count()
        bar = self.tabs_widget.tabBar()
        if c == 1:
            bar.setTabButton(0, 1, None)
            return
        for i in range(c):
            close_btn = QtWidgets.QToolButton()
            # noinspection PyTypeChecker
            close_btn.clicked.connect(lambda _, ii=i: (
                self.tabs_widget.widget(ii).cleanup(),
                self.tabs_widget.removeTab(ii),
                self.update_close_buttons()
            ))
            close_btn.setText('x')
            self.tabs_widget.tabBar().setTabButton(i, QtWidgets.QTabBar.ButtonPosition.RightSide, close_btn)

    def on_broadcast(self, kind, data, sender):
        for i in range(self.tabs_widget.count()):
            self.tabs_widget.widget(i).broadcast.emit(kind, data, sender)
