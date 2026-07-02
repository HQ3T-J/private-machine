# views/dashboard_view.py — 数据看板页面
"""数据看板视图：统计卡片 + 趋势占位 + 排行榜，可独立实例化。"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QProgressBar,
    QSizePolicy,
    QGridLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

# 尝试从 widgets 导入 StatCard，如果不存在则使用本地实现
try:
    from widgets import StatCard
except ImportError:
    class StatCard(QFrame):
        """简易统计卡片，当 widgets.StatCard 不可用时使用。"""

        def __init__(self, title: str, value: str, subtitle: str = "",
                     color: str = "#4A9ED9", parent=None):
            super().__init__(parent)
            self.setObjectName("StatCard")
            self.setFixedSize(200, 100)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 12, 16, 12)
            layout.setSpacing(4)

            title_lbl = QLabel(title)
            title_lbl.setStyleSheet("color: #8E8E9E; font-size: 12px;")
            layout.addWidget(title_lbl)

            value_lbl = QLabel(str(value))
            value_lbl.setStyleSheet(
                f"color: {color}; font-size: 28px; font-weight: bold;"
            )
            layout.addWidget(value_lbl)

            if subtitle:
                sub = QLabel(subtitle)
                sub.setStyleSheet("color: #6E6E8E; font-size: 11px;")
                layout.addWidget(sub)

            layout.addStretch()

            self.setStyleSheet(f"""
                #StatCard {{
                    background-color: #16213E;
                    border-radius: 8px;
                    border-left: 3px solid {color};
                }}
            """)


class TrendPlaceholder(QFrame):
    """趋势图占位区域，显示简单文字折线示意。"""

    def __init__(self, title: str, data: list[dict] = None, color: str = "#4A9ED9",
                 parent=None):
        super().__init__(parent)
        self.setObjectName("TrendPlaceholder")
        self.setMinimumSize(340, 180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # 标题
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #8E8E9E; font-size: 12px; font-weight: bold;")
        layout.addWidget(title_lbl)

        # 简易文字折线
        if data:
            # 构建 ━━ 风格折线
            points = "  ".join(
                f"<span style='color:{color};font-size:18px;'>{'●'}</span>"
                f"<span style='color:#6E6E8E;font-size:9px;'>{d['date']}</span>"
                for d in data
            )
            line_text = QLabel(points)
            line_text.setWordWrap(True)
            line_text.setStyleSheet("padding: 8px 0px;")
            layout.addWidget(line_text)

            # 数值行
            vals = "  ".join(
                f"<span style='color:{color};font-size:14px;font-weight:bold;'>"
                f"{int(d['rate']*100)}%</span>"
                for d in data
            )
            val_text = QLabel(vals)
            val_text.setStyleSheet("padding: 0px 4px;")
            layout.addWidget(val_text)

            # 趋势线模拟
            trend_frame = QFrame()
            trend_frame.setFixedHeight(48)
            trend_layout = QHBoxLayout(trend_frame)
            trend_layout.setContentsMargins(4, 4, 4, 4)
            trend_layout.setSpacing(0)

            if len(data) >= 2:
                max_rate = max(d["rate"] for d in data)
                min_rate = min(d["rate"] for d in data)
                rate_range = max_rate - min_rate or 0.01
                for d in data:
                    bar = QFrame()
                    height_pct = (d["rate"] - min_rate) / rate_range
                    bar_height = int(12 + height_pct * 36)
                    bar.setFixedSize(40, bar_height)
                    bar.setStyleSheet(
                        f"background-color: {color}; border-radius: 2px; "
                        f"margin-top: {48 - bar_height}px;"
                    )
                    trend_layout.addWidget(bar, 0, Qt.AlignBottom)
            layout.addWidget(trend_frame)
        else:
            empty = QLabel("加载中...")
            empty.setStyleSheet("color: #6E6E8E; font-size: 13px;")
            empty.setAlignment(Qt.AlignCenter)
            layout.addWidget(empty, 1)

        layout.addStretch()

        self.setStyleSheet("""
            #TrendPlaceholder {
                background-color: #16213E;
                border-radius: 8px;
                border: 1px solid #2A2A4A;
            }
        """)


class DashboardView(QWidget):
    """数据看板页面 — 可独立实例化。"""

    title = "数据看板"

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._summary = {}
        self._trend = []
        self._ranking = []
        self._setup_ui()

    # ── UI 构建 ──
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # ── 顶部：Sprint 选择器 ──
        top_bar = QHBoxLayout()
        sprint_label = QLabel("Sprint：")
        sprint_label.setStyleSheet("color: #8E8E9E; font-size: 13px;")
        self._sprint_combo = QComboBox()
        self._sprint_combo.addItems([
            "Sprint #12 (当前)",
            "Sprint #11",
            "Sprint #10",
            "Sprint #9",
        ])
        self._sprint_combo.setFixedWidth(180)
        self._sprint_combo.setStyleSheet("""
            QComboBox {
                background-color: #16213E;
                color: #E0E0E0;
                border: 1px solid #2A2A4A;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1A1A2E;
                color: #E0E0E0;
                selection-background-color: #0F3460;
            }
        """)
        top_bar.addWidget(sprint_label)
        top_bar.addWidget(self._sprint_combo)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # ── 第一行：4 个 StatCard ──
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        self._stat_cards = {}
        stat_configs = [
            ("card_meetings", "站会次数", "12", "次", "#4A9ED9"),
            ("card_attendance", "出勤率", "87%", "", "#52C41A"),
            ("card_completion", "完成率", "73%", "", "#F5A623"),
            ("card_blockers", "活跃阻碍", "3", "个", "#E74C3C"),
        ]
        for key, title, value, sub, color in stat_configs:
            card = StatCard(title, value, sub, color)
            self._stat_cards[key] = card
            stats_row.addWidget(card)
        stats_row.addStretch()
        layout.addLayout(stats_row)

        # ── 第二行：趋势占位 ──
        trend_row = QHBoxLayout()
        trend_row.setSpacing(16)

        self._trend_attendance = TrendPlaceholder(
            "出勤率趋势",
            [
                {"date": "06-01", "rate": 0.80},
                {"date": "06-03", "rate": 0.85},
                {"date": "06-05", "rate": 0.90},
                {"date": "06-07", "rate": 0.82},
                {"date": "06-09", "rate": 0.88},
                {"date": "06-11", "rate": 0.91},
                {"date": "06-13", "rate": 0.87},
            ],
            color="#52C41A",
        )
        self._trend_completion = TrendPlaceholder(
            "完成率趋势",
            [
                {"date": "06-01", "rate": 0.60},
                {"date": "06-03", "rate": 0.65},
                {"date": "06-05", "rate": 0.73},
                {"date": "06-07", "rate": 0.78},
                {"date": "06-09", "rate": 0.82},
                {"date": "06-11", "rate": 0.70},
                {"date": "06-13", "rate": 0.88},
            ],
            color="#F5A623",
        )
        trend_row.addWidget(self._trend_attendance)
        trend_row.addWidget(self._trend_completion)
        trend_row.addStretch()
        layout.addLayout(trend_row)

        # ── 第三行：阻碍分布 + 个人排行 ──
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        # 阻碍类型分布占位
        blocker_frame = QFrame()
        blocker_frame.setObjectName("BlockerPlaceholder")
        blocker_frame.setMinimumSize(340, 220)
        blocker_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        blocker_frame.setFixedHeight(220)
        blocker_layout = QVBoxLayout(blocker_frame)
        blocker_layout.setContentsMargins(12, 10, 12, 10)

        blocker_title = QLabel("阻碍类型分布")
        blocker_title.setStyleSheet(
            "color: #8E8E9E; font-size: 12px; font-weight: bold;"
        )
        blocker_layout.addWidget(blocker_title)

        blocker_items = [
            ("技术债务", 40, "#E74C3C"),
            ("依赖阻塞", 30, "#F5A623"),
            ("需求不清", 20, "#4A9ED9"),
            ("其他", 10, "#52C41A"),
        ]
        for name, pct, color in blocker_items:
            item_layout = QHBoxLayout()
            lbl_name = QLabel(name)
            lbl_name.setFixedWidth(70)
            lbl_name.setStyleSheet("color: #C0C0D0; font-size: 12px;")
            item_layout.addWidget(lbl_name)

            bar_bg = QFrame()
            bar_bg.setFixedHeight(14)
            bar_bg.setStyleSheet(
                "background-color: #1A1A2E; border-radius: 7px;"
            )
            bar_bg_layout = QHBoxLayout(bar_bg)
            bar_bg_layout.setContentsMargins(0, 0, 0, 0)
            bar_fill = QFrame()
            bar_fill.setFixedSize(int(pct * 2), 14)
            bar_fill.setStyleSheet(
                f"background-color: {color}; border-radius: 7px;"
            )
            bar_bg_layout.addWidget(bar_fill)
            bar_bg_layout.addStretch()
            item_layout.addWidget(bar_bg, 1)

            lbl_pct = QLabel(f"{pct}%")
            lbl_pct.setFixedWidth(40)
            lbl_pct.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl_pct.setStyleSheet("color: #8E8E9E; font-size: 12px;")
            item_layout.addWidget(lbl_pct)

            blocker_layout.addLayout(item_layout)

        blocker_layout.addStretch()
        blocker_frame.setStyleSheet("""
            #BlockerPlaceholder {
                background-color: #16213E;
                border-radius: 8px;
                border: 1px solid #2A2A4A;
            }
        """)
        bottom_row.addWidget(blocker_frame)

        # 个人完成排行表格
        rank_frame = QFrame()
        rank_frame.setObjectName("RankPlaceholder")
        rank_frame.setMinimumSize(340, 220)
        rank_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        rank_frame.setFixedHeight(220)
        rank_layout = QVBoxLayout(rank_frame)
        rank_layout.setContentsMargins(12, 10, 12, 10)

        rank_title = QLabel("个人完成排行")
        rank_title.setStyleSheet(
            "color: #8E8E9E; font-size: 12px; font-weight: bold;"
        )
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

        self._ranking_table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                color: #E0E0E0;
                border: none;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 4px 4px;
            }
            QHeaderView::section {
                background-color: transparent;
                color: #8E8E9E;
                padding: 4px 4px;
                border: none;
                border-bottom: 1px solid #2A2A4A;
                font-size: 11px;
            }
        """)
        rank_layout.addWidget(self._ranking_table)

        rank_frame.setStyleSheet("""
            #RankPlaceholder {
                background-color: #16213E;
                border-radius: 8px;
                border: 1px solid #2A2A4A;
            }
        """)
        bottom_row.addWidget(rank_frame)

        layout.addLayout(bottom_row)
        layout.addStretch()

    # ── 数据加载 ──
    def activate(self):
        """页面激活时刷新数据。"""
        if self.api_client:
            self._summary = self.api_client.get_dashboard_summary("1")
            self._trend = self.api_client.get_dashboard_trend("1")
            self._ranking = self.api_client.get_member_ranking("1")
        else:
            self._summary = self._get_stub_summary()
            self._trend = self._get_stub_trend()
            self._ranking = self._get_stub_ranking()
        self._refresh_display()

    def _get_stub_summary(self):
        return {
            "total_meetings": 12,
            "avg_attendance": 0.87,
            "completion_rate": 0.73,
            "active_blockers": 3,
        }

    def _get_stub_trend(self):
        return [
            {"date": "06-01", "rate": 0.80},
            {"date": "06-03", "rate": 0.85},
            {"date": "06-05", "rate": 0.90},
            {"date": "06-07", "rate": 0.82},
            {"date": "06-09", "rate": 0.88},
            {"date": "06-11", "rate": 0.91},
            {"date": "06-13", "rate": 0.87},
        ]

    def _get_stub_ranking(self):
        return [
            {"name": "张三", "total": 12, "rate": 0.92},
            {"name": "李四", "total": 8, "rate": 0.75},
            {"name": "王五", "total": 15, "rate": 0.60},
            {"name": "赵六", "total": 5, "rate": 0.45},
            {"name": "孙七", "total": 3, "rate": 0.30},
        ]

    def _refresh_display(self):
        """根据数据刷新显示。"""
        if self._summary:
            self._stat_cards["card_meetings"].findChildren(QLabel)[1].setText(
                str(self._summary.get("total_meetings", "—"))
            )
            self._stat_cards["card_attendance"].findChildren(QLabel)[1].setText(
                f"{int(self._summary.get('avg_attendance', 0) * 100)}%"
            )
            self._stat_cards["card_completion"].findChildren(QLabel)[1].setText(
                f"{int(self._summary.get('completion_rate', 0) * 100)}%"
            )
            self._stat_cards["card_blockers"].findChildren(QLabel)[1].setText(
                str(self._summary.get("active_blockers", "—"))
            )

        if self._ranking:
            self._ranking_table.setRowCount(len(self._ranking))
            for i, member in enumerate(self._ranking):
                # 排名
                rank_item = QTableWidgetItem(str(i + 1))
                rank_item.setTextAlignment(Qt.AlignCenter)
                self._ranking_table.setItem(i, 0, rank_item)

                # 姓名
                self._ranking_table.setItem(
                    i, 1, QTableWidgetItem(member["name"])
                )

                # 待办数
                total_item = QTableWidgetItem(str(member["total"]))
                total_item.setTextAlignment(Qt.AlignCenter)
                self._ranking_table.setItem(i, 2, total_item)

                # 完成率
                rate_text = f"{int(member['rate'] * 100)}%"
                rate_item = QTableWidgetItem(rate_text)
                rate_item.setTextAlignment(Qt.AlignCenter)
                self._ranking_table.setItem(i, 3, rate_item)

                # 进度条
                progress = QProgressBar()
                progress.setRange(0, 100)
                progress.setValue(int(member["rate"] * 100))
                progress.setTextVisible(False)
                progress.setFixedHeight(12)
                progress.setStyleSheet(f"""
                    QProgressBar {{
                        background-color: #1A1A2E;
                        border-radius: 6px;
                        border: none;
                    }}
                    QProgressBar::chunk {{
                        background-color: #4A9ED9;
                        border-radius: 6px;
                    }}
                """)
                self._ranking_table.setCellWidget(i, 4, progress)
