STYLE = """
QWidget { background: #101927; color: #e6ebf3; font-family: 'Segoe UI', 'DejaVu Sans'; font-size: 13px; }
QMainWindow { background: #101927; }
QLabel { background: transparent; }
QLabel#Title { font-size: 29px; font-weight: 700; }
QLabel#Heading { font-size: 21px; font-weight: 600; }
QLabel#Muted { color: #9cabc0; }
QLabel#Eyebrow { color: #ffb65d; font-size: 11px; font-weight: 600; letter-spacing: 2px; }
QFrame#Card { background: #162335; border: 1px solid #263950; border-radius: 10px; }
QListWidget#Navigation { background: #0c1421; border: none; outline: none; padding: 10px; }
QListWidget#Navigation::item { padding: 14px 12px; margin: 3px 0; border-radius: 7px; color: #a8b8ca; }
QListWidget#Navigation::item:selected { background: #29303a; color: #ffb967; border-left: 3px solid #ff8b45; }
QListWidget#Navigation::item:hover { background: #1a293d; }
QPushButton { background: #223349; border: 1px solid #344962; padding: 8px 14px; border-radius: 6px; }
QPushButton:hover { border-color: #ffae61; background: #2b3c51; }
QPushButton:pressed { background: #36475c; }
QPushButton:disabled { color: #66768a; background: #1a2433; border-color: #253247; }
QPushButton#Primary { background: #ed8641; color: #151b25; border: none; font-weight: 700; }
QPushButton#Primary:hover { background: #ffab60; }
QPushButton:checked { background: #e99449; color: #151b25; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background: #0e1725; border: 1px solid #32435a; border-radius: 5px; padding: 6px; selection-background-color: #5a432b; }
QLineEdit:focus, QSpinBox:focus { border-color: #e99449; }
QComboBox::drop-down { width: 24px; border: none; }
QComboBox QAbstractItemView { background: #172538; selection-background-color: #39465b; }
QPlainTextEdit, QTextEdit, QTextBrowser { background: #0c1421; border: 1px solid #26364d; border-radius: 5px; selection-background-color: #57452f; }
QTabWidget::pane { border: 1px solid #2b3a50; }
QTabBar::tab { background: #142031; color: #9cabc0; padding: 9px 15px; border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: #f8d4a3; border-bottom: 2px solid #f9a052; background: #1b293c; }
QTreeWidget, QTableWidget, QListWidget { background: #111d2c; alternate-background-color: #172538; border: 1px solid #293a51; selection-background-color: #35475f; }
QHeaderView::section { background: #1d2d41; color: #bfcadb; padding: 7px; border: none; border-bottom: 1px solid #324258; }
QTableWidget::item { padding: 4px; }
QScrollBar:vertical { background: #101a29; width: 10px; }
QScrollBar::handle:vertical { background: #35465e; min-height: 28px; border-radius: 5px; }
QScrollBar:horizontal { background: #101a29; height: 10px; }
QScrollBar::handle:horizontal { background: #35465e; min-width: 28px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QSplitter::handle { background: #26374c; }
QMenuBar { background: #0c1421; color: #b8c8dc; }
QMenuBar::item:selected, QMenu::item:selected { background: #34475f; }
QMenu { border: 1px solid #34465e; }
QStatusBar { background: #0c1421; color: #9cabc0; }
QToolTip { background: #25354b; color: #ffffff; border: 1px solid #697b92; }
"""
