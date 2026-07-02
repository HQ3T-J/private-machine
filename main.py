"""
StandupSync Desktop — 应用入口
支持: 自动登录（记住我）+ 手动登录
"""
import sys
import os
import json
from PySide6.QtWidgets import QApplication, QMessageBox
from theme import DARK_STYLE, LIGHT_STYLE


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(DARK_STYLE)

    # 存储窗口尺寸/位置
    settings_path = os.path.join(os.path.expanduser("~"), ".standupsync_window.json")

    def save_window_geometry():
        try:
            geo = {
                "x": window.x(), "y": window.y(),
                "w": window.width(), "h": window.height()
            }
            with open(settings_path, "w") as f:
                json.dump(geo, f)
        except Exception:
            pass

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
        # 恢复窗口尺寸
        try:
            with open(settings_path) as f:
                geo = json.load(f)
            window.resize(geo.get("w", 1280), geo.get("h", 820))
            window.move(geo.get("x", 100), geo.get("y", 100))
        except Exception:
            window.resize(1280, 820)
        window.show()
        app.aboutToQuit.connect(save_window_geometry)
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
        try:
            with open(settings_path) as f:
                geo = json.load(f)
            window.resize(geo.get("w", 1280), geo.get("h", 820))
            window.move(geo.get("x", 100), geo.get("y", 100))
        except Exception:
            window.resize(1280, 820)
        window.show()
        app.aboutToQuit.connect(save_window_geometry)
        sys.exit(app.exec())


if __name__ == '__main__':
    main()
