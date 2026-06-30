# views/team_view.py — 团队管理页面
"""团队管理视图：成员表格 + 权限操作 + 邀请码 + 创建/加入团队。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMenu, QApplication, QSizePolicy, QDialog, QLineEdit,
    QFormLayout, QDialogButtonBox, QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QBrush, QFont

ROLE_COLORS = {
    "Tech Lead": "#4A9ED9", "TECH_LEAD": "#4A9ED9",
    "Scrum Master": "#52C41A", "SCRUM_MASTER": "#52C41A",
    "Developer": "#F5A623", "DEVELOPER": "#F5A623",
    "Observer": "#8E8E9E", "OBSERVER": "#8E8E9E",
}


class CreateTeamDialog(QDialog):
    """创建团队对话框"""

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.setWindowTitle("创建新团队")
        self.setFixedSize(340, 150)
        layout = QFormLayout(self)
        layout.setSpacing(12)
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("例如: 核心开发组")
        self._name_input.setMinimumHeight(32)
        layout.addRow("团队名称:", self._name_input)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_create)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

    def _on_create(self):
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入团队名称")
            return
        if self.api_client:
            resp = self.api_client._post("/api/teams", {"name": name})
            if resp and resp.get("code") == 200:
                self.accept()
            else:
                msg = resp.get("message", "服务器无响应") if isinstance(resp, dict) else "无法连接后端"
                QMessageBox.warning(self, "创建失败", msg)
        else:
            QMessageBox.warning(self, "错误", "未连接到服务器")


class JoinTeamDialog(QDialog):
    """加入团队对话框"""

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.setWindowTitle("加入团队")
        self.setFixedSize(340, 150)
        layout = QFormLayout(self)
        layout.setSpacing(12)
        self._code_input = QLineEdit()
        self._code_input.setPlaceholderText("输入6位邀请码")
        self._code_input.setMinimumHeight(32)
        layout.addRow("邀请码:", self._code_input)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_join)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

    def _on_join(self):
        code = self._code_input.text().strip().upper()
        if len(code) < 4:
            QMessageBox.warning(self, "提示", "邀请码格式不正确")
            return
        if self.api_client:
            self.api_client._post("/api/teams/join", {"code": code})
        self.accept()


class TeamView(QWidget):
    """团队管理页面"""

    title = "团队管理"
    role_changed = Signal(str, str)
    member_removed = Signal(str)
    team_dissolved = Signal()

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._members = []
        self._invite_code = None
        self._current_team_id = None
        self._current_role = "tech_lead"
        self._setup_ui()

    @property
    def current_role(self):
        return self._current_role

    @current_role.setter
    def current_role(self, role: str):
        self._current_role = role
        self._update_dissolve_visibility()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # ── 顶部操作栏 ----
        top_bar = QHBoxLayout()
        title_lbl = QLabel("团队管理")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: bold;")
        top_bar.addWidget(title_lbl)
        top_bar.addStretch()

        self._btn_create = QPushButton("+ 创建团队")
        self._btn_create.setStyleSheet("""
            QPushButton { background: #52C41A; color: #FFF; border: none;
                border-radius: 4px; padding: 6px 14px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background: #45A818; }
        """)
        self._btn_create.setCursor(Qt.PointingHandCursor)
        self._btn_create.clicked.connect(self._on_create_team)
        top_bar.addWidget(self._btn_create)

        self._btn_join = QPushButton("加入团队")
        self._btn_join.setStyleSheet("""
            QPushButton { background: #4A90D9; color: #FFF; border: none;
                border-radius: 4px; padding: 6px 14px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background: #5BA0E9; }
        """)
        self._btn_join.setCursor(Qt.PointingHandCursor)
        self._btn_join.clicked.connect(self._on_join_team)
        top_bar.addWidget(self._btn_join)
        layout.addLayout(top_bar)

        # ── 邀请码栏 ----
        invite_bar = QHBoxLayout()
        invite_label = QLabel("邀请码：")
        invite_label.setStyleSheet("font-size: 13px;")
        self._invite_code_label = QLabel("N/A")
        self._invite_code_label.setStyleSheet(
            "font-family: 'Consolas', monospace; font-size: 20px; font-weight: bold; "
            "color: #4A9ED9; padding: 6px 16px; border-radius: 4px;"
        )
        self._btn_copy = QPushButton("复制")
        self._btn_copy.setObjectName("btnCopyInvite")
        self._btn_copy.setCursor(Qt.PointingHandCursor)
        self._btn_copy.clicked.connect(self._on_copy_invite)
        invite_bar.addWidget(invite_label)
        invite_bar.addWidget(self._invite_code_label)
        invite_bar.addWidget(self._btn_copy)
        invite_bar.addStretch()
        layout.addLayout(invite_bar)

        # ── 成员表格 ----
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["成员", "身份", "出勤率", "完成率", "操作"])
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
            QTableWidget { border: none; border-radius: 8px; font-size: 13px; }
            QTableWidget::item { padding: 8px 6px; }
            QHeaderView::section { padding: 8px 6px; border: none; font-size: 12px; font-weight: bold; }
        """)
        layout.addWidget(self._table, 1)

        # ── 底部 ---- 
        bottom_bar = QHBoxLayout()
        self._btn_dissolve = QPushButton("解散团队")
        self._btn_dissolve.setObjectName("btnDissolve")
        self._btn_dissolve.setCursor(Qt.PointingHandCursor)
        self._btn_dissolve.clicked.connect(self._on_dissolve_team)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self._btn_dissolve)
        layout.addLayout(bottom_bar)
        self._update_dissolve_visibility()

        self.setStyleSheet("""
            #btnCopyInvite { background: #4A9ED9; color: #FFF; border: none;
                border-radius: 4px; padding: 8px 14px; font-size: 12px; font-weight: bold; }
            #btnCopyInvite:hover { background: #3A8EC9; }
            #btnDissolve { background: #E74C3C; color: #FFF; border: none;
                border-radius: 4px; padding: 10px 24px; font-size: 13px; font-weight: bold; }
            #btnDissolve:hover { background: #C0392B; }
        """)

    def _update_dissolve_visibility(self):
        if hasattr(self, "_btn_dissolve"):
            self._btn_dissolve.setVisible(
                self._current_role.lower() in ("tech_lead", "techlead")
            )

    def activate(self):
        """页面激活时刷新"""
        if self.api_client:
            teams = self.api_client.get_teams()
            if teams:
                self._current_team_id = teams[0].get("id")
                self._invite_code = self.api_client.get_invite_code(str(self._current_team_id))
                self._members = self.api_client.get_team_members(str(self._current_team_id))
            else:
                self._current_team_id = None
                self._invite_code = None
                self._members = []
        else:
            self._invite_code = None
            self._members = []
        self._invite_code_label.setText(self._invite_code or "N/A")
        self._populate_table()

    def _populate_table(self):
        self._table.setRowCount(len(self._members))
        for row, member in enumerate(self._members):
            # 成员名：name > username > display_name > user_id
            name = (member.get("name") or member.get("username") or
                    member.get("display_name") or member.get("user_id") or "?")
            name_item = QTableWidgetItem(name)
            name_font = name_item.font()
            name_font.setBold(True)
            name_item.setFont(name_font)
            self._table.setItem(row, 0, name_item)

            role = member.get("role", "?")
            role_item = QTableWidgetItem(role)
            role_item.setTextAlignment(Qt.AlignCenter)
            role_color = ROLE_COLORS.get(role, "#8E8E9E")
            role_item.setForeground(QBrush(QColor(role_color)))
            role_font = role_item.font()
            role_font.setBold(True)
            role_item.setFont(role_font)
            self._table.setItem(row, 1, role_item)

            # 出勤率/完成率 来自 Dashboard，团队列表暂不显示
            att_item = QTableWidgetItem("—")
            att_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 2, att_item)

            comp_item = QTableWidgetItem("—")
            comp_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 3, comp_item)

            role_lower = role.lower()
            if role_lower in ("developer", "observer"):
                btn = QPushButton("移除")
                btn.setCursor(Qt.PointingHandCursor)
                btn.setFixedSize(50, 26)
                btn.setStyleSheet("""
                    QPushButton { background: transparent; color: #E74C3C;
                        border: 1px solid #E74C3C; border-radius: 3px; padding: 4px 8px; font-size: 11px; }
                    QPushButton:hover { background: #E74C3C; color: #FFF; }
                """)
                mid = member.get("id") or member.get("user_id")
                r = row
                btn.clicked.connect(lambda checked, mid=mid, row=r: self._remove_member(mid, row))
                self._table.setCellWidget(row, 4, btn)
            else:
                placeholder = QTableWidgetItem("—")
                placeholder.setTextAlignment(Qt.AlignCenter)
                placeholder.setFlags(Qt.NoItemFlags)
                self._table.setItem(row, 4, placeholder)

    def _on_create_team(self):
        dlg = CreateTeamDialog(self.api_client, self)
        if dlg.exec() == QDialog.Accepted:
            self.activate()

    def _on_join_team(self):
        dlg = JoinTeamDialog(self.api_client, self)
        if dlg.exec() == QDialog.Accepted:
            self.activate()

    def _on_copy_invite(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self._invite_code or "")
        self._btn_copy.setText("已复制")
        self._btn_copy.setStyleSheet("""
            #btnCopyInvite { background: #52C41A; color: #FFF; border: none;
                border-radius: 4px; padding: 8px 14px; font-size: 12px; font-weight: bold; }
        """)

    def _remove_member(self, member_id, row):
        if self.api_client and self._current_team_id:
            try:
                import requests
                from api_client import APIClient
                requests.delete(
                    f"{APIClient.base_url()}/api/teams/{self._current_team_id}/members/{member_id}",
                    headers=self.api_client._headers(), timeout=5)
            except Exception:
                pass
        if 0 <= row < len(self._members):
            del self._members[row]
            self._populate_table()
            self.member_removed.emit(str(member_id))

    def _on_dissolve_team(self):
        reply = QMessageBox.question(self, "确认", "确定要解散团队吗？此操作不可撤销。",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        if self.api_client and self._current_team_id:
            try:
                import requests
                from api_client import APIClient
                requests.delete(
                    f"{APIClient.base_url()}/api/teams/{self._current_team_id}",
                    headers=self.api_client._headers(), timeout=5)
            except Exception:
                pass
        self._members.clear()
        self._current_team_id = None
        self._invite_code = None
        self._invite_code_label.setText("N/A")
        self._populate_table()
        self.team_dissolved.emit()

    def _on_context_menu(self, pos):
        idx = self._table.indexAt(pos)
        if not idx.isValid():
            return
        row = idx.row()
        if row < 0 or row >= len(self._members):
            return
        member = self._members[row]
        mid = member.get("id") or member.get("user_id")
        role = member.get("role", "")
        menu = QMenu(self)
        act_edit = QAction("编辑角色", menu)
        act_edit.triggered.connect(lambda: QMessageBox.information(self, "提示", "角色编辑功能即将开放"))
        menu.addAction(act_edit)
        if role.lower() in ("developer", "observer"):
            act_remove = QAction("移除成员", menu)
            act_remove.triggered.connect(lambda: self._remove_member(mid, row))
            menu.addAction(act_remove)
        menu.exec(self._table.viewport().mapToGlobal(pos))
