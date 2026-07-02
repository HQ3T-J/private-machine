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

# 新增视图（Phase6: To-Do Module 接入）
try:
    from views.notification_view import NotificationView
except ImportError:
    class NotificationView(QWidget):
        title = "通知"
        unread_count_changed = Signal(int)

        def __init__(self, api_client=None, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            lbl = QLabel("通知中心\n(notification_view.py)")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #8E8E9E; font-size: 16px;")
            layout.addWidget(lbl)

        def activate(self):
            pass

try:
    from views.transfer_view import TransferView
except ImportError:
    class TransferView(QWidget):
        title = "转交审核"

        def __init__(self, api_client=None, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            lbl = QLabel("转交审核\n(transfer_view.py)")
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
PAGE_MEETING_ROOM = 5
PAGE_NOTIFICATION = 6
PAGE_TRANSFER = 7


class SidebarButton(QFrame):
    """侧边栏导航按钮：图标 + 文字独立布局，视觉对齐，主题感知。"""

    clicked = Signal()

    DARK_ACTIVE_BG = "#0F3460"
    DARK_INACTIVE_TEXT = "#8E8E9E"
    LIGHT_ACTIVE_BG = "#E6F7FF"
    LIGHT_INACTIVE_TEXT = "#8C8C8C"
    ACCENT = "#1890FF"

    def __init__(self, icon: str, label: str, page_index: int, parent=None):
        super().__init__(parent)
        self.page_index = page_index
        self._active = False
        self._theme = "dark"
        self.setFixedHeight(40)
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)

        self._icon_label = QLabel(icon)
        self._icon_label.setFixedWidth(20)
        self._icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._icon_label)

        self._text_label = QLabel(label)
        layout.addWidget(self._text_label)
        layout.addStretch()

        self._apply_theme()

    def mousePressEvent(self, event):
        self.clicked.emit()

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, val: bool):
        self._active = val
        self._apply_theme()

    def set_theme(self, theme: str):
        if theme == self._theme:
            return
        self._theme = theme
        self._apply_theme()

    def _apply_theme(self):
        is_dark = (self._theme == "dark")
        accent = "#4A9ED9" if is_dark else self.ACCENT
        if self._active:
            bg = self.DARK_ACTIVE_BG if is_dark else self.LIGHT_ACTIVE_BG
            text_c = "#FFFFFF" if is_dark else "#1890FF"
            self.setStyleSheet(
                f"SidebarButton {{ background-color: {bg}; border-left: 3px solid {accent}; }}")
            self._icon_label.setStyleSheet(
                f"background: transparent; font-size: 14px; color: {text_c};")
            self._text_label.setStyleSheet(
                f"background: transparent; font-size: 13px; color: {text_c}; font-weight: bold;")
        else:
            text_c = self.DARK_INACTIVE_TEXT if is_dark else self.LIGHT_INACTIVE_TEXT
            hover_bg = "#1A1A3E" if is_dark else "#E6F7FF"
            self.setStyleSheet(
                f"SidebarButton {{ background-color: transparent; border-left: 3px solid transparent; }}"
                f"SidebarButton:hover {{ background-color: {hover_bg}; }}")
            self._icon_label.setStyleSheet(
                f"background: transparent; font-size: 14px; color: {text_c};")
            self._text_label.setStyleSheet(
                f"background: transparent; font-size: 13px; color: {text_c};")


class Sidebar(QFrame):
    """应用侧边栏：Logo + 导航 + 用户信息。"""

    navigated = Signal(int)  # page_index

    def __init__(self, username: str = "", role: str = "", parent=None):
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
        logo_label.setFixedHeight(60)
        logo_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        logo_label.setStyleSheet(
            "color: #4A9ED9; font-size: 18px; font-weight: bold; "
            "padding: 0px 16px;"
        )
        layout.addWidget(logo_label)

        # ── 分割线 ──
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("max-height: 1px; margin: 0 12px;")
        layout.addWidget(sep1)

        # ── 导航按钮（使用固定宽度图标区，确保文字对齐）──
        nav_items = [
            ("\u2630", "站会", PAGE_HOME),
            ("\u2713", "待办", PAGE_TODO),
            ("\u25A3", "看板", PAGE_DASHBOARD),
            ("\u263A", "团队", PAGE_TEAM),
            ("\u25CF", "通知", PAGE_NOTIFICATION),
            ("\u2194", "转交", PAGE_TRANSFER),
            ("\u2699", "设置", PAGE_SETTINGS),
        ]
        for icon, label, idx in nav_items:
            btn = SidebarButton(icon, label, idx)
            btn.clicked.connect(lambda checked=False, i=idx: self.set_active(i))
            self._buttons[idx] = btn
            layout.addWidget(btn)

        # ── 弹性空间 ──
        layout.addStretch(1)

        # ── 分割线 ──
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("max-height: 1px; margin: 0 12px;")
        layout.addWidget(sep2)

        # ── 用户区域 ──
        user_frame = QFrame()
        user_frame.setObjectName("SidebarUser")
        user_frame.setFixedHeight(68)
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
        self.setObjectName("Sidebar")

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
            # 隐藏"团队"和"转交审核"
            for idx, btn in self._buttons.items():
                btn.setVisible(idx not in (PAGE_TEAM, PAGE_TRANSFER))
        elif role in ("observer",):
            # 只显示"站会"、"看板"、"通知"
            for idx, btn in self._buttons.items():
                btn.setVisible(idx in (PAGE_HOME, PAGE_DASHBOARD, PAGE_NOTIFICATION))
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
        """设置导航按钮角标"""
        if page_index in self._buttons:
            btn = self._buttons[page_index]
            base = btn._text_label.text()
            # Strip existing count
            if " (" in base:
                base = base.split(" (")[0]
            if count > 0:
                btn._text_label.setText(f"{base} ({count})")
            else:
                btn._text_label.setText(base)

    def set_theme(self, theme: str):
        """切换侧边栏主题（深色/浅色）"""
        is_dark = (theme == "dark")
        bg = "#1A1A2E" if is_dark else "#FFFFFF"
        border = "#2A2A4A" if is_dark else "#E5E5E5"
        sep = "#2A2A4A" if is_dark else "#E5E5E5"
        logo_color = "#4A9ED9" if is_dark else "#1890FF"
        name_color = "#E0E0E0" if is_dark else "#262626"
        role_color = "#8E8E9E" if is_dark else "#8C8C8C"

        self.setStyleSheet(f"#Sidebar {{ background-color: {bg}; border-right: 1px solid {border}; }}")
        for btn in self._buttons.values():
            btn.set_theme(theme)


class MainWindow(QMainWindow):
    """StandupSync 主窗口。

    Usage:
        app = QApplication(sys.argv)
        window = MainWindow(username="admin", role="Tech Lead", api_client=None)
        window.show()
        sys.exit(app.exec())
    """

    def __init__(self, username: str = "", role: str = "",
                 api_client=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("StandupSync")
        self.setMinimumSize(1024, 720)
        self.resize(1280, 820)

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
        settings.theme_changed.connect(self._on_theme_changed)
        self._stack.addWidget(settings)
        self._pages[PAGE_SETTINGS] = settings

        # 5: 站会进行中
        meeting_room = MeetingRoomView(api_client=self._api_client)
        meeting_room.navigate_back.connect(self._on_meeting_back)
        self._stack.addWidget(meeting_room)
        self._pages[PAGE_MEETING_ROOM] = meeting_room

        # 6: 通知中心
        notification = NotificationView(api_client=self._api_client)
        notification.unread_count_changed.connect(self._on_unread_count_changed)
        self._stack.addWidget(notification)
        self._pages[PAGE_NOTIFICATION] = notification

        # 7: 转交审核
        transfer = TransferView(api_client=self._api_client)
        self._stack.addWidget(transfer)
        self._pages[PAGE_TRANSFER] = transfer

        # 首页 → 站会室 导航
        home.navigate_to_meeting.connect(self._on_enter_meeting_room)

        main_layout.addWidget(self._stack, 1)

        # 初始页面
        self._stack.setCurrentIndex(PAGE_HOME)
        self._sidebar.set_active(PAGE_HOME)

    # ── 导航切换 ──
    def _on_navigate(self, page_index: int):
        self._current_page = page_index
        self._stack.setCurrentIndex(page_index)
        page = self._pages.get(page_index)
        if page and hasattr(page, "activate"):
            page.activate()

    def _on_theme_changed(self, theme: str):
        """切换全局主题"""
        from theme import DARK_STYLE, LIGHT_STYLE
        style = LIGHT_STYLE if theme == "light" else DARK_STYLE
        QApplication.instance().setStyleSheet(style)
        self._sidebar.set_theme(theme)

    def _on_enter_meeting_room(self, meeting_id, meeting_data=None):
        """从首页进入站会室"""
        room = self._pages.get(PAGE_MEETING_ROOM)
        if room:
            room.activate(meeting_id=meeting_id, meeting_data=meeting_data)
        self._stack.setCurrentIndex(PAGE_MEETING_ROOM)
        self._current_page = PAGE_MEETING_ROOM

    def _on_meeting_back(self):
        """从站会室返回首页"""
        self._stack.setCurrentIndex(PAGE_HOME)
        self._current_page = PAGE_HOME
        self._sidebar.set_active(PAGE_HOME)
        home = self._pages.get(PAGE_HOME)
        if home and hasattr(home, "activate"):
            home.activate()

    # ── 公开方法 ──
    def navigate_to(self, page_index: int):
        """程序化导航到指定页面。"""
        self._sidebar.set_active(page_index)

    def _on_unread_count_changed(self, count):
        """更新侧边栏通知角标"""
        if count > 0:
            display = f"{min(count, 99)}+" if count > 99 else str(count)
            self._sidebar.set_notification(PAGE_NOTIFICATION, int(display) if count <= 99 else 99)
        else:
            self._sidebar.set_notification(PAGE_NOTIFICATION, 0)

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

    window = MainWindow(username="admin", role="Tech Lead")
    window.show()
    sys.exit(app.exec())
