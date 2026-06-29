# app.py — 主窗口 + 侧边栏 + 页面路由
"""StandupSync 主窗口：侧边栏导航 + QStackedWidget 页面切换 + 身份权限控制。

集成所有 view 页面，支持独立实例化与完整集成两种模式。
"""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QStackedWidget,
    QSizePolicy,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QFont

# ── 视图导入（子代理 B 的 view 可能尚未创建，做容错处理）──
from views.todo_view import TodoView
from views.dashboard_view import DashboardView
from views.team_view import TeamView

try:
    from views.home_view import HomeView
except ImportError:
    # 占位：子代理 B 的 home_view 尚未创建
    class HomeView(QWidget):
        title = "站会首页"

        def __init__(self, api_client=None, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            lbl = QLabel("站会首页\n(Sub-agent B: home_view.py)")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #8E8E9E; font-size: 16px;")
            layout.addWidget(lbl)

        def activate(self):
            pass

try:
    from views.settings_view import SettingsView
except ImportError:
    class SettingsView(QWidget):
        title = "设置"

        def __init__(self, api_client=None, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            lbl = QLabel("设置\n(Sub-agent B: settings_view.py)")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #8E8E9E; font-size: 16px;")
            layout.addWidget(lbl)

        def activate(self):
            pass

# 如果主入口提供了 meeting_room_view / ai_result_view，可通过 set_extra_views 注入
try:
    from views.meeting_room_view import MeetingRoomView
except ImportError:
    MeetingRoomView = None
try:
    from views.ai_result_view import AIResultView
except ImportError:
    AIResultView = None

# ── 页面索引常量 ──
PAGE_HOME = 0
PAGE_TODO = 1
PAGE_DASHBOARD = 2
PAGE_TEAM = 3
PAGE_SETTINGS = 4


class SidebarButton(QPushButton):
    """侧边栏导航按钮，带激活态指示条。"""

    def __init__(self, text: str, page_index: int, parent=None):
        super().__init__(text, parent)
        self.page_index = page_index
        self._active = False
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(34)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._update_style()
        self.clicked.connect(self._on_click)

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, val: bool):
        self._active = val
        self._update_style()

    def _on_click(self):
        # 信号由父级 Sidebar 统一处理
        pass

    def _update_style(self):
        if self._active:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #0F3460;
                    color: #FFFFFF;
                    border: none;
                    border-left: 3px solid #4A9ED9;
                    text-align: left;
                    padding: 0px 16px;
                    font-size: 13px;
                    font-weight: bold;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #8E8E9E;
                    border: none;
                    border-left: 3px solid transparent;
                    text-align: left;
                    padding: 0px 16px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #1A1A3E;
                    color: #C0C0D0;
                }
            """)


class Sidebar(QFrame):
    """应用侧边栏：Logo + 导航 + 用户信息。"""

    navigated = Signal(int)  # page_index

    def __init__(self, username: str = "张三", role: str = "Tech Lead", parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(200)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self._username = username
        self._role = role
        self._buttons: dict[int, SidebarButton] = {}
        self._active_index = PAGE_HOME

        self._setup_ui()
        self._apply_identity_rules()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Logo ──
        logo_label = QLabel("StandupSync")
        logo_label.setObjectName("SidebarLogo")
        logo_label.setFixedHeight(56)
        logo_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        logo_label.setStyleSheet(
            "color: #4A9ED9; font-size: 18px; font-weight: bold; "
            "padding: 0px 16px;"
        )
        layout.addWidget(logo_label)

        # ── 分割线 ──
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("background-color: #2A2A4A; max-height: 1px; margin: 0 12px;")
        layout.addWidget(sep1)

        # ── 导航按钮 ──
        nav_items = [
            ("☰  站会", PAGE_HOME),
            ("☑  待办", PAGE_TODO),
            ("▣  看板", PAGE_DASHBOARD),
            ("👥  团队", PAGE_TEAM),
            ("⚙  设置", PAGE_SETTINGS),
        ]
        for text, idx in nav_items:
            btn = SidebarButton(text, idx)
            btn.clicked.connect(lambda checked, i=idx: self.set_active(i))
            self._buttons[idx] = btn
            layout.addWidget(btn)

        # ── 弹性空间 ──
        layout.addStretch(1)

        # ── 分割线 ──
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background-color: #2A2A4A; max-height: 1px; margin: 0 12px;")
        layout.addWidget(sep2)

        # ── 用户区域 ──
        user_frame = QFrame()
        user_frame.setObjectName("SidebarUser")
        user_frame.setFixedHeight(64)
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(12, 10, 12, 10)
        user_layout.setSpacing(10)

        # 圆形头像
        avatar = QFrame()
        avatar.setObjectName("SidebarAvatar")
        avatar.setFixedSize(36, 36)
        avatar.setStyleSheet(
            "background-color: #4A9ED9; border-radius: 18px; "
            "color: #FFFFFF; font-size: 14px; font-weight: bold;"
        )
        avatar_layout = QVBoxLayout(avatar)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_initials = QLabel(self._username[0] if self._username else "U")
        avatar_initials.setAlignment(Qt.AlignCenter)
        avatar_initials.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold;")
        avatar_layout.addWidget(avatar_initials)

        user_layout.addWidget(avatar)

        # 用户名 + 角色
        user_info = QVBoxLayout()
        user_info.setSpacing(2)

        name_lbl = QLabel(self._username)
        name_lbl.setStyleSheet("color: #E0E0E0; font-size: 13px; font-weight: bold;")
        user_info.addWidget(name_lbl)

        role_lbl = QLabel(self._role)
        role_lbl.setStyleSheet("color: #8E8E9E; font-size: 11px;")
        user_info.addWidget(role_lbl)

        user_layout.addLayout(user_info)
        user_layout.addStretch()

        layout.addWidget(user_frame)

        # ── 整体样式 ──
        self.setStyleSheet("""
            #Sidebar {
                background-color: #1A1A2E;
                border-right: 1px solid #2A2A4A;
            }
        """)

    # ── 身份权限控制 ──
    def _apply_identity_rules(self):
        role = self._role.lower()

        if role in ("tech_lead", "tech lead", "techlead"):
            # 全部可见
            for btn in self._buttons.values():
                btn.setVisible(True)
        elif role in ("scrum_master", "scrum master", "scrummaster"):
            # 全部可见
            for btn in self._buttons.values():
                btn.setVisible(True)
        elif role in ("developer",):
            # 隐藏"团队"按钮
            for idx, btn in self._buttons.items():
                btn.setVisible(idx != PAGE_TEAM)
        elif role in ("observer",):
            # 只显示"站会"和"看板"
            for idx, btn in self._buttons.items():
                btn.setVisible(idx in (PAGE_HOME, PAGE_DASHBOARD))
        else:
            # 默认全部可见
            pass

    # ── 导航 ──
    def set_active(self, page_index: int):
        if page_index not in self._buttons:
            return
        self._active_index = page_index
        for idx, btn in self._buttons.items():
            btn.active = (idx == page_index)
        self.navigated.emit(page_index)

    def active_index(self) -> int:
        return self._active_index

    def update_user(self, name: str, role: str):
        self._username = name
        self._role = role
        self._apply_identity_rules()

    def set_notification(self, page_index: int, count: int):
        """设置导航按钮角标（简单实现：追加计数到按钮文本）。"""
        if page_index in self._buttons:
            btn = self._buttons[page_index]
            # 提取原始文本（去掉已有的角标）
            base_texts = {
                PAGE_HOME: "☰  站会",
                PAGE_TODO: "☑  待办",
                PAGE_DASHBOARD: "▣  看板",
                PAGE_TEAM: "👥  团队",
                PAGE_SETTINGS: "⚙  设置",
            }
            base = base_texts.get(page_index, btn.text().split(" (")[0])
            if count > 0:
                btn.setText(f"{base} ({count})")
            else:
                btn.setText(base)


class MainWindow(QMainWindow):
    """StandupSync 主窗口。

    Usage:
        app = QApplication(sys.argv)
        window = MainWindow(username="张三", role="Tech Lead")
        window.show()
        sys.exit(app.exec())
    """

    def __init__(self, username: str = "张三", role: str = "Tech Lead",
                 api_client=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("StandupSync")
        self.setMinimumSize(960, 680)
        self.resize(1200, 780)

        self._username = username
        self._role = role
        self._api_client = api_client
        self._current_page = PAGE_HOME

        self._setup_ui()

    def _setup_ui(self):
        # ── 中心部件 ──
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 侧边栏 ──
        self._sidebar = Sidebar(
            username=self._username, role=self._role
        )
        self._sidebar.navigated.connect(self._on_navigate)
        main_layout.addWidget(self._sidebar)

        # ── 右侧内容区 ──
        self._stack = QStackedWidget()
        self._stack.setObjectName("ContentStack")

        # 创建所有页面
        self._pages = {}

        # 0: 站会首页
        home = HomeView(api_client=self._api_client)
        self._stack.addWidget(home)
        self._pages[PAGE_HOME] = home

        # 1: 待办管理
        todo = TodoView(api_client=self._api_client)
        self._stack.addWidget(todo)
        self._pages[PAGE_TODO] = todo

        # 2: 数据看板
        dashboard = DashboardView(api_client=self._api_client)
        self._stack.addWidget(dashboard)
        self._pages[PAGE_DASHBOARD] = dashboard

        # 3: 团队管理
        team = TeamView(api_client=self._api_client)
        team.current_role = self._role
        self._stack.addWidget(team)
        self._pages[PAGE_TEAM] = team

        # 4: 设置
        settings = SettingsView(api_client=self._api_client)
        self._stack.addWidget(settings)
        self._pages[PAGE_SETTINGS] = settings

        main_layout.addWidget(self._stack, 1)

        # 初始页面
        self._stack.setCurrentIndex(PAGE_HOME)
        self._sidebar.set_active(PAGE_HOME)

        # ── 全局暗色背景 ──
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0D1117;
            }
            #ContentStack {
                background-color: #0D1117;
            }
        """)

    # ── 导航切换 ──
    def _on_navigate(self, page_index: int):
        if page_index == self._current_page:
            return
        self._current_page = page_index
        self._stack.setCurrentIndex(page_index)
        # 激活页面
        page = self._pages.get(page_index)
        if page and hasattr(page, "activate"):
            page.activate()

    # ── 公开方法 ──
    def navigate_to(self, page_index: int):
        """程序化导航到指定页面。"""
        self._sidebar.set_active(page_index)

    def set_extra_views(self, extra: dict):
        """注册额外的页面（如会议页面等），用于子代理 B 集成。

        Args:
            extra: {page_index: QWidget} 例如 {5: MeetingRoomView(), 6: AIResultView()}
        """
        for idx, widget in extra.items():
            while self._stack.count() <= idx:
                self._stack.addWidget(QWidget())  # 占位
            # 替换占位
            self._stack.removeWidget(self._stack.widget(idx))
            self._stack.insertWidget(idx, widget)
            self._pages[idx] = widget


# ── 独立运行入口（调试用）──
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    try:
        from theme import DARK_STYLE
        app.setStyleSheet(DARK_STYLE)
    except ImportError:
        pass

    window = MainWindow(username="张三", role="Tech Lead")
    window.show()
    sys.exit(app.exec())
