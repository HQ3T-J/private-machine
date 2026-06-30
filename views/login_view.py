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
            QLineEdit {
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 14px;
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

        icon_label = QLabel("📋")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)

        title = QLabel("StandupSync")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #4A90D9; font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        card_layout = QVBoxLayout()
        card_layout.setSpacing(12)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名")
        self.username_input.setMinimumHeight(40)
        card_layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("密码")
        self.password_input.setMinimumHeight(40)
        card_layout.addWidget(self.password_input)

        self.login_btn = QPushButton("登  录")
        self.login_btn.setObjectName("login_btn")
        self.login_btn.setMinimumHeight(40)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self._on_login)
        card_layout.addWidget(self.login_btn)

        layout.addLayout(card_layout)
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet("color: #8E8E9E; font-size: 12px;")
        layout.addWidget(self._status_label)

        signup_label = QLabel('<a href="#" style="color: #4A90D9; text-decoration: none;">还没有账号？注册</a>')
        signup_label.setObjectName("signup_link")
        signup_label.setAlignment(Qt.AlignCenter)
        signup_label.setCursor(Qt.PointingHandCursor)
        signup_label.linkActivated.connect(self._on_signup)
        layout.addWidget(signup_label)

    def _on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "提示", "请输入用户名和密码")
            return

        self._status_label.setText("正在连接服务器...")
        self.login_btn.setEnabled(False)

        try:
            from api_client import APIClient
            client = APIClient()
            result = client.login(username, password)
            if result:
                self.api_client = client
                self.username = client.username
                self.role = client.role or "DEVELOPER"
                self.accept()
            elif not client.online:
                QMessageBox.critical(self, "连接失败",
                    "无法连接到后端服务。\n\n请确认：\n"
                    "1. 后端已启动 (java -jar ...)\n"
                    "2. 端口 8080 未被占用\n"
                    "3. API 地址正确: localhost:8080")
                self._status_label.setText("")
                self.login_btn.setEnabled(True)
            else:
                QMessageBox.warning(self, "登录失败", "用户名或密码错误")
                self._status_label.setText("")
                self.login_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"登录异常: {e}")
            self._status_label.setText("")
            self.login_btn.setEnabled(True)

    def _on_signup(self):
        QMessageBox.information(self, "提示", "注册功能即将开放", QMessageBox.Ok)
