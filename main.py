"""
StandupSync Desktop — 应用入口
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from theme import DARK_STYLE


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(DARK_STYLE)

    from views.login_view import LoginWindow
    login = LoginWindow()
    if login.exec() == LoginWindow.Accepted:
        from app import MainWindow
        username = login.username or "张三"
        role = login.role or "tech_lead"
        window = MainWindow(username=username, role=role)
        window.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    main()
