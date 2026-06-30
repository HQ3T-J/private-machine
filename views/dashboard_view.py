# views/dashboard_view.py — 数据看板页面，接入看板引擎 + 筛选 UI
"""数据看板视图：统计卡片(带对比箭头) + 趋势图 + 阻碍分布 + 排行 + 筛选工具栏。

activate() 调用 services.dashboard_engine 各 compute_*() 函数刷新真实数据。
筛选工具栏：Sprint 选择器 / 阻碍类型选择器 / 活跃标签行（× 可移除）。
"""

import sys
import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QProgressBar, QSizePolicy, QPushButton,
)
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPolygonF

from services.dashboard_engine import (
    compute_summary, compute_attendance_trend,
    compute_completion_trend, compute_blocker_distribution,
    compute_member_ranking, apply_filters, FilterConfig,
)


# ── 本地 StatCard（带对比箭头）──

class StatCard(QFrame):
    """统计卡片：标题 + 数值 + 上期对比箭头 ↑↓。"""

    def __init__(self, title: str, value: str, subtitle: str = "",
                 color: str = "#4A9ED9", delta: int = 0, parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setFixedSize(200, 100)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 12px;")
        layout.addWidget(title_lbl)

        val_row = QHBoxLayout()
        val_row.setSpacing(6)
        self._value_lbl = QLabel(str(value))
        self._value_lbl.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")
        val_row.addWidget(self._value_lbl)

        self._delta_lbl = QLabel("")
        self._delta_lbl.setStyleSheet("font-size: 11px;")
        val_row.addWidget(self._delta_lbl)
        val_row.addStretch()
        layout.addLayout(val_row)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet("font-size: 11px;")
            layout.addWidget(sub)

        layout.addStretch()
        self.setStyleSheet(f"""
            #StatCard {{
                border-radius: 8px;
                border-left: 3px solid {color};
            }}
        """)

    def update_value(self, text: str, color: str = ""):
        self._value_lbl.setText(str(text))
        if color:
            self._value_lbl.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")

    def update_delta(self, delta: int):
        if delta != 0:
            arrow = "↑" if delta > 0 else "↓"
            delta_color = "#52C41A" if delta > 0 else "#E74C3C"
            self._delta_lbl.setText(f"{arrow}{abs(delta)}")
            self._delta_lbl.setStyleSheet(f"color: {delta_color}; font-size: 11px;")
        else:
            self._delta_lbl.setText("")


# ── 趋势简图（QPainter 绘制折线）──

class TrendMiniChart(QFrame):
    """迷你趋势折线图：用 QPainter 画折线 + 数据点。"""

    def __init__(self, title: str, data: list = None, color: str = "#4A9ED9", parent=None):
        super().__init__(parent)
        self.setObjectName("TrendMiniChart")
        self.setMinimumSize(340, 160)
        self.setFixedHeight(160)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._title = title
        self._data = data or []
        self._color = QColor(color)
        self.setStyleSheet(
            "#TrendMiniChart{border-radius:8px;}"
        )

    def set_data(self, data: list):
        self._data = data
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(QColor("#8E8E9E"))
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.drawText(12, 18, self._title)

        if not self._data or len(self._data) < 2:
            p.setPen(QColor("#6E6E8E"))
            p.drawText(self.rect(), Qt.AlignCenter, "暂无数据")
            p.end()
            return

        margin_l, margin_r, margin_t, margin_b = 40, 20, 30, 30
        w = self.width() - margin_l - margin_r
        h = self.height() - margin_t - margin_b

        rates = [d["rate"] for d in self._data]
        min_r, max_r = min(rates), max(rates)
        rng = max_r - min_r or 0.1

        def to_x(i): return margin_l + int(w * i / (len(self._data) - 1))
        def to_y(r): return margin_t + h - int(h * (r - min_r) / rng)

        pts = [(to_x(i), to_y(r)) for i, r in enumerate(rates)]

        # 填充
        fill_pts = pts + [(pts[-1][0], margin_t + h), (pts[0][0], margin_t + h)]
        p.setBrush(QBrush(QColor(self._color.red(), self._color.green(), self._color.blue(), 40)))
        p.setPen(Qt.NoPen)
        p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in fill_pts]))

        # 折线
        p.setPen(QPen(self._color, 2))
        p.setBrush(Qt.NoBrush)
        for i in range(len(pts) - 1):
            p.drawLine(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])

        # 数据点
        p.setBrush(QBrush(self._color))
        p.setPen(Qt.NoPen)
        for x, y in pts:
            p.drawEllipse(x - 3, y - 3, 6, 6)

        # 日期标签
        p.setPen(QColor("#6E6E8E"))
        p.setFont(QFont("Segoe UI", 7))
        for i, d in enumerate(self._data):
            p.drawText(to_x(i) - 14, margin_t + h + 16, 28, 14, Qt.AlignCenter, d["date"])

        p.end()


# ── 阻碍分布图（色块 + 百分比）──

class BlockerPieChart(QFrame):
    """阻碍分布：横向色块条 + 类型标签 + 百分比文字。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BlockerPieChart")
        self.setMinimumSize(300, 180)
        self.setFixedHeight(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._data = []
        self.setStyleSheet(
            "#BlockerPieChart{border-radius:8px;}"
        )

    def set_data(self, data: list):
        """data: [{type, label, count, color}, ...]"""
        self._data = data
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(QColor("#8E8E9E"))
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.drawText(12, 18, "阻碍类型分布")

        if not self._data:
            p.setPen(QColor("#6E6E8E"))
            p.drawText(self.rect(), Qt.AlignCenter, "暂无阻碍")
            p.end()
            return

        total = sum(item["count"] for item in self._data) or 1
        bar_w = self.width() - 32 - 60  # 留出百分比文字空间

        y = 36
        for item in self._data[:4]:
            color = item.get("color", "#888")
            label = item.get("label", item["type"])
            count = item["count"]
            pct = round(count / total * 100)

            # 色块
            p.setBrush(QBrush(QColor(color)))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(16, y, 14, 14, 3, 3)

            # 标签
            p.setPen(QColor("#C0C0D0"))
            p.setFont(QFont("Segoe UI", 10))
            p.drawText(36, y + 12, f"{label} ({count})")

            # 横向条
            fill_w = int(bar_w * count / total) if total else 0
            p.setBrush(QBrush(QColor(color)))
            p.drawRoundedRect(180, y + 1, fill_w, 12, 4, 4)

            # 百分比
            p.setPen(QColor("#8E8E9E"))
            p.drawText(180 + bar_w + 8, y + 12, f"{pct}%")

            y += 32

        p.end()


# ── 筛选标签 ──

class FilterTag(QFrame):
    """可移除的筛选标签。"""
    remove_clicked = Signal(str)

    def __init__(self, text: str, tag_key: str, parent=None):
        super().__init__(parent)
        self.tag_key = tag_key
        self.setObjectName("FilterTag")
        self.setFixedHeight(26)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 4, 2)
        layout.setSpacing(4)

        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 11px;")
        layout.addWidget(lbl)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(16, 16)
        close_btn.setStyleSheet(
            "QPushButton{color:#8E8E9E;border:none;font-size:12px;} "
            "QPushButton:hover{color:#E74C3C;}"
        )
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(lambda: self.remove_clicked.emit(self.tag_key))
        layout.addWidget(close_btn)

        self.setStyleSheet("#FilterTag{border-radius:4px;}")


# ── DashboardView ──

class DashboardView(QWidget):
    """数据看板页面 — 可独立实例化。"""

    title = "数据看板"

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._raw_data = {}
        self._filters = {"sprint": None, "blocker_type": None}
        self._setup_ui()

    # ── UI 构建 ──
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # ── 筛选工具栏 ──
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        sprint_label = QLabel("Sprint：")
        sprint_label.setStyleSheet("font-size: 13px;")
        filter_bar.addWidget(sprint_label)

        self._sprint_combo = QComboBox()
        self._sprint_combo.addItem("全部")
        self._sprint_combo.setFixedWidth(140)
        self._sprint_combo.setStyleSheet(_combo_style())
        self._sprint_combo.currentTextChanged.connect(self._on_sprint_changed)
        filter_bar.addWidget(self._sprint_combo)

        blocker_label = QLabel("阻碍：")
        blocker_label.setStyleSheet("font-size: 13px;")
        filter_bar.addWidget(blocker_label)

        self._blocker_combo = QComboBox()
        self._blocker_combo.addItems(["全部", "技术", "资源", "沟通", "其他"])
        self._blocker_combo.setFixedWidth(120)
        self._blocker_combo.setStyleSheet(_combo_style())
        self._blocker_combo.currentTextChanged.connect(self._on_blocker_changed)
        filter_bar.addWidget(self._blocker_combo)

        filter_bar.addStretch()
        layout.addLayout(filter_bar)

        # ── 活跃筛选标签行 ──
        self._tags_layout = QHBoxLayout()
        self._tags_layout.setSpacing(6)
        self._tags_layout.addStretch()
        layout.addLayout(self._tags_layout)

        # ── StatCard 行 ──
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        self._stat_cards = {}

        stat_templates = [
            ("card_meetings", "站会次数", "—", "次", "#4A9ED9"),
            ("card_attendance", "出勤率", "—", "", "#52C41A"),
            ("card_completion", "完成率", "—", "", "#F5A623"),
            ("card_blockers", "活跃阻碍", "—", "个", "#E74C3C"),
        ]
        for key, title, val, sub, color in stat_templates:
            card = StatCard(title, val, sub, color, 0)
            self._stat_cards[key] = card
            stats_row.addWidget(card)
        stats_row.addStretch()
        layout.addLayout(stats_row)

        # ── 趋势图行 ──
        trend_row = QHBoxLayout()
        trend_row.setSpacing(16)
        self._trend_attendance = TrendMiniChart("出勤率趋势", [], "#52C41A")
        self._trend_completion = TrendMiniChart("完成率趋势", [], "#F5A623")
        trend_row.addWidget(self._trend_attendance)
        trend_row.addWidget(self._trend_completion)
        trend_row.addStretch()
        layout.addLayout(trend_row)

        # ── 阻碍分布 + 排行 ──
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        self._blocker_chart = BlockerPieChart()
        bottom_row.addWidget(self._blocker_chart)

        # 排行表
        rank_frame = QFrame()
        rank_frame.setObjectName("RankPlaceholder")
        rank_frame.setMinimumSize(340, 180)
        rank_frame.setFixedHeight(180)
        rank_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        rank_layout = QVBoxLayout(rank_frame)
        rank_layout.setContentsMargins(12, 10, 12, 10)

        rank_title = QLabel("个人完成排行")
        rank_title.setStyleSheet("font-size: 12px; font-weight: bold;")
        rank_layout.addWidget(rank_title)

        self._ranking_table = QTableWidget()
        self._ranking_table.setColumnCount(5)
        self._ranking_table.setHorizontalHeaderLabels(
            ["排名", "姓名", "待办数", "完成率", "进度"]
        )
        self._ranking_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._ranking_table.setSelectionMode(QAbstractItemView.NoSelection)
        self._ranking_table.setShowGrid(False)
        self._ranking_table.verticalHeader().setVisible(False)
        self._ranking_table.setAlternatingRowColors(True)
        hdr = self._ranking_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Fixed)
        self._ranking_table.setColumnWidth(0, 40)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.Fixed)
        self._ranking_table.setColumnWidth(2, 60)
        hdr.setSectionResizeMode(3, QHeaderView.Fixed)
        self._ranking_table.setColumnWidth(3, 60)
        hdr.setSectionResizeMode(4, QHeaderView.Fixed)
        self._ranking_table.setColumnWidth(4, 100)
        self._ranking_table.setStyleSheet(_table_style())
        rank_layout.addWidget(self._ranking_table)

        rank_frame.setStyleSheet(
            "#RankPlaceholder{border-radius:8px;}"
        )
        bottom_row.addWidget(rank_frame)
        layout.addLayout(bottom_row)
        layout.addStretch()

    # ── 激活 ──
    def activate(self):
        """页面激活：通过 API 加载真实数据。"""
        self._meetings_cache = []
        self._items_cache = []
        self._team_id = None

        if self.api_client:
            teams = self.api_client.get_teams()
            if teams:
                self._team_id = teams[0].get("id")
                self._load_sprints(self._team_id)
                self._meetings_cache = self.api_client.get_meetings(self._team_id) or []
                self._items_cache = self.api_client.get_todos() or []
            else:
                self._clear_sprints()

        self._apply_and_refresh()

    def _load_sprints(self, team_id):
        """从站会列表提取 Sprint 编号填入下拉框。"""
        meetings = self.api_client.get_meetings(team_id) or []
        sprints = sorted(set(
            m.get("sprintNo") for m in meetings if m.get("sprintNo") is not None
        ), reverse=True)
        current = self._sprint_combo.currentText()
        self._sprint_combo.blockSignals(True)
        self._sprint_combo.clear()
        self._sprint_combo.addItem("全部")
        for s in sprints:
            self._sprint_combo.addItem(f"Sprint #{s}")
        idx = self._sprint_combo.findText(current)
        self._sprint_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._sprint_combo.blockSignals(False)

    def _clear_sprints(self):
        self._sprint_combo.blockSignals(True)
        self._sprint_combo.clear()
        self._sprint_combo.addItem("全部")
        self._sprint_combo.blockSignals(False)

    # ── 筛选事件 ──
    def _on_sprint_changed(self, text: str):
        sprint_no = None if text == "全部" else int(text.split("#")[1])
        self._filters["sprint"] = sprint_no
        self._sync_tags()
        self._apply_and_refresh()

    def _on_blocker_changed(self, text: str):
        self._filters["blocker_type"] = None if text == "全部" else _BLOCKER_MAP.get(text, text)
        self._sync_tags()
        self._apply_and_refresh()

    def _sync_tags(self):
        """同步活跃筛选标签行。"""
        while self._tags_layout.count() > 1:
            item = self._tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        display_map = {"sprint": "Sprint", "blocker_type": "阻碍"}
        val_map = {"tech": "技术", "resource": "资源", "communication": "沟通", "other": "其他"}

        for key, val in self._filters.items():
            if val is not None:
                label = display_map.get(key, key)
                display_val = val_map.get(val, str(val))
                tag = FilterTag(f"{label}: {display_val}", key)
                tag.remove_clicked.connect(self._on_tag_removed)
                self._tags_layout.insertWidget(self._tags_layout.count() - 1, tag)

    def _on_tag_removed(self, tag_key: str):
        """移除单个筛选标签。"""
        self._filters[tag_key] = None
        if tag_key == "sprint":
            self._sprint_combo.blockSignals(True)
            self._sprint_combo.setCurrentText("全部")
            self._sprint_combo.blockSignals(False)
        elif tag_key == "blocker_type":
            self._blocker_combo.blockSignals(True)
            self._blocker_combo.setCurrentText("全部")
            self._blocker_combo.blockSignals(False)
        self._sync_tags()
        self._apply_and_refresh()

    # ── 数据刷新 ──
    def _apply_and_refresh(self):
        """从 API 直接加载所有 Dashboard 数据。"""
        if not self._team_id or not self.api_client:
            return

        c = self.api_client

        # Summary
        summary = c.get_dashboard_summary(self._team_id) or {}

        # Trends
        att_trend = c.get_dashboard_trend(self._team_id, "attendance") or []
        comp_trend = c.get_dashboard_trend(self._team_id, "completion") or []

        # Blocker distribution
        blocker_dist = c.get_dashboard_trend(self._team_id, "blocker") or []

        # Member ranking
        ranking = c.get_member_ranking(self._team_id) or []

        self._refresh_display(summary, att_trend, comp_trend, blocker_dist, ranking)

    def _refresh_display(self, summary: dict, att_trend: list, comp_trend: list,
                         blocker_dist: list, ranking: list):
        """刷新所有 UI 组件。"""
        s = summary

        # StatCards
        self._stat_cards["card_meetings"].update_value(str(s.get("totalMeetings", 0)))
        self._stat_cards["card_meetings"].update_delta(0)

        att_rate = s.get("avgAttendanceRate", 0)
        if isinstance(att_rate, float) and att_rate <= 1:
            att_rate *= 100
        self._stat_cards["card_attendance"].update_value(f"{int(att_rate)}%")
        self._stat_cards["card_attendance"].update_delta(0)

        comp_rate = s.get("completionRate", 0)
        if isinstance(comp_rate, float) and comp_rate <= 1:
            comp_rate *= 100
        self._stat_cards["card_completion"].update_value(f"{int(comp_rate)}%")
        self._stat_cards["card_completion"].update_delta(0)

        self._stat_cards["card_blockers"].update_value(str(s.get("activeBlockers", 0)))
        self._stat_cards["card_blockers"].update_delta(0)

        # 趋势图
        if att_trend:
            self._trend_attendance.set_data([{
                "date": p.get("date", "")[-5:] if len(p.get("date", "")) > 5 else p.get("date", ""),
                "rate": p.get("rate", p.get("attended", 0) / max(p.get("total", 1), 1)) if isinstance(p.get("rate"), (int, float)) else 0
            } for p in att_trend])
        else:
            self._trend_attendance.set_data([])

        if comp_trend:
            self._trend_completion.set_data([{
                "date": p.get("date", "")[-5:] if len(p.get("date", "")) > 5 else p.get("date", ""),
                "rate": p.get("rate", 0) if isinstance(p.get("rate"), (int, float)) else 0
            } for p in comp_trend])
        else:
            self._trend_completion.set_data([])

        # 阻碍分布
        self._blocker_chart.set_data(blocker_dist if blocker_dist else [])

        # 排行表
        self._ranking_table.setRowCount(len(ranking))
        medals = {0: "🥇", 1: "🥈", 2: "🥉"}
        for i, m in enumerate(ranking):
            rank_text = medals.get(i, str(i + 1))
            rank_item = QTableWidgetItem(rank_text)
            rank_item.setTextAlignment(Qt.AlignCenter)
            self._ranking_table.setItem(i, 0, rank_item)

            name = m.get("username") or m.get("userId", "?")
            name_item = QTableWidgetItem(name)
            self._ranking_table.setItem(i, 1, name_item)

            total_item = QTableWidgetItem(str(m.get("totalItems", 0)))
            total_item.setTextAlignment(Qt.AlignCenter)
            self._ranking_table.setItem(i, 2, total_item)

            rate = m.get("completionRate", 0)
            if isinstance(rate, float) and rate <= 1:
                rate *= 100
            rate_item = QTableWidgetItem(f"{int(rate)}%")
            rate_item.setTextAlignment(Qt.AlignCenter)
            self._ranking_table.setItem(i, 3, rate_item)

            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(int(member.get("completion_rate", 0) * 100))
            progress.setTextVisible(False)
            progress.setFixedHeight(12)
            bar_color = "#4A9ED9"
            if i == 0:
                bar_color = "#FFD700"
            elif i == 1:
                bar_color = "#C0C0C0"
            elif i == 2:
                bar_color = "#CD7F32"
            progress.setStyleSheet(f"""
                QProgressBar{{border-radius:6px;border:none;}}
                QProgressBar::chunk{{background-color:{bar_color};border-radius:6px;}}
            """)
            self._ranking_table.setCellWidget(i, 4, progress)


# ── 常量 ──

_BLOCKER_MAP = {"技术": "tech", "资源": "resource", "沟通": "communication", "其他": "other"}


# ── 样式辅助 ──

def _combo_style() -> str:
    return """
        QComboBox {
            border-radius: 4px;
            padding: 6px 10px; font-size: 13px;
        }
        QComboBox::drop-down { border: none; }
    """


def _table_style() -> str:
    return """
        QTableWidget {
            background-color: transparent;
            border: none; font-size: 12px;
        }
        QTableWidget::item { padding: 4px 4px; }
        QHeaderView::section {
            background-color: transparent;
            padding: 4px 4px; border: none;
            font-size: 11px;
        }
    """
