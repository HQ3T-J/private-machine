# views/settings_view.py — 设置页面 V3
"""设置视图：个人 / AI / 通知(可交互) / 外观(真实主题切换)"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QGroupBox, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal


class ToggleSwitch(QPushButton):
    """可交互的开关按钮：显示 ✓ 或 ✗"""

    toggled = Signal(bool)

    def __init__(self, label: str, checked: bool = True, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._label = label
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(36)
        self.clicked.connect(self._on_click)
        self._render()

    def _on_click(self):
        self._checked = self.isChecked()
        self._render()
        self.toggled.emit(self._checked)

    def _render(self):
        mark = "\u2713" if self._checked else "\u2717"
        color = "#52C41A" if self._checked else "#E74C3C"
        self.setText(f"  {mark}  {self._label}")
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {color};
                border: none; text-align: left; font-size: 13px;
                padding: 6px 4px;
            }}
        """)

    def is_on(self) -> bool:
        return self._checked


class SettingsView(QWidget):
    """设置页面"""

    theme_changed = Signal(str)

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.title = "设置"
        self._current_theme = "dark"
        self._setup_ui()

    def activate(self):
        """页面激活时刷新用户信息"""
        if self.api_client:
            self.nickname_input.setText(self.api_client.username or "")
            self.role_label.setText(self.api_client.role or "—")

    def _on_logout(self):
        from PySide6.QtWidgets import QApplication, QMessageBox
        reply = QMessageBox.question(self, "确认", "确定要退出登录吗？",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            QApplication.instance().quit()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(12)

        # 标题
        title = QLabel("设置")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(self._create_profile_section())
        layout.addWidget(self._create_ai_section())
        layout.addWidget(self._create_notification_section())
        layout.addWidget(self._create_appearance_section())
        layout.addStretch(1)

        logout = QPushButton("退出登录")
        logout.setStyleSheet("""
            QPushButton { background: transparent; color: #FF4D4D;
                border: 1px solid #FF4D4D; border-radius: 8px;
                padding: 10px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background: rgba(255,77,77,0.15); }
        """)
        logout.setCursor(Qt.PointingHandCursor)
        logout.clicked.connect(self._on_logout)
        layout.addWidget(logout)

    # ── 个人信息 ──
    def _create_profile_section(self) -> QGroupBox:
        g = QGroupBox("个人信息")
        gl = QVBoxLayout(g)
        gl.setSpacing(8)

        row = QHBoxLayout()
        avatar = QLabel("\U0001F464")
        avatar.setFixedSize(48, 48)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("font-size: 28px; border-radius: 24px;")
        row.addWidget(avatar)

        self.nickname_input = QLineEdit()
        self.nickname_input.setPlaceholderText("输入昵称")
        self.nickname_input.setFixedWidth(180)
        self.nickname_input.setMinimumHeight(32)
        row.addWidget(self.nickname_input)

        self.role_label = QLabel("Tech Lead")
        self.role_label.setStyleSheet("color: #4A90D9; font-size: 12px;")
        row.addWidget(self.role_label)
        row.addStretch()

        save = QPushButton("保存修改")
        save.setFixedHeight(32)
        save.setCursor(Qt.PointingHandCursor)
        row.addWidget(save)
        gl.addLayout(row)
        return g

    # ── AI 设置 ──
    def _create_ai_section(self) -> QGroupBox:
        g = QGroupBox("AI 设置")
        gl = QVBoxLayout(g)
        gl.setSpacing(8)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["豆包", "通义千问", "OpenAI", "自定义"])
        self.provider_combo.setMinimumHeight(32)
        gl.addWidget(self._labeled_row("服务商", self.provider_combo))

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("例如: doubao-pro-32k")
        self.model_input.setMinimumHeight(32)
        gl.addWidget(self._labeled_row("模型", self.model_input))

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("输入 API Key")
        self.api_key_input.setMinimumHeight(32)
        gl.addWidget(self._labeled_row("API Key", self.api_key_input))

        test_btn = QPushButton("测试连接")
        test_btn.setFixedHeight(32)
        test_btn.setCursor(Qt.PointingHandCursor)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(test_btn)
        gl.addLayout(btn_row)
        return g

    # ── 通知设置（可交互开关） ──
    def _create_notification_section(self) -> QGroupBox:
        g = QGroupBox("通知设置")
        gl = QVBoxLayout(g)
        gl.setSpacing(6)

        self.standup_reminder = ToggleSwitch("站会开始前提醒", True)
        gl.addWidget(self.standup_reminder)

        self.todo_reminder = ToggleSwitch("待办到期前提醒", True)
        gl.addWidget(self.todo_reminder)

        self.assign_notify = ToggleSwitch("被分配新待办时通知", True)
        gl.addWidget(self.assign_notify)
        return g

    # ── 外观 ──
    def _create_appearance_section(self) -> QGroupBox:
        g = QGroupBox("外观")
        gl = QVBoxLayout(g)
        gl.setSpacing(8)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["深色", "浅色"])
        self.theme_combo.setCurrentIndex(0)
        self.theme_combo.setMinimumHeight(32)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_change)
        gl.addWidget(self._labeled_row("主题", self.theme_combo))
        return g

    def _on_theme_change(self, idx: int):
        theme = "dark" if idx == 0 else "light"
        if theme == self._current_theme:
            return
        self._current_theme = theme
        self.theme_changed.emit(theme)

    def _labeled_row(self, label: str, widget: QWidget) -> QWidget:
        c = QWidget()
        r = QHBoxLayout(c)
        r.setContentsMargins(0, 4, 0, 4)
        r.setSpacing(12)
        lbl = QLabel(label)
        lbl.setFixedWidth(60)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setStyleSheet("font-size: 13px;")
        r.addWidget(lbl)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        r.addWidget(widget, 1)
        return c
