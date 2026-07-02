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
    QInputDialog,
    QMessageBox,
    QDialog,
    QLineEdit,
    QComboBox,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QColor, QBrush, QFont

ROLE_COLORS = {
    "Tech Lead": "#4A9ED9",
    "Scrum Master": "#52C41A",
    "Developer": "#F5A623",
    "Observer": "#8E8E9E",
}

ROLE_MAP = {
    "tech_lead": "Tech Lead",
    "scrum_master": "Scrum Master",
    "developer": "Developer",
    "observer": "Observer",
}

REVERSE_ROLE_MAP = {v: k for k, v in ROLE_MAP.items()}


class TeamView(QWidget):
    """团队管理页面 — 可独立实例化。"""

    title = "团队管理"

    role_changed = Signal(str, str)   # member_id, new_role
    member_removed = Signal(str)      # member_id
    team_dissolved = Signal()
    team_created = Signal(dict)       # new_team
    team_joined = Signal(dict)        # team

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._members = []
        self._invite_code = self._generate_numeric_code()
        self._current_role = "tech_lead"
        self._current_team_id = "1"
        self._current_team_name = "默认团队"
        self._team_list = [{"id": "1", "name": "默认团队"}]
        self._removed_members = []
        self._setup_ui()
    
    def _generate_numeric_code(self):
        import random
        return ''.join(random.choices('0123456789', k=6))

    @property
    def current_role(self):
        return self._current_role

    @current_role.setter
    def current_role(self, role: str):
        self._current_role = role
        self._update_dissolve_visibility()

    def set_team_id(self, team_id: str):
        self._current_team_id = team_id
        self.activate()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        title_bar = QHBoxLayout()
        
        self._team_combo = QComboBox()
        self._team_combo.addItem(f"🏢 {self._current_team_name}")
        self._team_combo.setStyleSheet("""
            QComboBox {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 4px;
                padding: 4px 8px;
                color: #E0E0E0;
                font-size: 14px;
                font-weight: bold;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self._team_combo.currentIndexChanged.connect(self._on_team_changed)
        title_bar.addWidget(self._team_combo)
        
        title_bar.addStretch()
        layout.addLayout(title_bar)

        invite_frame = QFrame()
        invite_frame.setStyleSheet("""
            QFrame {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 8px;
            }
        """)
        invite_layout = QHBoxLayout(invite_frame)
        invite_layout.setContentsMargins(16, 12, 16, 12)
        invite_layout.setSpacing(16)

        code_section = QVBoxLayout()
        code_section.setSpacing(4)
        
        code_header = QHBoxLayout()
        invite_label = QLabel("🔑 邀请码")
        invite_label.setStyleSheet("color: #8E8E9E; font-size: 13px; font-weight: bold;")
        code_header.addWidget(invite_label)
        code_header.addStretch()
        
        code_actions = QHBoxLayout()
        code_actions.setSpacing(6)
        
        self._btn_copy_code = QPushButton("📋 复制")
        self._btn_copy_code.setObjectName("btnCopyCode")
        self._btn_copy_code.setCursor(Qt.PointingHandCursor)
        self._btn_copy_code.clicked.connect(self._on_copy_invite_code)
        self._btn_copy_code.setStyleSheet("""
            QPushButton {
                background-color: #4A9ED9;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3A8EC9;
            }
        """)
        code_actions.addWidget(self._btn_copy_code)
        
        self._btn_regenerate = QPushButton("🔄 刷新")
        self._btn_regenerate.setObjectName("btnRegenerate")
        self._btn_regenerate.setCursor(Qt.PointingHandCursor)
        self._btn_regenerate.clicked.connect(self._on_regenerate_invite)
        self._btn_regenerate.setStyleSheet("""
            QPushButton {
                background-color: #2A2A4A;
                color: #E0E0E0;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3A3A5A;
            }
        """)
        code_actions.addWidget(self._btn_regenerate)
        
        code_header.addLayout(code_actions)
        code_section.addLayout(code_header)
        
        self._invite_code_label = QLabel(self._invite_code)
        self._invite_code_label.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; "
            "font-size: 28px; font-weight: bold; color: #4A9ED9; "
            "letter-spacing: 4px;"
        )
        self._invite_code_label.setAlignment(Qt.AlignCenter)
        code_section.addWidget(self._invite_code_label)
        
        invite_layout.addLayout(code_section)

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #2A2A4A;")
        invite_layout.addWidget(separator)

        link_section = QVBoxLayout()
        link_section.setSpacing(4)
        
        link_label = QLabel("🔗 邀请链接")
        link_label.setStyleSheet("color: #8E8E9E; font-size: 13px; font-weight: bold;")
        link_section.addWidget(link_label)
        
        self._invite_link_label = QLabel(self._generate_invite_link())
        self._invite_link_label.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; "
            "font-size: 12px; color: #52C41A; "
            "background-color: #0D1117; padding: 6px 10px; "
            "border-radius: 4px; border: 1px solid #2A2A4A;"
        )
        self._invite_link_label.setToolTip("点击复制邀请链接")
        self._invite_link_label.setCursor(Qt.PointingHandCursor)
        self._invite_link_label.mousePressEvent = lambda e: self._on_copy_invite_link()
        link_section.addWidget(self._invite_link_label)
        
        self._btn_copy_link = QPushButton("📋 复制链接")
        self._btn_copy_link.setObjectName("btnCopyLink")
        self._btn_copy_link.setCursor(Qt.PointingHandCursor)
        self._btn_copy_link.clicked.connect(self._on_copy_invite_link)
        self._btn_copy_link.setStyleSheet("""
            QPushButton {
                background-color: #52C41A;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #43A017;
            }
        """)
        link_section.addWidget(self._btn_copy_link)
        
        invite_layout.addLayout(link_section)

        invite_layout.addStretch()
        layout.addWidget(invite_frame)

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

        bottom_bar = QHBoxLayout()

        self._btn_create_team = QPushButton("+ 创建团队")
        self._btn_create_team.setObjectName("btnCreateTeam")
        self._btn_create_team.setCursor(Qt.PointingHandCursor)
        self._btn_create_team.clicked.connect(self._on_create_team)

        self._btn_join_team = QPushButton("加入团队")
        self._btn_join_team.setObjectName("btnJoinTeam")
        self._btn_join_team.setCursor(Qt.PointingHandCursor)
        self._btn_join_team.clicked.connect(self._on_join_team)

        self._btn_dissolve = QPushButton("解散团队")
        self._btn_dissolve.setObjectName("btnDissolve")
        self._btn_dissolve.setCursor(Qt.PointingHandCursor)
        self._btn_dissolve.clicked.connect(self._on_dissolve_team)

        bottom_bar.addWidget(self._btn_create_team)
        bottom_bar.addWidget(self._btn_join_team)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self._btn_dissolve)
        layout.addLayout(bottom_bar)

        self._update_dissolve_visibility()

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
            #btnRegenerate {
                background-color: #16213E;
                color: #8E8E9E;
                border: 1px solid #2A2A4A;
                border-radius: 4px;
                padding: 8px 14px;
                font-size: 12px;
            }
            #btnRegenerate:hover {
                background-color: #1E1E36;
                color: #E0E0E0;
            }
            #btnCopyCode {
                background-color: #4A9ED9;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: bold;
            }
            #btnCopyCode:hover {
                background-color: #3A8EC9;
            }
            #btnCopyLink {
                background-color: #52C41A;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: bold;
            }
            #btnCopyLink:hover {
                background-color: #43A017;
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
        if hasattr(self, "_btn_dissolve"):
            self._btn_dissolve.setVisible(
                self._current_role.lower() in ("tech_lead", "techlead")
            )

    def activate(self):
        if self.api_client:
            try:
                self._load_teams()
                code = self.api_client.get_invite_code(self._current_team_id)
                self._invite_code = self._ensure_numeric_code(code)
                self._members = self.api_client.get_team_members(self._current_team_id)
            except Exception as e:
                print(f"Failed to load team data: {e}")
                self._invite_code = self._generate_numeric_code()
                self._members = self._get_stub_members()
        else:
            self._invite_code = self._generate_numeric_code()
            self._members = self._get_stub_members()
        self._invite_code_label.setText(self._invite_code)
        self._invite_link_label.setText(self._generate_invite_link())
        self._populate_table()

    def _ensure_numeric_code(self, code):
        if code and len(code) == 6 and code.isdigit():
            return code
        return self._generate_numeric_code()

    def _load_teams(self):
        try:
            teams = self.api_client.get_teams()
            if teams:
                self._team_list = [{"id": t.get("id"), "name": t.get("name")} for t in teams]
                self._update_team_combo()
                if self._current_team_id not in [t["id"] for t in self._team_list]:
                    if self._team_list:
                        self._current_team_id = self._team_list[0]["id"]
                        self._current_team_name = self._team_list[0]["name"]
        except Exception as e:
            print(f"Failed to load teams: {e}")

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

    def _populate_table(self):
        self._table.setRowCount(len(self._members))
        for row, member in enumerate(self._members):
            name_item = QTableWidgetItem(member["name"])
            name_font = name_item.font()
            name_font.setBold(True)
            name_item.setFont(name_font)
            self._table.setItem(row, 0, name_item)

            role = member["role"]
            role_item = QTableWidgetItem(role)
            role_item.setTextAlignment(Qt.AlignCenter)
            role_color = ROLE_COLORS.get(role, "#8E8E9E")
            role_item.setForeground(QBrush(QColor(role_color)))
            role_font = role_item.font()
            role_font.setBold(True)
            role_item.setFont(role_font)
            self._table.setItem(row, 1, role_item)

            att_text = f"{int(member.get('attendance', 0) * 100)}%"
            att_item = QTableWidgetItem(att_text)
            att_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 2, att_item)

            comp_text = f"{int(member.get('completion', 0) * 100)}%"
            comp_item = QTableWidgetItem(comp_text)
            comp_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 3, comp_item)

            can_remove = self._current_role.lower() in ("tech_lead", "techlead")
            
            if can_remove:
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

    def _generate_invite_link(self):
        return f"standup://join?code={self._invite_code}"

    def _on_copy_invite_code(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self._invite_code)
        
        self._btn_copy_code.setText("✓ 已复制")
        self._btn_copy_code.setStyleSheet("""
            QPushButton {
                background-color: #52C41A;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        
        QTimer.singleShot(2000, lambda: self._restore_copy_code_btn())

    def _restore_copy_code_btn(self):
        self._btn_copy_code.setText("📋 复制")
        self._btn_copy_code.setStyleSheet("""
            QPushButton {
                background-color: #4A9ED9;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3A8EC9;
            }
        """)

    def _on_copy_invite_link(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self._generate_invite_link())
        
        self._btn_copy_link.setText("✓ 已复制")
        self._btn_copy_link.setStyleSheet("""
            QPushButton {
                background-color: #52C41A;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        
        QTimer.singleShot(2000, lambda: self._restore_copy_link_btn())

    def _restore_copy_link_btn(self):
        self._btn_copy_link.setText("📋 复制链接")
        self._btn_copy_link.setStyleSheet("""
            QPushButton {
                background-color: #52C41A;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #43A017;
            }
        """)

    def _on_regenerate_invite(self):
        if self.api_client:
            try:
                new_code = self.api_client.regenerate_invite_code(self._current_team_id)
                self._invite_code = new_code
                self._invite_code_label.setText(new_code)
                self._invite_link_label.setText(self._generate_invite_link())
                QMessageBox.information(self, "成功", "邀请码和邀请链接已刷新")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"刷新邀请码失败: {str(e)}")
        else:
            import random
            new_code = ''.join(random.choices('0123456789', k=6))
            self._invite_code = new_code
            self._invite_code_label.setText(new_code)
            self._invite_link_label.setText(self._generate_invite_link())
            QMessageBox.information(self, "成功", "邀请码和邀请链接已刷新（模拟）")

    def _remove_member(self, member_id: str, row: int):
        if self.api_client:
            try:
                result = self.api_client.remove_member(self._current_team_id, member_id)
                if result.get("success"):
                    if 0 <= row < len(self._members):
                        removed_member = self._members[row]
                        self._removed_members.append(removed_member)
                        del self._members[row]
                        self._populate_table()
                        self.member_removed.emit(member_id)
                        QMessageBox.information(self, "成功", "成员已移除，记录保留为只读")
                else:
                    QMessageBox.warning(self, "失败", result.get("error", "移除失败"))
            except Exception as e:
                QMessageBox.warning(self, "失败", f"移除成员失败: {str(e)}")
        else:
            if 0 <= row < len(self._members):
                removed_member = self._members[row]
                self._removed_members.append(removed_member)
                del self._members[row]
                self._populate_table()
                self.member_removed.emit(member_id)
                QMessageBox.information(self, "成功", "成员已移除，记录保留为只读")

    def _on_dissolve_team(self):
        reply = QMessageBox.question(
            self, "确认解散", 
            "⚠️ 确定要解散团队「{}」吗？\n\n此操作将级联删除：\n• 所有站会记录\n• 所有待办事项\n• 所有成员关联数据\n\n此操作不可撤销！".format(self._current_team_name),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.api_client:
                try:
                    result = self.api_client.delete_team(self._current_team_id)
                    if result.get("success"):
                        self._members.clear()
                        self._populate_table()
                        self._current_team_id = "1"
                        self._current_team_name = "默认团队"
                        self._team_combo.clear()
                        self._team_combo.addItem(f"🏢 {self._current_team_name}")
                        self._invite_code_label.setText("A3F8K2")
                        self.team_dissolved.emit()
                        QMessageBox.information(self, "成功", "团队已解散，所有相关数据已清除")
                    else:
                        QMessageBox.warning(self, "失败", result.get("error", "解散失败"))
                except Exception as e:
                    QMessageBox.warning(self, "失败", f"解散团队失败: {str(e)}")
            else:
                self._members.clear()
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
        mid = member["id"]
        role = member["role"]

        menu = QMenu(self)

        act_edit_role = QAction("✎ 编辑角色", menu)
        act_edit_role.triggered.connect(lambda: self._edit_role(mid, role, row))
        menu.addAction(act_edit_role)

        if role in ("Developer", "Observer"):
            act_remove = QAction("✕ 移除成员", menu)
            act_remove.triggered.connect(
                lambda: self._remove_member(mid, row))
            menu.addAction(act_remove)

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _edit_role(self, member_id: str, current_role: str, row: int):
        roles = ["Tech Lead", "Scrum Master", "Developer", "Observer"]
        roles.remove(current_role)
        
        selected_role, ok = QInputDialog.getItem(
            self, "编辑角色", "选择新角色:", roles, 0, False
        )
        
        if ok and selected_role:
            if self.api_client:
                try:
                    role_key = REVERSE_ROLE_MAP.get(selected_role, selected_role.lower().replace(" ", "_"))
                    result = self.api_client.update_member_role(self._current_team_id, member_id, role_key)
                    if result.get("success"):
                        self._members[row]["role"] = selected_role
                        self._populate_table()
                        self.role_changed.emit(member_id, selected_role)
                        QMessageBox.information(self, "成功", "角色已更新")
                    else:
                        QMessageBox.warning(self, "失败", result.get("error", "更新失败"))
                except Exception as e:
                    QMessageBox.warning(self, "失败", f"更新角色失败: {str(e)}")
            else:
                self._members[row]["role"] = selected_role
                self._populate_table()
                self.role_changed.emit(member_id, selected_role)

    def _on_create_team(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("创建团队")
        dialog.setFixedSize(380, 220)
        dialog.setStyleSheet("""
            QDialog { background-color: #1A1A2E; }
            QLabel { color: #E0E0E0; font-size: 13px; }
            QLineEdit {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 4px;
                padding: 6px;
                color: #E0E0E0;
                font-size: 13px;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(QLabel("团队名称:"))
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("输入团队名称")
        layout.addWidget(name_edit)

        layout.addWidget(QLabel("团队描述（可选）:"))
        desc_edit = QLineEdit()
        desc_edit.setPlaceholderText("简短描述团队用途")
        layout.addWidget(desc_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.close)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #16213E;
                color: #8E8E9E;
                border: 1px solid #2A2A4A;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 13px;
            }
        """)
        btn_layout.addWidget(cancel_btn)

        create_btn = QPushButton("创建")
        create_btn.clicked.connect(lambda: self._create_team(dialog, name_edit.text(), desc_edit.text()))
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90D9;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #5BA0E9; }
        """)
        btn_layout.addWidget(create_btn)
        layout.addLayout(btn_layout)

        dialog.exec()

    def _create_team(self, dialog, name, description):
        if not name.strip():
            QMessageBox.warning(self, "警告", "请输入团队名称")
            return

        if self.api_client:
            try:
                result = self.api_client.create_team(name, description)
                if result.get("success"):
                    team_data = result.get("team", {})
                    self._current_team_id = team_data.get("id", "1")
                    self._current_team_name = team_data.get("name", name)
                    self._current_role = "tech_lead"
                    self._team_list.append({"id": self._current_team_id, "name": self._current_team_name})
                    self._update_team_combo()
                    QMessageBox.information(self, "成功", "团队创建成功，您已成为Tech Lead")
                    dialog.close()
                    self.team_created.emit(team_data)
                    self.activate()
                else:
                    QMessageBox.warning(self, "失败", result.get("error", "创建失败"))
            except Exception as e:
                QMessageBox.warning(self, "失败", f"创建团队失败: {str(e)}")
        else:
            new_team_id = f"team_{len(self._team_list) + 1}"
            self._team_list.append({"id": new_team_id, "name": name})
            self._current_team_id = new_team_id
            self._current_team_name = name
            self._current_role = "tech_lead"
            self._update_team_combo()
            QMessageBox.information(self, "成功", "团队创建成功，您已成为Tech Lead（模拟）")
            dialog.close()
            self.team_created.emit({"id": new_team_id, "name": name})
            self.activate()

    def _update_team_combo(self):
        current_text = self._team_combo.currentText()
        self._team_combo.clear()
        for team in self._team_list:
            self._team_combo.addItem(f"🏢 {team['name']}", team["id"])
        
        index = self._team_combo.findText(current_text)
        if index >= 0:
            self._team_combo.setCurrentIndex(index)

    def _on_team_changed(self, index):
        team_id = self._team_combo.itemData(index)
        if team_id:
            self._current_team_id = team_id
            team = next((t for t in self._team_list if t["id"] == team_id), None)
            if team:
                self._current_team_name = team["name"]
            self.activate()

    def _on_join_team(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("加入团队")
        dialog.setFixedSize(380, 180)
        dialog.setStyleSheet("""
            QDialog { background-color: #1A1A2E; }
            QLabel { color: #E0E0E0; font-size: 13px; }
            QLineEdit {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 4px;
                padding: 6px;
                color: #E0E0E0;
                font-size: 13px;
                font-family: 'Consolas', monospace;
                letter-spacing: 2px;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(QLabel("邀请码:"))
        code_edit = QLineEdit()
        code_edit.setPlaceholderText("输入6位邀请码")
        code_edit.setMaxLength(6)
        layout.addWidget(code_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.close)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #16213E;
                color: #8E8E9E;
                border: 1px solid #2A2A4A;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 13px;
            }
        """)
        btn_layout.addWidget(cancel_btn)

        join_btn = QPushButton("加入")
        join_btn.clicked.connect(lambda: self._join_team(dialog, code_edit.text()))
        join_btn.setStyleSheet("""
            QPushButton {
                background-color: #52C41A;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #43A017; }
        """)
        btn_layout.addWidget(join_btn)
        layout.addLayout(btn_layout)

        dialog.exec()

    def _join_team(self, dialog, invite_code):
        code = invite_code.strip()
        
        if not code:
            QMessageBox.warning(self, "警告", "请输入邀请码")
            return
        
        if len(code) != 6 or not code.isdigit():
            QMessageBox.warning(self, "警告", "请输入6位数字邀请码")
            return

        if self.api_client:
            try:
                result = self.api_client.join_team(code)
                if result.get("success"):
                    team_data = result.get("team", {})
                    self._current_team_id = team_data.get("id", "1")
                    self._current_team_name = team_data.get("name", "默认团队")
                    QMessageBox.information(self, "成功", f"已成功加入团队「{self._current_team_name}」")
                    dialog.close()
                    self.activate()
                    self.team_joined.emit(team_data)
                else:
                    QMessageBox.warning(self, "失败", result.get("error", "邀请码无效"))
            except Exception as e:
                QMessageBox.warning(self, "失败", f"加入团队失败: {str(e)}")
        else:
            if code == self._invite_code:
                QMessageBox.information(self, "成功", f"已成功加入团队「{self._current_team_name}」（模拟）")
                dialog.close()
                self.activate()
            else:
                QMessageBox.warning(self, "失败", "邀请码无效")
