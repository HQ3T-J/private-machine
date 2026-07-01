"""
StandupSync Desktop — 应用入口
支持: 自动登录（记住我）+ 手动登录
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMessageBox
from theme import DARK_STYLE, LIGHT_STYLE


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(LIGHT_STYLE)

    # ═══ 尝试自动登录 ═══
    from api_client import APIClient
    client = APIClient()

    if client.try_auto_login():
        from app import MainWindow
        window = MainWindow(
            username=client.username or "",
            role=client.role or "",
            api_client=client
        )
        window.show()
        sys.exit(app.exec())

    # ═══ 手动登录 ═══
    from views.login_view import LoginWindow
    login = LoginWindow()
    if login.exec() == LoginWindow.Accepted:
        from app import MainWindow
        username = login.username
        role = login.role
        if not username or not role:
            QMessageBox.critical(None, "错误", "登录信息无效，请重试")
            sys.exit(1)
        window = MainWindow(username=username, role=role, api_client=login.api_client)
        window.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    main()
