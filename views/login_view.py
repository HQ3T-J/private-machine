"""登录/注册窗口 - StandupSync"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QStackedWidget, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt


class LoginWindow(QDialog):
    """登录+注册窗口 — QStackedWidget 切换两张表单"""

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.username = ""
        self.role = ""
        self.setWindowTitle("StandupSync - 登录")
        self.setFixedSize(420, 460)
        self.setStyleSheet("""
            QLineEdit {
                border-radius: 6px; padding: 10px 12px; font-size: 14px;
                border: 1px solid #555; background: #0D1117; color: #C0C0D0;
            }
            QLineEdit:focus { border: 1px solid #4A90D9; }
            QPushButton#action_btn {
                background-color: #4A90D9; color: #FFF; border: none;
                border-radius: 8px; font-size: 15px; font-weight: bold;
            }
            QPushButton#action_btn:hover { background-color: #5BA0E9; }
            QPushButton#action_btn:pressed { background-color: #3A80C9; }
            QPushButton#action_btn:disabled { background-color: #3A5A7A; }
            QLabel#switch_link { color: #4A90D9; font-size: 13px; }
            QLabel#switch_link:hover { color: #6AB0F9; }
            QLabel#error_label { color: #E74C3C; font-size: 12px; }
            QLabel#hint_label { color: #F5A623; font-size: 11px; }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30); layout.setSpacing(12)

        # Logo
        icon = QLabel("📋"); icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 48px;"); layout.addWidget(icon)

        self._title = QLabel("StandupSync")
        self._title.setAlignment(Qt.AlignCenter)
        self._title.setStyleSheet("color:#4A90D9;font-size:22px;font-weight:bold;")
        layout.addWidget(self._title)

        # 堆栈：两张表单
        self._stack = QStackedWidget()
        self._login_form = self._create_login_form()
        self._register_form = self._create_register_form()
        self._stack.addWidget(self._login_form)   # index 0
        self._stack.addWidget(self._register_form) # index 1
        layout.addWidget(self._stack)

        layout.addStretch()

    # ═══════════════════════════════════════════════════
    #  登录表单
    # ═══════════════════════════════════════════════════
    def _create_login_form(self) -> QFrame:
        f = QFrame()
        l = QVBoxLayout(f); l.setContentsMargins(0, 0, 0, 0); l.setSpacing(12)

        self._login_user = QLineEdit(); self._login_user.setPlaceholderText("用户名")
        self._login_user.setMinimumHeight(40); l.addWidget(self._login_user)

        self._login_pass = QLineEdit(); self._login_pass.setPlaceholderText("密码")
        self._login_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self._login_pass.setMinimumHeight(40); l.addWidget(self._login_pass)
        self._login_pass.returnPressed.connect(self._on_login)

        from PySide6.QtWidgets import QCheckBox
        self._remember_cb = QCheckBox("记住我（下次自动登录）")
        self._remember_cb.setStyleSheet("color:#8E8E9E;font-size:12px;")
        self._remember_cb.setChecked(True)
        l.addWidget(self._remember_cb)

        self._login_error = QLabel(""); self._login_error.setObjectName("error_label")
        self._login_error.setAlignment(Qt.AlignCenter); l.addWidget(self._login_error)

        self._login_btn = QPushButton("登  录")
        self._login_btn.setObjectName("action_btn"); self._login_btn.setMinimumHeight(42)
        self._login_btn.setCursor(Qt.PointingHandCursor)
        self._login_btn.clicked.connect(self._on_login); l.addWidget(self._login_btn)

        switch = QLabel('<a href="#" style="color:#4A90D9;text-decoration:none;">没有账号？注册</a>')
        switch.setObjectName("switch_link"); switch.setAlignment(Qt.AlignCenter)
        switch.setCursor(Qt.PointingHandCursor)
        switch.linkActivated.connect(lambda: self._show_form(1)); l.addWidget(switch)
        return f

    # ═══════════════════════════════════════════════════
    #  注册表单
    # ═══════════════════════════════════════════════════
    def _create_register_form(self) -> QFrame:
        f = QFrame()
        l = QVBoxLayout(f); l.setContentsMargins(0, 0, 0, 0); l.setSpacing(12)

        self._reg_user = QLineEdit(); self._reg_user.setPlaceholderText("用户名 (必填，至少3位)")
        self._reg_user.setMinimumHeight(40); l.addWidget(self._reg_user)

        self._reg_pass = QLineEdit(); self._reg_pass.setPlaceholderText("密码 (必填，至少4位)")
        self._reg_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self._reg_pass.setMinimumHeight(40); l.addWidget(self._reg_pass)
        self._reg_pass.returnPressed.connect(self._on_register)

        self._reg_nick = QLineEdit(); self._reg_nick.setPlaceholderText("昵称 (可选，默认同用户名)")
        self._reg_nick.setMinimumHeight(40); l.addWidget(self._reg_nick)

        self._reg_hint = QLabel("")
        self._reg_hint.setObjectName("hint_label"); self._reg_hint.setAlignment(Qt.AlignCenter)
        l.addWidget(self._reg_hint)

        self._reg_btn = QPushButton("注  册")
        self._reg_btn.setObjectName("action_btn"); self._reg_btn.setMinimumHeight(42)
        self._reg_btn.setCursor(Qt.PointingHandCursor)
        self._reg_btn.clicked.connect(self._on_register); l.addWidget(self._reg_btn)

        switch = QLabel('<a href="#" style="color:#4A90D9;text-decoration:none;">已有账号？返回登录</a>')
        switch.setObjectName("switch_link"); switch.setAlignment(Qt.AlignCenter)
        switch.setCursor(Qt.PointingHandCursor)
        switch.linkActivated.connect(lambda: self._show_form(0)); l.addWidget(switch)
        return f

    # ── 表单切换 ──
    def _show_form(self, idx):
        self._stack.setCurrentIndex(idx)
        if idx == 0:
            self._title.setText("StandupSync"); self._login_error.setText("")
        else:
            self._title.setText("注册账号"); self._reg_hint.setText("")
        # 清空字段
        self._login_user.clear(); self._login_pass.clear()
        self._reg_user.clear(); self._reg_pass.clear(); self._reg_nick.clear()

    # ═══════════════════════════════════════════════════
    #  登录
    # ═══════════════════════════════════════════════════
    def _on_login(self):
        username = self._login_user.text().strip()
        password = self._login_pass.text().strip()
        if not username or not password:
            self._login_error.setText("请输入用户名和密码"); return
        if len(password) < 2:  # P2: 前端最小长度校验
            self._login_error.setText("密码至少2位"); return

        self._login_error.setText("正在连接..."); self._login_btn.setEnabled(False)

        try:
            from api_client import APIClient
            client = APIClient()
            result = client.login(username, password)
            if result:
                self.api_client = client
                self.username = client.username
                self.role = client.role or "DEVELOPER"
                if self._remember_cb.isChecked():
                    client.save_session(remember=True)
                self.accept()
            elif not client.online:
                self._login_error.setText("无法连接到服务器 (localhost:8080)")
            else:
                self._login_error.setText("用户名或密码错误")
        except Exception as e:
            self._login_error.setText(f"异常: {e}")
        finally:
            self._login_btn.setEnabled(True)

    # ═══════════════════════════════════════════════════
    #  注册
    # ═══════════════════════════════════════════════════
    def _on_register(self):
        username = self._reg_user.text().strip()
        password = self._reg_pass.text().strip()
        nickname = self._reg_nick.text().strip()

        # P2: 前端校验
        if not username:
            self._reg_hint.setText("用户名不能为空"); return
        if len(username) < 3:
            self._reg_hint.setText("用户名至少3位"); return
        if not password:
            self._reg_hint.setText("密码不能为空"); return
        if len(password) < 4:
            self._reg_hint.setText("密码至少4位"); return
        if not any(c.isalpha() for c in username):
            self._reg_hint.setText("用户名需包含字母"); return

        # P7: 禁用按钮防重复提交
        self._reg_hint.setText("正在注册...")
        self._reg_btn.setEnabled(False)

        try:
            from api_client import APIClient
            client = APIClient()

            # P3: 网络检测
            if not client.online:
                self._reg_hint.setText("无法连接到服务器")
                self._reg_btn.setEnabled(True); return

            result = client.register(username, password, nickname)

            if result is None:
                self._reg_hint.setText("注册失败，无法连接服务器")
                self._reg_btn.setEnabled(True); return

            # 成功: register() 返回 data dict (无code)，已设 client.token
            if client.token:
                self.api_client = client
                self.username = client.username
                self.role = client.role or "DEVELOPER"
                client.save_session(remember=True)
                self.accept()
                return

            # 失败: register() 返回完整响应 (含code)
            code = result.get("code", 500)
            if code == 400:
                self._reg_hint.setText(result.get("message", "账号已存在"))
            else:
                msg = result.get("message", f"服务器错误 ({code})")
                self._reg_hint.setText(msg)
        except Exception as e:
            self._reg_hint.setText(f"异常: {e}")
        finally:
            self._reg_btn.setEnabled(True)
