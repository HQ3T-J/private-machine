"""
StandupSync 主题样式表
导出 DARK_STYLE / LIGHT_STYLE 供全局切换。
"""

DARK_STYLE = """
QMainWindow { background-color: #1A1A2E; color: #FFFFFF; }
QMainWindow::separator { background-color: #2A2A4E; width: 1px; height: 1px; }
QWidget { background-color: #1A1A2E; color: #FFFFFF; font-family: "Microsoft YaHei","Segoe UI",sans-serif; font-size: 13px; }
QLabel { background-color: transparent; color: #FFFFFF; border: none; }
QPushButton { background-color: #4A9ED9; color: #FFFFFF; border: none; border-radius: 6px; padding: 8px 20px; font-weight: bold; min-height: 20px; }
QPushButton:hover { background-color: #5DB3E8; }
QPushButton:pressed { background-color: #3A8EC9; }
QPushButton:disabled { background-color: #2A2A4E; color: #8E8E9E; }
QLineEdit { background-color: #16213E; color: #FFFFFF; border: 1px solid #2A2A4E; border-radius: 6px; padding: 6px 12px; selection-background-color: #4A9ED9; selection-color: #FFFFFF; }
QLineEdit:focus { border-color: #4A9ED9; }
QLineEdit:disabled { background-color: #1A1A2E; color: #8E8E9E; }
QLineEdit::placeholder { color: #8E8E9E; }
QTextEdit, QPlainTextEdit { background-color: #16213E; color: #FFFFFF; border: 1px solid #2A2A4E; border-radius: 6px; padding: 8px; selection-background-color: #4A9ED9; }
QTextEdit:focus, QPlainTextEdit:focus { border-color: #4A9ED9; }
QTableView { background-color: #16213E; color: #FFFFFF; border: 1px solid #2A2A4E; border-radius: 6px; gridline-color: #2A2A4E; selection-background-color: #0F3460; alternate-background-color: #1A1A2E; }
QTableView::item { padding: 8px 12px; }
QTableView::item:hover { background-color: #0F3460; }
QHeaderView { background-color: #16213E; border: none; }
QHeaderView::section { background-color: #16213E; color: #8E8E9E; padding: 8px 12px; border: none; border-bottom: 2px solid #2A2A4E; font-weight: bold; }
QHeaderView::section:hover { background-color: #1E2D50; color: #FFFFFF; }
QTabWidget::pane { background-color: #16213E; border: 1px solid #2A2A4E; border-radius: 6px; top: -1px; }
QTabBar::tab { background-color: #1A1A2E; color: #8E8E9E; padding: 8px 16px; border: 1px solid #2A2A4E; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
QTabBar::tab:hover { background-color: #1E2D50; color: #FFFFFF; }
QTabBar::tab:selected { background-color: #16213E; color: #4A9ED9; font-weight: bold; }
QComboBox { background-color: #16213E; color: #FFFFFF; border: 1px solid #2A2A4E; border-radius: 6px; padding: 6px 12px; min-width: 80px; }
QComboBox:hover, QComboBox:focus { border-color: #4A9ED9; }
QComboBox::drop-down { background-color: transparent; border: none; width: 24px; }
QComboBox QAbstractItemView { background-color: #16213E; color: #FFFFFF; border: 1px solid #2A2A4E; border-radius: 4px; selection-background-color: #0F3460; outline: none; }
QScrollBar:vertical { background-color: #1A1A2E; width: 8px; margin: 0; border-radius: 4px; }
QScrollBar::handle:vertical { background-color: #2A2A4E; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background-color: #4A9ED9; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; border: none; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
QScrollBar:horizontal { background-color: #1A1A2E; height: 8px; margin: 0; border-radius: 4px; }
QScrollBar::handle:horizontal { background-color: #2A2A4E; border-radius: 4px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background-color: #4A9ED9; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; border: none; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }
QDialog { background-color: #1A1A2E; color: #FFFFFF; }
QMenu { background-color: #16213E; color: #FFFFFF; border: 1px solid #2A2A4E; border-radius: 6px; padding: 4px 0; }
QMenu::item { padding: 8px 32px 8px 16px; background-color: transparent; }
QMenu::item:selected { background-color: #0F3460; color: #4A9ED9; }
QMenu::item:disabled { color: #8E8E9E; }
QMenu::separator { height: 1px; background-color: #2A2A4E; margin: 4px 8px; }
QToolTip { background-color: #16213E; color: #FFFFFF; border: 1px solid #4A9ED9; border-radius: 4px; padding: 6px 10px; font-size: 12px; }
QToolBar { background-color: #1A1A2E; border-bottom: 1px solid #2A2A4E; padding: 4px; spacing: 4px; }
QStatusBar { background-color: #16213E; color: #8E8E9E; border-top: 1px solid #2A2A4E; }
QProgressBar { background-color: #16213E; border: 1px solid #2A2A4E; border-radius: 4px; text-align: center; color: #FFFFFF; height: 12px; }
QProgressBar::chunk { background-color: #4A9ED9; border-radius: 3px; }
QCheckBox { background-color: transparent; color: #FFFFFF; spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #2A2A4E; border-radius: 4px; background-color: #16213E; }
QCheckBox::indicator:checked { background-color: #4A9ED9; border-color: #4A9ED9; }
QCheckBox::indicator:hover { border-color: #4A9ED9; }
QRadioButton { background-color: transparent; color: #FFFFFF; spacing: 8px; }
QRadioButton::indicator { width: 18px; height: 18px; border: 2px solid #2A2A4E; border-radius: 9px; background-color: #16213E; }
QRadioButton::indicator:checked { background-color: #4A9ED9; border-color: #4A9ED9; }
QGroupBox { background-color: #16213E; border: 1px solid #2A2A4E; border-radius: 8px; margin-top: 12px; padding: 16px 12px 12px 12px; font-weight: bold; color: #FFFFFF; }
QGroupBox::title { subcontrol-origin: margin; left: 16px; padding: 0 6px; color: #8E8E9E; }
QSplitter::handle { background-color: #2A2A4E; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }
QSpinBox, QDoubleSpinBox { background-color: #16213E; color: #FFFFFF; border: 1px solid #2A2A4E; border-radius: 6px; padding: 4px 8px; }
QSpinBox:focus, QDoubleSpinBox:focus { border-color: #4A9ED9; }
QSpinBox::up-button, QDoubleSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::down-button { background-color: #1A1A2E; border-radius: 3px; width: 18px; }
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover, QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { background-color: #0F3460; }
QListWidget, QTreeWidget { background-color: #16213E; color: #FFFFFF; border: 1px solid #2A2A4E; border-radius: 6px; outline: none; }
QListWidget::item, QTreeWidget::item { padding: 6px 12px; }
QListWidget::item:selected, QTreeWidget::item:selected { background-color: #0F3460; color: #4A9ED9; }
QListWidget::item:hover, QTreeWidget::item:hover { background-color: #1E2D50; }
"""

LIGHT_STYLE = """
/* ═══════════════════════════════════════════
   StandupSync 浅色主题
   主背景: #F4F6F8  主文本: #262626
   辅助文本: #8C8C8C  品牌色: #1890FF
   边框: #E5E5E5  悬停: #E6F7FF
   ═══════════════════════════════════════════ */

/* ── 全局基础 ── */
QMainWindow { background-color: #F4F6F8; color: #262626; }
QMainWindow::separator { background-color: #E5E5E5; width: 1px; height: 1px; }
QWidget { background-color: #F4F6F8; color: #262626; font-family: "Microsoft YaHei","Segoe UI",sans-serif; font-size: 13px; }
QLabel { background-color: transparent; color: #262626; border: none; }

/* ── 按钮 ── */
QPushButton { background-color: #1890FF; color: #FFFFFF; border: none; border-radius: 6px; padding: 8px 20px; font-weight: bold; min-height: 20px; }
QPushButton:hover { background-color: #40A9FF; }
QPushButton:pressed { background-color: #096DD9; }
QPushButton:disabled { background-color: #D9D9D9; color: #8C8C8C; }

/* ── 输入框 ── */
QLineEdit { background-color: #FFFFFF; color: #262626; border: 1px solid #E5E5E5; border-radius: 6px; padding: 6px 12px; selection-background-color: #1890FF; selection-color: #FFFFFF; }
QLineEdit:focus { border-color: #1890FF; }
QLineEdit:disabled { background-color: #F4F6F8; color: #8C8C8C; }
QLineEdit::placeholder { color: #8C8C8C; }

/* ── 多行文本 ── */
QTextEdit, QPlainTextEdit { background-color: #FFFFFF; color: #262626; border: 1px solid #E5E5E5; border-radius: 6px; padding: 8px; selection-background-color: #1890FF; }
QTextEdit:focus, QPlainTextEdit:focus { border-color: #1890FF; }

/* ── 表格 ── */
QTableView { background-color: #FFFFFF; color: #262626; border: 1px solid #E5E5E5; border-radius: 6px; gridline-color: #F0F0F0; selection-background-color: #E6F7FF; selection-color: #262626; alternate-background-color: #FAFBFC; }
QTableView::item { padding: 8px 12px; }
QTableView::item:hover { background-color: #E6F7FF; }
QHeaderView { background-color: #FAFBFC; border: none; }
QHeaderView::section { background-color: #FAFBFC; color: #8C8C8C; padding: 8px 12px; border: none; border-bottom: 1px solid #E5E5E5; font-weight: bold; }
QHeaderView::section:hover { background-color: #E6F7FF; color: #262626; }

/* ── Tab 页签 ── */
QTabWidget::pane { background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 6px; top: -1px; }
QTabBar::tab { background: #F4F6F8; color: #8C8C8C; padding: 8px 16px; border: 1px solid #E5E5E5; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
QTabBar::tab:hover { background: #E6F7FF; color: #262626; }
QTabBar::tab:selected { background: #FFFFFF; color: #1890FF; font-weight: bold; }

/* ── 下拉框 ── */
QComboBox { background-color: #FFFFFF; color: #262626; border: 1px solid #E5E5E5; border-radius: 6px; padding: 6px 12px; min-width: 80px; }
QComboBox:hover, QComboBox:focus { border-color: #1890FF; }
QComboBox::drop-down { background: transparent; border: none; width: 24px; }
QComboBox QAbstractItemView { background-color: #FFFFFF; color: #262626; border: 1px solid #E5E5E5; border-radius: 4px; selection-background-color: #E6F7FF; outline: none; }

/* ── 滚动条 ── */
QScrollBar:vertical { background: #F4F6F8; width: 8px; margin: 0; border-radius: 4px; }
QScrollBar::handle:vertical { background: #D9D9D9; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #1890FF; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; border: none; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
QScrollBar:horizontal { background: #F4F6F8; height: 8px; margin: 0; border-radius: 4px; }
QScrollBar::handle:horizontal { background: #D9D9D9; border-radius: 4px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: #1890FF; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; border: none; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }

/* ── 对话框 ── */
QDialog { background-color: #F4F6F8; color: #262626; }

/* ── 菜单 ── */
QMenu { background-color: #FFFFFF; color: #262626; border: 1px solid #E5E5E5; border-radius: 6px; padding: 4px 0; }
QMenu::item { padding: 8px 32px 8px 16px; background-color: transparent; }
QMenu::item:selected { background-color: #E6F7FF; color: #1890FF; }
QMenu::item:disabled { color: #D9D9D9; }
QMenu::separator { height: 1px; background-color: #E5E5E5; margin: 4px 8px; }

/* ── 提示 ── */
QToolTip { background-color: #FFFFFF; color: #262626; border: 1px solid #1890FF; border-radius: 4px; padding: 6px 10px; font-size: 12px; }

/* ── 工具栏 ── */
QToolBar { background-color: #FFFFFF; border-bottom: 1px solid #E5E5E5; padding: 4px; spacing: 4px; }

/* ── 状态栏 ── */
QStatusBar { background-color: #FAFBFC; color: #8C8C8C; border-top: 1px solid #E5E5E5; }

/* ── 进度条 ── */
QProgressBar { background-color: #F4F6F8; border: 1px solid #E5E5E5; border-radius: 4px; text-align: center; color: #262626; height: 12px; }
QProgressBar::chunk { background-color: #1890FF; border-radius: 3px; }

/* ── 复选框 / 单选框 ── */
QCheckBox { background-color: transparent; color: #262626; spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #D9D9D9; border-radius: 4px; background-color: #FFFFFF; }
QCheckBox::indicator:checked { background-color: #1890FF; border-color: #1890FF; }
QCheckBox::indicator:hover { border-color: #1890FF; }
QRadioButton { background-color: transparent; color: #262626; spacing: 8px; }
QRadioButton::indicator { width: 18px; height: 18px; border: 2px solid #D9D9D9; border-radius: 9px; background-color: #FFFFFF; }
QRadioButton::indicator:checked { background-color: #1890FF; border-color: #1890FF; }

/* ── 分组框 ── */
QGroupBox { background-color: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 8px; margin-top: 12px; padding: 16px 12px 12px 12px; font-weight: bold; color: #262626; }
QGroupBox::title { subcontrol-origin: margin; left: 16px; padding: 0 6px; color: #8C8C8C; }

/* ── 分割条 ── */
QSplitter::handle { background-color: #E5E5E5; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }

/* ── 数字输入框 ── */
QSpinBox, QDoubleSpinBox { background-color: #FFFFFF; color: #262626; border: 1px solid #E5E5E5; border-radius: 6px; padding: 4px 8px; }
QSpinBox:focus, QDoubleSpinBox:focus { border-color: #1890FF; }
QSpinBox::up-button, QDoubleSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::down-button { background-color: #F4F6F8; border-radius: 3px; width: 18px; }
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover, QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { background-color: #E6F7FF; }

/* ── 列表 / 树 ── */
QListWidget, QTreeWidget { background-color: #FFFFFF; color: #262626; border: 1px solid #E5E5E5; border-radius: 6px; outline: none; }
QListWidget::item, QTreeWidget::item { padding: 6px 12px; }
QListWidget::item:selected, QTreeWidget::item:selected { background-color: #E6F7FF; color: #1890FF; }
QListWidget::item:hover, QTreeWidget::item:hover { background-color: #E6F7FF; }
"""
