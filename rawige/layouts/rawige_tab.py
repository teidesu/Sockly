from PyQt5 import QtWidgets

from rawige.structs import MessageTypes, SocketMessage, MessageContent
from rawige.utils.helpers import MONOSPACE, get_font, label, ellipsize, button
from rawige.utils.highlighters import JsonHighlighter
from rawige.widgets.BetterPlainTextEdit import BetterPlainTextEdit
from rawige.widgets.SocketOutput import SocketOutput


def layout_tab(self: QtWidgets.QWidget):
    self.setAcceptDrops(True)
    self.widget = QtWidgets.QWidget(self)
    self.layout = QtWidgets.QHBoxLayout(self.widget)
    self.setLayout(self.layout)
    self.main_splitter = QtWidgets.QSplitter()
    self.main_splitter.setContentsMargins(0, 0, 0, 0)

    left_layt = QtWidgets.QVBoxLayout()
    left_layt_wid = QtWidgets.QWidget()
    left_layt.setContentsMargins(0, 0, 0, 0)
    left_layt_wid.setLayout(left_layt)
    right_layt = QtWidgets.QVBoxLayout()
    right_layt_wid = QtWidgets.QWidget()
    right_layt.setContentsMargins(0, 0, 0, 0)
    right_layt_wid.setLayout(right_layt)
    self.main_splitter.addWidget(left_layt_wid)
    self.main_splitter.addWidget(right_layt_wid)
    self.layout.addWidget(self.main_splitter)

    layout_left_pane(self, left_layt)
    layout_right_pane(self, right_layt)


def layout_left_pane(self: QtWidgets.QWidget, layt: QtWidgets.QVBoxLayout):
    self.tabname_input = QtWidgets.QLineEdit()
    self.tabname_input.setPlaceholderText('Tab name')
    self.tabname_input.textChanged.connect(self.update_title)
    layt.addWidget(self.tabname_input)

    grp = QtWidgets.QGroupBox('Connection settings')
    grp_layt = QtWidgets.QVBoxLayout(grp)
    grp.setLayout(grp_layt)
    layt.addWidget(grp)

    self.url_input = QtWidgets.QLineEdit()
    self.url_input.setPlaceholderText('WebSocket URL')
    self.url_input.textChanged.connect(self.update_title)
    grp_layt.addWidget(self.url_input)

    self.headers_input = QtWidgets.QPlainTextEdit()
    self.headers_input.setPlaceholderText("Header-Name: Header Value")
    self.headers_input.setFont(get_font(MONOSPACE))
    grp_layt.addWidget(label('Headers'))
    grp_layt.addWidget(self.headers_input)

    self.proxy_input = QtWidgets.QLineEdit()
    self.proxy_enabled = QtWidgets.QCheckBox('Proxy (HTTP/S ONLY)')
    grp_layt.addWidget(self.proxy_enabled)
    self.proxy_input.setPlaceholderText('http[s]://[user[:password]@]domain.tld[:port]')
    self.proxy_input.setFont(get_font(MONOSPACE))
    grp_layt.addWidget(self.proxy_input)

    cb_row = QtWidgets.QHBoxLayout()
    grp_layt.addLayout(cb_row)

    self.conn_use_compression = QtWidgets.QCheckBox('Use compression')
    cb_row.addWidget(self.conn_use_compression)

    self.conn_persist = QtWidgets.QCheckBox('Auto-reconnect')
    cb_row.addWidget(self.conn_persist)

    cb_row1 = QtWidgets.QHBoxLayout()
    layt.addLayout(cb_row1)

    self.show_http = QtWidgets.QCheckBox('Show HTTP responses')
    self.show_http.setChecked(True)
    cb_row1.addWidget(self.show_http)

    self.show_alive_checks = QtWidgets.QCheckBox('Show Pings/Pongs/Polls')
    cb_row1.addWidget(self.show_alive_checks)

    tabs = QtWidgets.QTabWidget()

    hist_wid = QtWidgets.QWidget()
    hist_layt = QtWidgets.QVBoxLayout(hist_wid)
    hist_wid.setLayout(hist_layt)
    tabs.addTab(hist_wid, 'History')
    layout_history(self, hist_layt)

    favs_wid = QtWidgets.QWidget()
    favs_layt = QtWidgets.QVBoxLayout(favs_wid)
    favs_wid.setLayout(favs_layt)
    tabs.addTab(favs_wid, 'Favourites')
    layout_favs(self, favs_layt)

    layt.addWidget(tabs)

    bottom = QtWidgets.QHBoxLayout()
    for name, slug in (
            ('Clear history', 'clear_hist'),
            ('Save', 'save'),
            ('Save as', 'save_as'),
            ('Open', 'open')
    ):
        wid = button(name, getattr(self, slug))
        setattr(self, slug + '_btn', wid)
        bottom.addWidget(wid)
    layt.addLayout(bottom)


def layout_history(self: QtWidgets.QWidget, layt: QtWidgets.QVBoxLayout):
    self.history_list = QtWidgets.QListWidget()
    self.history_list.setFont(get_font(MONOSPACE))
    layt.addWidget(self.history_list)
    self.history_list.addItems(self.history)
    self.history_list.itemClicked.connect(lambda i: (
        self.set_input(i.text()),
        self.history_list.clearSelection()
    ))


def layout_favs(self: QtWidgets.QWidget, layt: QtWidgets.QVBoxLayout):
    btns = QtWidgets.QHBoxLayout()
    spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    btns.addItem(spacer)

    btns.addWidget(button('Add', self.add_fav))
    self.del_fav_btn = button('Remove', self.del_fav)
    self.del_fav_btn.setEnabled(False)
    btns.addWidget(self.del_fav_btn)
    self.set_fav_btn = button('To input', self.set_fav)
    self.set_fav_btn.setEnabled(False)
    btns.addWidget(self.set_fav_btn)

    btns.addItem(spacer)
    layt.addLayout(btns)

    self.favs_list = QtWidgets.QListWidget()
    self.favs_list.setFont(get_font(MONOSPACE))
    self.favs_list.itemClicked.connect(self.on_fav_item_click)
    layt.addWidget(self.favs_list)


def layout_right_pane(self: QtWidgets.QWidget, layt: QtWidgets.QVBoxLayout):
    self.right_splitter = QtWidgets.QSplitter()
    self.right_splitter.setOrientation(2)  # Vertical
    layt.addWidget(self.right_splitter)

    self.output = SocketOutput()
    self.right_splitter.addWidget(self.output)

    # btn = QtWidgets.QPushButton()
    # btn.setText('add')
    bottom = QtWidgets.QHBoxLayout()
    # bottom.setContentsMargins(0, 0, 0, 0)
    bottom_wid = QtWidgets.QWidget()
    bottom_wid.setLayout(bottom)
    self.right_splitter.addWidget(bottom_wid)

    bottom_left = QtWidgets.QVBoxLayout()
    bottom.addLayout(bottom_left)
    bottom_right = QtWidgets.QVBoxLayout()
    bottom.addLayout(bottom_right)

    btns = QtWidgets.QHBoxLayout()
    for name, slug in (
            ('Connect', 'toggle_connect'),
            ('Clear output', 'clear_output'),
    ):
        wid = button(name, getattr(self, slug))
        setattr(self, slug + '_btn', wid)
        btns.addWidget(wid)
    bottom_left.addLayout(btns)
    self.toggle_connect_btn.setEnabled(False)
    modes_scroll = QtWidgets.QScrollArea()
    modes_scroll.setStyleSheet('QScrollArea { background: transparent; }')
    modes_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
    modes_scroll_layt = QtWidgets.QVBoxLayout()
    modes_scroll_wid = QtWidgets.QFrame()
    modes_scroll_wid.setLayout(modes_scroll_layt)
    modes_scroll_layt.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
    modes_scroll.setWidget(modes_scroll_wid)
    modes_scroll.setSizeAdjustPolicy(QtWidgets.QScrollArea.AdjustToContents)
    modes_scroll_wid.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
    modes_scroll_wid.setStyleSheet('QFrame { background: transparent; }')

    modes_scroll.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred))
    bottom_right.addWidget(modes_scroll)

    for i, (name, slug) in enumerate((
            ('Plain text', 'plain_text'),
            ('Binary', 'binary'),
            ('Hex', 'hex'),
            ('Base64', 'base64'),
            ('JSON', 'json'),
            ('BSON', 'bson'),
    )):
        wid = QtWidgets.QRadioButton(name)
        if hasattr(self, 'on_' + slug):
            h = getattr(self, 'on_' + slug)
            wid.toggled.connect(h)
        setattr(self, 'send_{}_radio'.format(slug), wid)
        wid.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        modes_scroll_layt.addWidget(wid)
        if i == 0:
            wid.setChecked(True)

    self.use_compression = QtWidgets.QCheckBox('Use compression')

    bottom_right.addWidget(self.use_compression)

    self.send_button = button('Send', self.send)
    self.send_button.setEnabled(False)
    bottom_right.addWidget(self.send_button)

    self.input = BetterPlainTextEdit()
    self.input.setFont(get_font(MONOSPACE))

    self.input.jhl = JsonHighlighter()

    self.input.textEdited.connect(lambda:
                                  self.input.jhl.highlight(
                                      self.input.toPlainText(),
                                      self.input.document()
                                  ) if (self.send_json_radio.isChecked() or self.send_bson_radio.isChecked()) else 1)
    bottom_left.addWidget(self.input)
