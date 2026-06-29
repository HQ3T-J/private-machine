# views/team_view.py — 团队管理页面
"""团队管理视图：成员表格 + 权限操作 + 邀请码，可独立实例化。"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMenu,
    QApplication,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QBrush, QFont

# 身份颜色映射
ROLE_COLORS = {
    "Tech Lead": "#4A9ED9",
    "Scrum Master": "#52C41A",
    "Developer": "#F5A623",
    "Observer": "#8E8E9E",
}


class TeamView(QWidget):
    """团队管理页面 — 可独立实例化。"""

    title = "团队管理"

    # 信号
    role_changed = Signal(str, str)   # member_id, new_role
    member_removed = Signal(str)      # member_id
    team_dissolved = Signal()

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._members = []
        self._invite_code = "A3F8K2"
        self._current_role = "tech_lead"  # 当前用户角色，用于控制按钮可见性
        self._setup_ui()

    @property
    def current_role(self):
        return self._current_role

    @current_role.setter
    def current_role(self, role: str):
        self._current_role = role
        self._update_dissolve_visibility()

    # ── UI 构建 ──
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # ── 顶部：邀请码 ──
        invite_bar = QHBoxLayout()
        invite_label = QLabel("邀请码：")
        invite_label.setStyleSheet("color: #8E8E9E; font-size: 13px;")

        self._invite_code_label = QLabel(self._invite_code)
        self._invite_code_label.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; "
            "font-size: 20px; font-weight: bold; color: #4A9ED9; "
            "background-color: #16213E; padding: 6px 16px; "
            "border-radius: 4px; border: 1px solid #2A2A4A;"
        )

        self._btn_copy = QPushButton("📋 复制")
        self._btn_copy.setObjectName("btnCopyInvite")
        self._btn_copy.setCursor(Qt.PointingHandCursor)
        self._btn_copy.clicked.connect(self._on_copy_invite)

        invite_bar.addWidget(invite_label)
        invite_bar.addWidget(self._invite_code_label)
        invite_bar.addWidget(self._btn_copy)
        invite_bar.addStretch()
        layout.addLayout(invite_bar)

        # ── 成员表格 ──
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["成员", "身份", "出勤率", "完成率", "操作"]
        )
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self._table.setColumnWidth(1, 120)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self._table.setColumnWidth(2, 80)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self._table.setColumnWidth(3, 80)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self._table.setColumnWidth(4, 100)

        self._table.setStyleSheet("""
            QTableWidget {
                background-color: #1A1A2E;
                alternate-background-color: #1E1E36;
                color: #E0E0E0;
                border: none;
                border-radius: 8px;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px 6px;
                border-bottom: 1px solid #2A2A4A;
            }
            QTableWidget::item:selected {
                background-color: #0F3460;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #16213E;
                color: #8E8E9E;
                padding: 8px 6px;
                border: none;
                border-bottom: 1px solid #2A2A4A;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self._table, 1)

        # ── 底部：解散团队按钮 ──
        bottom_bar = QHBoxLayout()

        self._btn_dissolve = QPushButton("解散团队")
        self._btn_dissolve.setObjectName("btnDissolve")
        self._btn_dissolve.setCursor(Qt.PointingHandCursor)
        self._btn_dissolve.clicked.connect(self._on_dissolve_team)

        bottom_bar.addStretch()
        bottom_bar.addWidget(self._btn_dissolve)
        layout.addLayout(bottom_bar)

        # 初始化可见性
        self._update_dissolve_visibility()

        # ── 样式 ──
        self.setStyleSheet("""
            #btnCopyInvite {
                background-color: #4A9ED9;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: bold;
            }
            #btnCopyInvite:hover {
                background-color: #3A8EC9;
            }
            #btnDissolve {
                background-color: #E74C3C;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: bold;
            }
            #btnDissolve:hover {
                background-color: #C0392B;
            }
            QMenu {
                background-color: #1A1A2E;
                color: #E0E0E0;
                border: 1px solid #2A2A4A;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
            }
            QMenu::item:selected {
                background-color: #0F3460;
            }
        """)

    def _update_dissolve_visibility(self):
        """仅 Tech Lead 可见解散按钮。"""
        if hasattr(self, "_btn_dissolve"):
            self._btn_dissolve.setVisible(
                self._current_role.lower() in ("tech_lead", "techlead")
            )

    # ── 数据加载 ──
    def activate(self):
        """页面激活时刷新数据。"""
        if self.api_client:
            self._invite_code = self.api_client.get_invite_code("1")
            self._members = self.api_client.get_team_members("1")
        else:
            self._invite_code = "A3F8K2"
            self._members = self._get_stub_members()
        self._invite_code_label.setText(self._invite_code)
        self._populate_table()

    def _get_stub_members(self):
        return [
            {"id": "1", "name": "张三", "role": "Tech Lead",
             "attendance": 0.95, "completion": 0.92},
            {"id": "2", "name": "李四", "role": "Scrum Master",
             "attendance": 0.88, "completion": 0.75},
            {"id": "3", "name": "王五", "role": "Developer",
             "attendance": 0.90, "completion": 0.60},
            {"id": "4", "name": "赵六", "role": "Developer",
             "attendance": 0.72, "completion": 0.45},
            {"id": "5", "name": "孙七", "role": "Observer",
             "attendance": 0.50, "completion": 0.30},
        ]

    # ── 表格填充 ──
    def _populate_table(self):
        self._table.setRowCount(len(self._members))
        for row, member in enumerate(self._members):
            # 成员名
            name_item = QTableWidgetItem(member["name"])
            name_font = name_item.font()
            name_font.setBold(True)
            name_item.setFont(name_font)
            self._table.setItem(row, 0, name_item)

            # 身份（带颜色）
            role = member["role"]
            role_item = QTableWidgetItem(role)
            role_item.setTextAlignment(Qt.AlignCenter)
            role_color = ROLE_COLORS.get(role, "#8E8E9E")
            role_item.setForeground(QBrush(QColor(role_color)))
            role_font = role_item.font()
            role_font.setBold(True)
            role_item.setFont(role_font)
            self._table.setItem(row, 1, role_item)

            # 出勤率
            att_text = f"{int(member['attendance'] * 100)}%"
            att_item = QTableWidgetItem(att_text)
            att_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 2, att_item)

            # 完成率
            comp_text = f"{int(member['completion'] * 100)}%"
            comp_item = QTableWidgetItem(comp_text)
            comp_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 3, comp_item)

            # 操作列：可移除的角色显示"移除"按钮
            if role in ("Developer", "Observer"):
                btn_remove = QPushButton("移除")
                btn_remove.setCursor(Qt.PointingHandCursor)
                btn_remove.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #E74C3C;
                        border: 1px solid #E74C3C;
                        border-radius: 3px;
                        padding: 4px 8px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #E74C3C;
                        color: #FFFFFF;
                    }
                """)
                mid = member["id"]
                r = row
                btn_remove.clicked.connect(
                    lambda checked, mid=mid, row=r: self._remove_member(mid, row))
                self._table.setCellWidget(row, 4, btn_remove)
            else:
                placeholder = QTableWidgetItem("—")
                placeholder.setTextAlignment(Qt.AlignCenter)
                placeholder.setFlags(Qt.NoItemFlags)
                self._table.setItem(row, 4, placeholder)

    # ── 操作 ──
    def _on_copy_invite(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self._invite_code)
        self._btn_copy.setText("✓ 已复制")
        self._btn_copy.setStyleSheet("""
            #btnCopyInvite {
                background-color: #52C41A;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: bold;
            }
        """)

    def _remove_member(self, member_id: str, row: int):
        if 0 <= row < len(self._members):
            del self._members[row]
            self._populate_table()
            self.member_removed.emit(member_id)

    def _on_dissolve_team(self):
        self._members.clear()
        self._populate_table()
        self.team_dissolved.emit()

    # ── 右键菜单 ──
    def _on_context_menu(self, pos):
        idx = self._table.indexAt(pos)
        if not idx.isValid():
            return
        row = idx.row()
        if row < 0 or row >= len(self._members):
            return

        member = self._members[row]
        mid = member["id"]
        role = member["role"]

        menu = QMenu(self)

        # 编辑角色
        act_edit_role = QAction("✎ 编辑角色", menu)
        act_edit_role.triggered.connect(lambda: None)  # 占位
        menu.addAction(act_edit_role)

        # 移除成员 (Developer 和 Observer 可移除)
        if role in ("Developer", "Observer"):
            act_remove = QAction("✕ 移除成员", menu)
            act_remove.triggered.connect(
                lambda: self._remove_member(mid, row))
            menu.addAction(act_remove)

        menu.exec(self._table.viewport().mapToGlobal(pos))
