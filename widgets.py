"""
可复用 UI 组件：StatCard, EmptyState, Toast
"""

from PySide6.QtWidgets import (
    QFrame, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect,
    QApplication,
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, Property, QPoint,
)
from PySide6.QtGui import QFont


# ============================================================================
# StatCard — 关键数字卡片
# ============================================================================

class StatCard(QFrame):
    """
    关键数字卡片组件。

    参数:
        title (str): 卡片标题（显示在顶部，灰色小字）
        value (str): 主要数值（24px 大字）
        trend (str): 趋势文本，如 "↑2"
        trend_color (str): 趋势颜色，如 "#52C41A" / "#E74C3C"
    """

    def __init__(self, title="", value="", trend="", trend_color="#52C41A",
                 parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setMinimumSize(160, 90)

        # 卡片基础样式（颜色由全局主题控制）
        self.setStyleSheet("""
            QFrame#StatCard {
                border-radius: 10px;
            }
        """)

        # ----- 主布局 -----
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        # 标题
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self._title_label)

        # 数值行（数值 + 趋势）
        value_row = QHBoxLayout()
        value_row.setSpacing(8)

        self._value_label = QLabel(value)
        self._value_label.setFont(QFont("Microsoft YaHei", 24, QFont.Weight.Bold))
        value_row.addWidget(self._value_label)

        self._trend_label = QLabel(trend)
        self._trend_label.setStyleSheet(
            f"color: {trend_color}; font-size: 12px; font-weight: bold;"
        )
        value_row.addWidget(self._trend_label)
        value_row.addStretch()

        layout.addLayout(value_row)

    # ---------- 属性接口 ----------

    @property
    def title(self):
        return self._title_label.text()

    @title.setter
    def title(self, text):
        self._title_label.setText(text)

    @property
    def value(self):
        return self._value_label.text()

    @value.setter
    def value(self, text):
        self._value_label.setText(text)

    @property
    def trend(self):
        return self._trend_label.text()

    @trend.setter
    def trend(self, text):
        self._trend_label.setText(text)

    @property
    def trend_color(self):
        return self._trend_label.styleSheet()

    @trend_color.setter
    def trend_color(self, color):
        self._trend_label.setStyleSheet(
            f"color: {color}; font-size: 12px; font-weight: bold;"
        )


# ============================================================================
# EmptyState — 空状态占位组件
# ============================================================================

class EmptyState(QWidget):
    """
    空状态占位组件，用于列表/表格为空时的友好提示。

    参数:
        icon (str): emoji 文本，如 "📭"
        title (str): 标题文字
        subtitle (str): 副标题 / 提示文字
    """

    def __init__(self, icon="📭", title="暂无数据", subtitle="",
                 parent=None):
        super().__init__(parent)
        self.setObjectName("EmptyState")

        # ----- 主布局（居中）-----
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        # 图标
        self._icon_label = QLabel(icon)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(self._icon_label)

        # 标题
        self._title_label = QLabel(title)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(self._title_label)

        # 副标题
        self._subtitle_label = QLabel(subtitle)
        self._subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle_label.setStyleSheet("font-size: 12px;")
        self._subtitle_label.setWordWrap(True)
        layout.addWidget(self._subtitle_label)

    # ---------- 属性接口 ----------

    @property
    def icon(self):
        return self._icon_label.text()

    @icon.setter
    def icon(self, text):
        self._icon_label.setText(text)

    @property
    def title(self):
        return self._title_label.text()

    @title.setter
    def title(self, text):
        self._title_label.setText(text)

    @property
    def subtitle(self):
        return self._subtitle_label.text()

    @subtitle.setter
    def subtitle(self, text):
        self._subtitle_label.setText(text)


# ============================================================================
# Toast — 右下角通知弹出
# ============================================================================

_TOAST_COLORS = {
    "info":    ("#1A1A2E", "#4A9ED9", "ℹ"),
    "success": ("#1A1A2E", "#52C41A", "✓"),
    "warning": ("#1A1A2E", "#F5A623", "⚠"),
    "error":   ("#1A1A2E", "#E74C3C", "✗"),
}


class Toast(QWidget):
    """
    右下角通知弹出组件，自动淡出消失。

    参数:
        message (str): 通知文字
        duration (int): 显示时长（毫秒），默认 3000
        type (str): 类型 — 'info' / 'success' / 'warning' / 'error'
        parent (QWidget): 父窗口（通常传入顶层窗口引用）
    """

    def __init__(self, message="", duration=3000, type="info",
                 parent=None):
        super().__init__(parent)
        self._duration = duration
        self._type = type

        bg, accent, icon_char = _TOAST_COLORS.get(type, _TOAST_COLORS["info"])

        self.setObjectName("Toast")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # 整体样式
        self.setStyleSheet(f"""
            QWidget#Toast {{
                border: 1px solid {accent};
                border-left: 4px solid {accent};
                border-radius: 8px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # 图标
        icon_label = QLabel(icon_char)
        icon_label.setStyleSheet(
            f"color: {accent}; font-size: 18px; font-weight: bold;"
        )
        layout.addWidget(icon_label)

        # 消息
        msg_label = QLabel(message)
        msg_label.setStyleSheet("color: #FFFFFF; font-size: 13px;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label, 1)

        # 初始透明度
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)

        # 淡入动画
        self._fade_in = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_in.setDuration(200)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 淡出动画
        self._fade_out = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_out.setDuration(400)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_out.finished.connect(self.close)

    # ---------- 显示 ----------

    def show(self):
        """显示 Toast 并启动自动消失计时器。"""
        super().show()
        self._position_bottom_right()
        self._fade_in.start()

        QTimer.singleShot(self._duration, self._start_fade_out)

    # ---------- 内部方法 ----------

    def _position_bottom_right(self):
        """将 Toast 定位到屏幕右下角。"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.availableGeometry()
            toast_size = self.sizeHint()
            x = screen_geom.right() - toast_size.width() - 20
            y = screen_geom.bottom() - toast_size.height() - 40
            self.move(QPoint(x, y))

    def _start_fade_out(self):
        self._fade_out.start()

    # ---------- 静态工厂 ----------

    @staticmethod
    def show_message(parent, message, duration=3000, type="info"):
        """
        便捷方法：创建并立即显示一条 Toast。

        示例:
            Toast.show_message(self, "保存成功", type="success")
        """
        toast = Toast(message=message, duration=duration, type=type,
                      parent=parent)
        toast.show()
        return toast
