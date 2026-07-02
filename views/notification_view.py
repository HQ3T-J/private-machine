# views/notification_view.py — 通知中心页面
"""通知中心视图：通知卡片列表，支持标记已读与自动轮询。"""

from datetime import datetime, timezone

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QTimer

from widgets import EmptyState


# ── 通知类型 → 中文标签 + 左侧色条颜色 ──
_NOTIFICATION_CONFIG = {
    "TODO_ASSIGNED":      ("待办分配", "#4A9ED9"),
    "TODO_TRANSFERRED":   ("待办转交", "#4A9ED9"),
    "TRANSFER_APPROVED":  ("转交通过", "#52C41A"),
    "TRANSFER_REJECTED":  ("转交驳回", "#E74C3C"),
    "TODO_COMPLETED":     ("待办完成", "#8E8E9E"),
}

_FALLBACK_CONFIG = ("系统通知", "#8E8E9E")

_POLL_INTERVAL_MS = 30_000  # 30 秒


def _time_ago(iso_str: str) -> str:
    """将 ISO 时间字符串转为「X 分钟前 / X 小时前」等中文表述。"""
    if not iso_str:
        return "—"
    try:
        # 处理带时区的 ISO 字符串，如 "2026-07-02T10:30:00+08:00"
        dt = datetime.fromisoformat(iso_str)
    except (ValueError, TypeError):
        try:
            # 尝试替换 Z 为 +00:00
            dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return iso_str[:16]

    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    diff = now - dt
    seconds = int(diff.total_seconds())

    if seconds < 0:
        return "刚刚"
    if seconds < 60:
        return f"{seconds} 秒前"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} 分钟前"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} 小时前"
    days = hours // 24
    if days < 30:
        return f"{days} 天前"
    months = days // 30
    return f"{months} 个月前"


class _NotificationCard(QFrame):
    """单条通知卡片：左侧色条 + 类型标签 + 时间 + 内容。点击标记已读。"""

    clicked = Signal(str)  # notification_id

    def __init__(self, notification: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("NotificationCard")
        self._notification = notification
        self._nid = str(notification.get("id", ""))

        ntype = notification.get("type", "")
        self._type_label, accent = _NOTIFICATION_CONFIG.get(ntype, _FALLBACK_CONFIG)

        is_read = notification.get("read", False)
        self._is_read = is_read

        # 卡片整体样式：背景由全局 QSS 管理，左侧 3px 色条
        self.setStyleSheet(f"""
            QFrame#NotificationCard {{
                border-left: 3px solid {accent};
                border-radius: 6px;
                margin: 2px 0;
                padding: 0;
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)

        # ── 主布局 ──
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # 第一行：●/○ + 类型标签 + 时间
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        dot = "○" if is_read else "●"
        self._dot_label = QLabel(dot)
        self._dot_label.setFixedWidth(18)
        self._dot_label.setStyleSheet(
            f"font-size: 14px; color: {accent}; font-weight: bold;"
        )
        top_row.addWidget(self._dot_label)

        self._type_widget = QLabel(self._type_label)
        self._type_widget.setStyleSheet(
            f"font-size: 12px; color: {accent}; "
            "font-weight: bold; "
            'font-family: "Microsoft YaHei", "Segoe UI", sans-serif;'
        )
        top_row.addWidget(self._type_widget)

        top_row.addStretch()

        created_at = notification.get("createdAt", "")
        self._time_label = QLabel(_time_ago(created_at))
        self._time_label.setStyleSheet("font-size: 11px; color: #8E8E9E;")
        top_row.addWidget(self._time_label)

        layout.addLayout(top_row)

        # 第二行：通知内容
        content = notification.get("content") or notification.get("message", "")
        self._content_label = QLabel(content)
        self._content_label.setWordWrap(True)
        self._content_label.setStyleSheet("font-size: 13px;")
        self._content_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        if not is_read:
            # 未读：加粗
            self._content_label.setStyleSheet("font-size: 13px; font-weight: bold;")
            self._type_widget.setStyleSheet(
                f"font-size: 12px; color: {accent}; font-weight: bold;"
            )

        layout.addWidget(self._content_label)

    # ── 点击事件 ──
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._nid)
        super().mousePressEvent(event)

    # ── 更新已读状态 ──
    def mark_read(self):
        self._is_read = True
        self._dot_label.setText("○")
        self._content_label.setStyleSheet("font-size: 13px;")
        accent = _NOTIFICATION_CONFIG.get(
            self._notification.get("type", ""), _FALLBACK_CONFIG
        )[1]
        self._type_widget.setStyleSheet(
            f"font-size: 12px; color: {accent}; "
            'font-family: "Microsoft YaHei", "Segoe UI", sans-serif;'
        )


class NotificationView(QWidget):
    """通知中心页面。"""

    title = "通知"
    unread_count_changed = Signal(int)

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._notifications: list = []
        self._cards: list[_NotificationCard] = []

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(_POLL_INTERVAL_MS)
        self._poll_timer.timeout.connect(self._poll_unread_count)

        self.setObjectName("NotificationView")
        self._setup_ui()

    # ── UI 构建 ──
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # ── 顶部：标题 + "全部已读" 按钮 ──
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        title_label = QLabel("通知中心")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_row.addWidget(title_label)

        header_row.addStretch()

        self._mark_all_btn = QPushButton("全部已读")
        self._mark_all_btn.setCursor(Qt.PointingHandCursor)
        self._mark_all_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #4A9ED9;
                border: 1px solid #4A9ED9;
                border-radius: 4px;
                padding: 4px 14px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(74, 158, 217, 0.15);
            }
        """)
        self._mark_all_btn.clicked.connect(self._on_mark_all_read)
        header_row.addWidget(self._mark_all_btn)

        layout.addLayout(header_row)

        # ── 滚动区域 ──
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet("QScrollArea { border: none; }")

        # 内容容器
        self._list_container = QWidget()
        self._list_container.setObjectName("NotificationListContainer")
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        self._list_layout.setAlignment(Qt.AlignTop)

        self._scroll.setWidget(self._list_container)
        layout.addWidget(self._scroll, 1)

        # ── 空状态（初始隐藏）──
        self._empty_state = EmptyState(
            icon="🔔",
            title="暂无通知",
            subtitle="当有待办分配、转交审批或完成通知时，会在这里显示"
        )
        self._empty_state.setVisible(False)
        layout.addWidget(self._empty_state, 1)

    # ── 激活 / 数据加载 ──
    def activate(self):
        """页面激活时从 API 加载通知列表。"""
        self._load_notifications()
        self._poll_timer.start()

    def _load_notifications(self):
        if not self.api_client:
            self._notifications = []
        else:
            self._notifications = self.api_client.get_notifications()
        self._rebuild_list()

    def _rebuild_list(self):
        # 清空旧卡片
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()

        # 清除旧布局中的所有 widget
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        if not self._notifications:
            self._scroll.setVisible(False)
            self._empty_state.setVisible(True)
            self._mark_all_btn.setVisible(False)
        else:
            self._empty_state.setVisible(False)
            self._scroll.setVisible(True)
            self._mark_all_btn.setVisible(True)

            for notification in self._notifications:
                card = _NotificationCard(notification)
                card.clicked.connect(self._on_card_clicked)
                self._cards.append(card)
                self._list_layout.addWidget(card)

            # 底部弹簧 —— 卡片填不满时不拉伸
            self._list_layout.addStretch()

        # 发射一次未读数
        self._emit_unread_count()

    # ── 卡片点击 ──
    def _on_card_clicked(self, nid: str):
        if self.api_client:
            self.api_client.mark_notification_read(nid)
        # 更新本地状态
        for i, n in enumerate(self._notifications):
            if str(n.get("id")) == nid:
                n["read"] = True
                if i < len(self._cards):
                    self._cards[i].mark_read()
                break
        self._emit_unread_count()

    # ── 全部已读 ──
    def _on_mark_all_read(self):
        if self.api_client:
            self.api_client.mark_all_notifications_read()
        for n in self._notifications:
            n["read"] = True
        for card in self._cards:
            card.mark_read()
        self._emit_unread_count()

    # ── 未读数轮询 ──
    def _poll_unread_count(self):
        """30s 定时轮询未读数量，发射信号更新角标。"""
        self._emit_unread_count()

    def _emit_unread_count(self):
        count = sum(1 for n in self._notifications if not n.get("read", False))
        self.unread_count_changed.emit(count)

    # ── 生命周期 ──
    def showEvent(self, event):
        super().showEvent(event)
        if not self._poll_timer.isActive():
            self._poll_timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._poll_timer.stop()
