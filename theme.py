"""
暗色主题 QSS 样式表
导出常量 DARK_STYLE 供应用全局使用。
"""

DARK_STYLE = """
/* ============ QMainWindow ============ */
QMainWindow {
    background-color: #1A1A2E;
    color: #FFFFFF;
}

/* ============ QMainWindow::separator ============ */
QMainWindow::separator {
    background-color: #2A2A4E;
    width: 1px;
    height: 1px;
}

/* ============ QWidget ============ */
QWidget {
    background-color: #1A1A2E;
    color: #FFFFFF;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ============ QLabel ============ */
QLabel {
    background-color: transparent;
    color: #FFFFFF;
    border: none;
}

/* ============ QPushButton ============ */
QPushButton {
    background-color: #4A9ED9;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: bold;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #5DB3E8;
}

QPushButton:pressed {
    background-color: #3A8EC9;
}

QPushButton:disabled {
    background-color: #2A2A4E;
    color: #8E8E9E;
}

/* ============ QLineEdit ============ */
QLineEdit {
    background-color: #16213E;
    color: #FFFFFF;
    border: 1px solid #2A2A4E;
    border-radius: 6px;
    padding: 6px 12px;
    selection-background-color: #4A9ED9;
    selection-color: #FFFFFF;
}

QLineEdit:focus {
    border-color: #4A9ED9;
}

QLineEdit:disabled {
    background-color: #1A1A2E;
    color: #8E8E9E;
}

QLineEdit::placeholder {
    color: #8E8E9E;
}

/* ============ QTextEdit / QPlainTextEdit ============ */
QTextEdit, QPlainTextEdit {
    background-color: #16213E;
    color: #FFFFFF;
    border: 1px solid #2A2A4E;
    border-radius: 6px;
    padding: 8px;
    selection-background-color: #4A9ED9;
    selection-color: #FFFFFF;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #4A9ED9;
}

/* ============ QTableView ============ */
QTableView {
    background-color: #16213E;
    color: #FFFFFF;
    border: 1px solid #2A2A4E;
    border-radius: 6px;
    gridline-color: #2A2A4E;
    selection-background-color: #0F3460;
    selection-color: #FFFFFF;
    alternate-background-color: #1A1A2E;
}

QTableView::item {
    padding: 8px 12px;
}

QTableView::item:hover {
    background-color: #0F3460;
}

/* ============ QHeaderView ============ */
QHeaderView {
    background-color: #16213E;
    border: none;
}

QHeaderView::section {
    background-color: #16213E;
    color: #8E8E9E;
    padding: 8px 12px;
    border: none;
    border-bottom: 2px solid #2A2A4E;
    font-weight: bold;
    text-transform: uppercase;
}

QHeaderView::section:hover {
    background-color: #1E2D50;
    color: #FFFFFF;
}

QHeaderView::down-arrow {
    image: none;
    width: 0;
}

QHeaderView::up-arrow {
    image: none;
    width: 0;
}

/* ============ QTabWidget ============ */
QTabWidget::pane {
    background-color: #16213E;
    border: 1px solid #2A2A4E;
    border-radius: 6px;
    top: -1px;
}

QTabBar::tab {
    background-color: #1A1A2E;
    color: #8E8E9E;
    padding: 8px 16px;
    border: 1px solid #2A2A4E;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}

QTabBar::tab:hover {
    background-color: #1E2D50;
    color: #FFFFFF;
}

QTabBar::tab:selected {
    background-color: #16213E;
    color: #4A9ED9;
    font-weight: bold;
}

/* ============ QComboBox ============ */
QComboBox {
    background-color: #16213E;
    color: #FFFFFF;
    border: 1px solid #2A2A4E;
    border-radius: 6px;
    padding: 6px 12px;
    min-width: 80px;
}

QComboBox:hover {
    border-color: #4A9ED9;
}

QComboBox:focus {
    border-color: #4A9ED9;
}

QComboBox::drop-down {
    background-color: transparent;
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #8E8E9E;
    margin-right: 4px;
}

QComboBox QAbstractItemView {
    background-color: #16213E;
    color: #FFFFFF;
    border: 1px solid #2A2A4E;
    border-radius: 4px;
    selection-background-color: #0F3460;
    selection-color: #FFFFFF;
    outline: none;
}

/* ============ QScrollBar: Vertical ============ */
QScrollBar:vertical {
    background-color: #1A1A2E;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #2A2A4E;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4A9ED9;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
    border: none;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}

/* ============ QScrollBar: Horizontal ============ */
QScrollBar:horizontal {
    background-color: #1A1A2E;
    height: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background-color: #2A2A4E;
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #4A9ED9;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
    border: none;
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: none;
}

/* ============ QFrame ============ */
QFrame[frameShape="4"] {  /* HLine */
    background-color: #2A2A4E;
    max-height: 1px;
}

QFrame[frameShape="5"] {  /* VLine */
    background-color: #2A2A4E;
    max-width: 1px;
}

/* ============ QDialog ============ */
QDialog {
    background-color: #1A1A2E;
    color: #FFFFFF;
}

/* ============ QMenu ============ */
QMenu {
    background-color: #16213E;
    color: #FFFFFF;
    border: 1px solid #2A2A4E;
    border-radius: 6px;
    padding: 4px 0;
}

QMenu::item {
    padding: 8px 32px 8px 16px;
    background-color: transparent;
}

QMenu::item:selected {
    background-color: #0F3460;
    color: #4A9ED9;
}

QMenu::item:disabled {
    color: #8E8E9E;
}

QMenu::separator {
    height: 1px;
    background-color: #2A2A4E;
    margin: 4px 8px;
}

/* ============ QToolTip ============ */
QToolTip {
    background-color: #16213E;
    color: #FFFFFF;
    border: 1px solid #4A9ED9;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ============ QToolBar ============ */
QToolBar {
    background-color: #1A1A2E;
    border-bottom: 1px solid #2A2A4E;
    padding: 4px;
    spacing: 4px;
}

/* ============ QStatusBar ============ */
QStatusBar {
    background-color: #16213E;
    color: #8E8E9E;
    border-top: 1px solid #2A2A4E;
}

/* ============ QProgressBar ============ */
QProgressBar {
    background-color: #16213E;
    border: 1px solid #2A2A4E;
    border-radius: 4px;
    text-align: center;
    color: #FFFFFF;
    height: 12px;
}

QProgressBar::chunk {
    background-color: #4A9ED9;
    border-radius: 3px;
}

/* ============ QCheckBox ============ */
QCheckBox {
    background-color: transparent;
    color: #FFFFFF;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #2A2A4E;
    border-radius: 4px;
    background-color: #16213E;
}

QCheckBox::indicator:checked {
    background-color: #4A9ED9;
    border-color: #4A9ED9;
}

QCheckBox::indicator:hover {
    border-color: #4A9ED9;
}

/* ============ QRadioButton ============ */
QRadioButton {
    background-color: transparent;
    color: #FFFFFF;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #2A2A4E;
    border-radius: 9px;
    background-color: #16213E;
}

QRadioButton::indicator:checked {
    background-color: #4A9ED9;
    border-color: #4A9ED9;
}

/* ============ QGroupBox ============ */
QGroupBox {
    background-color: #16213E;
    border: 1px solid #2A2A4E;
    border-radius: 8px;
    margin-top: 12px;
    padding: 16px 12px 12px 12px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 6px;
    color: #8E8E9E;
}

/* ============ QSplitter ============ */
QSplitter::handle {
    background-color: #2A2A4E;
}

QSplitter::handle:horizontal {
    width: 1px;
}

QSplitter::handle:vertical {
    height: 1px;
}

/* ============ QSpinBox / QDoubleSpinBox ============ */
QSpinBox, QDoubleSpinBox {
    background-color: #16213E;
    color: #FFFFFF;
    border: 1px solid #2A2A4E;
    border-radius: 6px;
    padding: 4px 8px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #4A9ED9;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #1A1A2E;
    border-radius: 3px;
    width: 18px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #0F3460;
}

/* ============ QListWidget / QTreeWidget ============ */
QListWidget, QTreeWidget {
    background-color: #16213E;
    color: #FFFFFF;
    border: 1px solid #2A2A4E;
    border-radius: 6px;
    outline: none;
}

QListWidget::item, QTreeWidget::item {
    padding: 6px 12px;
}

QListWidget::item:selected, QTreeWidget::item:selected {
    background-color: #0F3460;
    color: #4A9ED9;
}

QListWidget::item:hover, QTreeWidget::item:hover {
    background-color: #1E2D50;
}
"""
