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

    left_layout = QtWidgets.QVBoxLayout()
    left_layout_widget = QtWidgets.QWidget()
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_layout_widget.setLayout(left_layout)
    right_layout = QtWidgets.QVBoxLayout()
    right_layout_widget = QtWidgets.QWidget()
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout_widget.setLayout(right_layout)
    self.main_splitter.addWidget(left_layout_widget)
    self.main_splitter.addWidget(right_layout_widget)
    self.layout.addWidget(self.main_splitter)

    layout_left_pane(self, left_layout)
    layout_right_pane(self, right_layout)


def layout_left_pane(self: QtWidgets.QWidget, layout: QtWidgets.QVBoxLayout):
    self.tabname_input = QtWidgets.QLineEdit()
    self.tabname_input.setPlaceholderText('Tab name')
    self.tabname_input.textChanged.connect(self.update_title)
    layout.addWidget(self.tabname_input)

    group = QtWidgets.QGroupBox('Connection settings')
    group_layout = QtWidgets.QVBoxLayout(group)
    group.setLayout(group_layout)
    layout.addWidget(group)

    self.url_input = QtWidgets.QLineEdit()
    self.url_input.setPlaceholderText('WebSocket URL')
    self.url_input.textChanged.connect(self.update_title)
    group_layout.addWidget(self.url_input)

    self.headers_input = QtWidgets.QPlainTextEdit()
    self.headers_input.setPlaceholderText("Header-Name: Header Value")
    self.headers_input.setFont(get_font(MONOSPACE))
    group_layout.addWidget(label('Headers'))
    group_layout.addWidget(self.headers_input)

    self.proxy_input = QtWidgets.QLineEdit()
    self.proxy_enabled = QtWidgets.QCheckBox('Proxy (HTTP/S ONLY)')
    group_layout.addWidget(self.proxy_enabled)
    self.proxy_input.setPlaceholderText('http[s]://[user[:password]@]domain.tld[:port]')
    self.proxy_input.setFont(get_font(MONOSPACE))
    group_layout.addWidget(self.proxy_input)

    checkboxes_row = QtWidgets.QHBoxLayout()
    group_layout.addLayout(checkboxes_row)

    self.conn_use_compression = QtWidgets.QCheckBox('Use compression')
    checkboxes_row.addWidget(self.conn_use_compression)

    self.conn_persist = QtWidgets.QCheckBox('Auto-reconnect')
    checkboxes_row.addWidget(self.conn_persist)

    checkboxes_row1 = QtWidgets.QHBoxLayout()
    layout.addLayout(checkboxes_row1)

    self.show_http = QtWidgets.QCheckBox('Show HTTP responses')
    self.show_http.setChecked(True)
    checkboxes_row1.addWidget(self.show_http)

    self.show_alive_checks = QtWidgets.QCheckBox('Show Pings/Pongs/Polls')
    checkboxes_row1.addWidget(self.show_alive_checks)

    checkboxes_row2 = QtWidgets.QHBoxLayout()
    layout.addLayout(checkboxes_row2)
    self.decode_bson = QtWidgets.QCheckBox('Decode BSON')
    self.decode_bson.setChecked(True)
    checkboxes_row2.addWidget(self.decode_bson)

    tabs = QtWidgets.QTabWidget()

    history_widget = QtWidgets.QWidget()
    history_layout = QtWidgets.QVBoxLayout(history_widget)
    history_widget.setLayout(history_layout)
    tabs.addTab(history_widget, 'History')
    layout_history(self, history_layout)

    favourites_widget = QtWidgets.QWidget()
    favourites_layout = QtWidgets.QVBoxLayout(favourites_widget)
    favourites_widget.setLayout(favourites_layout)
    tabs.addTab(favourites_widget, 'Favourites')
    layout_favs(self, favourites_layout)

    layout.addWidget(tabs)

    bottom = QtWidgets.QHBoxLayout()
    for name, slug in (
            ('Clear history', 'clear_hist'),
            ('Save', 'save'),
            ('Save as', 'save_as'),
            ('Open', 'open')
    ):
        widget = button(name, getattr(self, slug))
        setattr(self, slug + '_btn', widget)
        bottom.addWidget(widget)
    layout.addLayout(bottom)


def layout_history(self: QtWidgets.QWidget, layout: QtWidgets.QVBoxLayout):
    self.history_list = QtWidgets.QListWidget()
    self.history_list.setFont(get_font(MONOSPACE))
    layout.addWidget(self.history_list)
    self.history_list.addItems(self.history)
    self.history_list.itemClicked.connect(lambda i: (
        self.set_input(i.text()),
        self.history_list.clearSelection()
    ))


def layout_favs(self: QtWidgets.QWidget, layout: QtWidgets.QVBoxLayout):
    buttons = QtWidgets.QHBoxLayout()
    spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    buttons.addItem(spacer)

    buttons.addWidget(button('Add', self.add_fav))
    self.del_fav_btn = button('Remove', self.del_fav)
    self.del_fav_btn.setEnabled(False)
    buttons.addWidget(self.del_fav_btn)
    self.set_fav_btn = button('To input', self.set_fav)
    self.set_fav_btn.setEnabled(False)
    buttons.addWidget(self.set_fav_btn)

    buttons.addItem(spacer)
    layout.addLayout(buttons)

    self.favourites_list = QtWidgets.QListWidget()
    self.favourites_list.setFont(get_font(MONOSPACE))
    self.favourites_list.itemClicked.connect(self.on_fav_item_click)
    layout.addWidget(self.favourites_list)


def layout_right_pane(self: QtWidgets.QWidget, layout: QtWidgets.QVBoxLayout):
    self.right_splitter = QtWidgets.QSplitter()
    self.right_splitter.setOrientation(2)  # Vertical
    layout.addWidget(self.right_splitter)

    self.output = SocketOutput()
    self.right_splitter.addWidget(self.output)

    bottom = QtWidgets.QHBoxLayout()
    bottom_widget = QtWidgets.QWidget()
    bottom_widget.setLayout(bottom)
    self.right_splitter.addWidget(bottom_widget)

    bottom_left = QtWidgets.QVBoxLayout()
    bottom.addLayout(bottom_left)
    bottom_right = QtWidgets.QVBoxLayout()
    bottom.addLayout(bottom_right)

    buttons = QtWidgets.QHBoxLayout()
    for name, slug in (
            ('Connect', 'toggle_connect'),
            ('Clear output', 'clear_output'),
    ):
        wid = button(name, getattr(self, slug))
        setattr(self, slug + '_btn', wid)
        buttons.addWidget(wid)
    bottom_left.addLayout(buttons)
    self.toggle_connect_btn.setEnabled(False)

    self.send_button = button('Send', self.send)
    self.send_button.setEnabled(False)
    bottom_right.addWidget(self.send_button)

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

    self.input = BetterPlainTextEdit()
    self.input.setFont(get_font(MONOSPACE))

    self.input.jhl = JsonHighlighter()

    self.input.textEdited.connect(lambda:
                                  self.input.jhl.highlight(
                                      self.input.toPlainText(),
                                      self.input.document()
                                  ) if (self.send_json_radio.isChecked() or self.send_bson_radio.isChecked()) else 1)
    bottom_left.addWidget(self.input)
