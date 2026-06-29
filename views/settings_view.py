"""设置页面 - StandupSync"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QGroupBox, QSizePolicy,
    QSpacerItem
)
from PySide6.QtCore import Qt


class SettingsView(QWidget):
    """设置页面"""

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.title = "设置"
        self.setStyleSheet(self._base_style())
        self._setup_ui()

    def _base_style(self):
        return """
            QWidget {
                background-color: #1A1A2E;
                color: #E0E0E0;
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #CCCCCC;
                border: 1px solid #0F3460;
                border-radius: 10px;
                margin-top: 16px;
                padding: 20px 16px 16px 16px;
                background-color: #16213E;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
            }
            QLineEdit {
                background-color: #0F3460;
                color: #E0E0E0;
                border: 1px solid #1A1A2E;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #4A90D9;
            }
            QComboBox {
                background-color: #0F3460;
                color: #E0E0E0;
                border: 1px solid #1A1A2E;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #16213E;
                color: #E0E0E0;
                selection-background-color: #0F3460;
                border: 1px solid #0F3460;
            }
            QCheckBox {
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #4A90D9;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #4A90D9;
            }
        """

    def activate(self):
        """页面显示时调用"""
        pass

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # ---- 页面标题 ----
        title_label = QLabel("⚙ 设置")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(title_label)

        # ---- 分区1: 个人信息 ----
        profile_group = self._create_profile_section()
        layout.addWidget(profile_group)

        # ---- 分区2: AI 设置 ----
        ai_group = self._create_ai_section()
        layout.addWidget(ai_group)

        # ---- 分区3: 通知设置 ----
        notification_group = self._create_notification_section()
        layout.addWidget(notification_group)

        # ---- 分区4: 外观 ----
        appearance_group = self._create_appearance_section()
        layout.addWidget(appearance_group)

        layout.addStretch(1)

        # ---- 底部: 退出登录 ----
        logout_btn = QPushButton("退出登录")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #FF4D4D;
                border: 1px solid #FF4D4D;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 77, 77, 0.15);
            }
        """)
        logout_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(logout_btn)

    def _form_row(self, label_text, widget):
        """创建表单行: 标签 + 控件"""
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 4, 0, 4)
        row.setSpacing(12)

        label = QLabel(label_text)
        label.setStyleSheet("font-size: 13px; color: #AAAAAA;")
        label.setFixedWidth(70)
        row.addWidget(label)

        row.addWidget(widget, 1)
        return container

    def _create_profile_section(self):
        group = QGroupBox("👤 个人信息")
        gl = QVBoxLayout(group)
        gl.setSpacing(10)

        # 头像占位
        avatar_row = QHBoxLayout()
        avatar = QLabel("👤")
        avatar.setStyleSheet("font-size: 40px;")
        avatar.setFixedSize(60, 60)
        avatar.setAlignment(Qt.AlignCenter)
        avatar_row.addWidget(avatar)
        avatar_row.addStretch()
        gl.addLayout(avatar_row)

        # 昵称
        self.nickname_input = QLineEdit()
        self.nickname_input.setPlaceholderText("输入昵称")
        gl.addWidget(self._form_row("昵称", self.nickname_input))

        # 身份
        role_row = QHBoxLayout()
        role_label = QLabel("身份")
        role_label.setStyleSheet("font-size: 13px; color: #AAAAAA;")
        role_label.setFixedWidth(70)
        role_row.addWidget(role_label)

        self.role_value = QLabel("开发者")
        self.role_value.setStyleSheet("font-size: 13px; color: #4A90D9;")
        role_row.addWidget(self.role_value)
        role_row.addStretch()
        gl.addLayout(role_row)

        # 保存按钮
        save_row = QHBoxLayout()
        save_row.addStretch()
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90D9;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5BA0E9;
            }
        """)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_row.addWidget(save_btn)
        gl.addLayout(save_row)

        return group

    def _create_ai_section(self):
        group = QGroupBox("🤖 AI 设置")
        gl = QVBoxLayout(group)
        gl.setSpacing(10)

        # 服务商
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["豆包", "通义千问", "OpenAI", "自定义"])
        gl.addWidget(self._form_row("服务商", self.provider_combo))

        # 模型
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("输入模型名称")
        gl.addWidget(self._form_row("模型", self.model_input))

        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("输入 API Key")
        gl.addWidget(self._form_row("API Key", self.api_key_input))

        # 测试连接按钮
        test_row = QHBoxLayout()
        test_row.addStretch()
        test_btn = QPushButton("测试连接")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #0F3460;
                color: #E0E0E0;
                border: 1px solid #4A90D9;
                border-radius: 6px;
                padding: 6px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1A4A7A;
            }
        """)
        test_btn.setCursor(Qt.PointingHandCursor)
        test_row.addWidget(test_btn)
        gl.addLayout(test_row)

        return group

    def _create_notification_section(self):
        group = QGroupBox("🔔 通知设置")
        gl = QVBoxLayout(group)
        gl.setSpacing(10)

        self.standup_reminder = QCheckBox("站会提醒")
        self.standup_reminder.setChecked(True)
        gl.addWidget(self.standup_reminder)

        self.todo_reminder = QCheckBox("待办到期提醒")
        self.todo_reminder.setChecked(True)
        gl.addWidget(self.todo_reminder)

        self.assign_notify = QCheckBox("分配通知")
        self.assign_notify.setChecked(True)
        gl.addWidget(self.assign_notify)

        return group

    def _create_appearance_section(self):
        group = QGroupBox("🎨 外观")
        gl = QVBoxLayout(group)
        gl.setSpacing(10)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色", "跟随系统"])
        self.theme_combo.setCurrentIndex(1)  # 默认深色
        gl.addWidget(self._form_row("主题", self.theme_combo))

        return group
