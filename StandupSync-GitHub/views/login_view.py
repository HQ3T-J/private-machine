"""登录窗口 (QDialog) - StandupSync"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap


class LoginWindow(QDialog):
    """登录窗口"""

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.username = ""
        self.role = ""
        self.setWindowTitle("StandupSync - 登录")
        self.setFixedSize(400, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #1A1A2E;
            }
            QLabel {
                color: #E0E0E0;
            }
            QLineEdit {
                background-color: #0F3460;
                color: #E0E0E0;
                border: 1px solid #16213E;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4A90D9;
            }
            QPushButton#login_btn {
                background-color: #4A90D9;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton#login_btn:hover {
                background-color: #5BA0E9;
            }
            QPushButton#login_btn:pressed {
                background-color: #3A80C9;
            }
            QLabel#signup_link {
                color: #4A90D9;
                font-size: 13px;
            }
            QLabel#signup_link:hover {
                color: #6AB0F9;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(15)

        # ---- 顶部图标 + 标题 ----
        icon_label = QLabel("📋")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)

        title = QLabel("StandupSync")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #4A90D9; font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # ---- 卡片容器 ----
        card_layout = QVBoxLayout()
        card_layout.setSpacing(12)

        # 用户名
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名")
        self.username_input.setMinimumHeight(40)
        card_layout.addWidget(self.username_input)

        # 密码
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("密码")
        self.password_input.setMinimumHeight(40)
        card_layout.addWidget(self.password_input)

        # 登录按钮
        self.login_btn = QPushButton("登  录")
        self.login_btn.setObjectName("login_btn")
        self.login_btn.setMinimumHeight(40)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self._on_login)
        card_layout.addWidget(self.login_btn)

        layout.addLayout(card_layout)

        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # ---- 底部注册链接 ----
        signup_label = QLabel('<a href="#" style="color: #4A90D9; text-decoration: none;">还没有账号？注册</a>')
        signup_label.setObjectName("signup_link")
        signup_label.setAlignment(Qt.AlignCenter)
        signup_label.setCursor(Qt.PointingHandCursor)
        signup_label.linkActivated.connect(self._on_signup)
        layout.addWidget(signup_label)

    def _on_login(self):
        """登录按钮点击"""
        self.username = self.username_input.text().strip() or "张三"
        # 演示用，根据用户名映射角色
        role_map = {"admin": "tech_lead", "sm": "scrum_master",
                     "dev": "developer", "obs": "observer"}
        self.role = role_map.get(self.username.lower(), "tech_lead")
        self.accept()

    def keyPressEvent(self, event):
        """回车键登录"""
        if event.key() == event.Key_Return or event.key() == event.Key_Enter:
            self._on_login()
        else:
            super().keyPressEvent(event)

    def _on_signup(self):
        """注册链接点击"""
        QMessageBox.information(
            self,
            "提示",
            "注册功能即将开放",
            QMessageBox.Ok
        )
