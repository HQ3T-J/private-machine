"""团队管理 V4 — 团队切换器 + 申请状态 + 审批面板 + 角色管理"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QLineEdit, QFormLayout, QDialogButtonBox,
    QMessageBox, QMenu, QComboBox, QSplitter,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush

ROLE_COLORS = {"TECH_LEAD":"#FFD700","SCRUM_MASTER":"#4A90D9","DEVELOPER":"#8E8E9E","OBSERVER":"#7B7B7B"}
ROLE_LABELS = {"TECH_LEAD":"技术主管","SCRUM_MASTER":"Scrum Master","DEVELOPER":"执行人员","OBSERVER":"观察者"}


class CreateTeamDialog(QDialog):
    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.setWindowTitle("创建团队"); self.setFixedSize(320, 120)
        layout = QFormLayout(self)
        self._name = QLineEdit(); self._name.setPlaceholderText("输入团队名称")
        layout.addRow("名称:", self._name)
        btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn.accepted.connect(self._on_create); btn.rejected.connect(self.reject)
        layout.addRow(btn)

    def _on_create(self):
        name = self._name.text().strip()
        if not name: QMessageBox.warning(self, "提示", "请输入团队名称"); return
        if self.api_client:
            r = self.api_client._post("/api/teams", {"name": name})
            if r and r.get("code") == 200: self.accept(); return
        QMessageBox.warning(self, "错误", "创建失败，请检查后端连接")
        self.accept()


class JoinTeamDialog(QDialog):
    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.setWindowTitle("加入团队"); self.setFixedSize(320, 120)
        layout = QFormLayout(self)
        self._code = QLineEdit(); self._code.setPlaceholderText("输入6位邀请码")
        layout.addRow("邀请码:", self._code)
        btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn.accepted.connect(self._on_join); btn.rejected.connect(self.reject)
        layout.addRow(btn)

    def _on_join(self):
        code = self._code.text().strip()
        if not code: return
        if self.api_client:
            r = self.api_client.apply_to_join(code)
            if r and r.get("code") == 200:
                QMessageBox.information(self, "提示", r.get("message", "申请已提交，等待团长审核"))
                self.accept(); return
            msg = r.get("message", "失败") if r else "后端无响应"
            QMessageBox.warning(self, "提示", msg)
        self.accept()


class TeamView(QWidget):
    title = "团队管理"
    member_removed = Signal(str)
    team_dissolved = Signal()

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._teams = []
        self._current_team_id = None
        self._members = []
        self._invite_code = None
        self._current_role = None
        self._my_application = None
        self._setup_ui()

    def activate(self):
        self._load_teams()
        self._load_data()
        if self._current_team_id:
            self._load_applications()

    def _load_teams(self):
        """加载团队列表到下拉框"""
        self._teams = self.api_client.get_teams() if self.api_client else []
        cur = self._combo.currentText()
        self._combo.blockSignals(True)
        self._combo.clear()
        for t in self._teams:
            self._combo.addItem(t.get("name", f"Team {t['id']}"), t.get("id"))
        if self._teams:
            idx = self._combo.findText(cur)
            self._combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._combo.blockSignals(False)

    def _load_data(self):
        if not self.api_client or not self._teams:
            self._clear_ui(); return
        self._current_team_id = self._combo.currentData()
        if not self._current_team_id and self._teams:
            self._current_team_id = self._teams[0].get("id")

        team_data = self.api_client._get(f"/api/teams/{self._current_team_id}")
        if not team_data:
            self._clear_ui(); return
        self._members = team_data.get("members", [])
        team = team_data.get("team", {})
        self._invite_code = team.get("inviteCode", "N/A")
        self._team_name_label.setText(team.get("name", ""))
        self._invite_label.setText(f"📋 {self._invite_code}")

        # 确定当前角色
        self._current_role = None
        self._my_application = None
        uid = self.api_client.user_id
        for m in self._members:
            if m.get("user_id") == uid:
                self._current_role = m.get("role", ""); break
        self._current_role = self.api_client.role or self._current_role or ""

        # 查询我的申请状态
        self._check_my_application()

        self._populate_members()
        self._update_button_visibility()

    def _check_my_application(self):
        """检查当前用户是否有待审批的申请"""
        if not self._current_team_id or not self.api_client: return
        if self._current_role: self._my_application = None; return  # 已是成员
        try:
            apps = self.api_client.get_applications(self._current_team_id)
            uid = self.api_client.user_id
            for a in apps:
                if a.get("userId") == uid:
                    self._my_application = a; return
        except Exception as e:
            print(f"[TeamView] Check application failed: {e}")

    def _clear_ui(self):
        self._members = []; self._current_team_id = None; self._current_role = None
        self._my_application = None
        self._team_name_label.setText("暂无团队")
        self._invite_label.setText("📋 N/A")
        self._populate_members()
        self._app_table.setRowCount(0)
        self._dismiss_btn.setVisible(False)
        self._refresh_btn.setVisible(False)

    def _update_button_visibility(self):
        is_lead = self._current_role == "TECH_LEAD"
        self._dismiss_btn.setVisible(is_lead)
        self._refresh_btn.setVisible(is_lead)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16); layout.setSpacing(12)

        # ── 团队切换器 ──
        top = QHBoxLayout()
        self._combo = QComboBox(); self._combo.setFixedWidth(240)
        self._combo.setStyleSheet("QComboBox{border-radius:4px;padding:4px 8px;font-size:13px;}")
        self._combo.currentIndexChanged.connect(self._on_team_changed)
        top.addWidget(self._combo)
        top.addStretch()
        self._invite_label = QLabel("📋 ...")
        self._invite_label.setStyleSheet("font-size:14px;color:#4A90D9;font-family:monospace;")
        top.addWidget(self._invite_label)
        self._refresh_btn = QPushButton("🔄")
        self._refresh_btn.setFixedSize(32, 32)
        self._refresh_btn.setStyleSheet("QPushButton{background:transparent;border:1px solid #555;border-radius:4px;font-size:14px;}")
        self._refresh_btn.setCursor(Qt.PointingHandCursor)
        self._refresh_btn.clicked.connect(self._on_regenerate_code)
        self._refresh_btn.setVisible(False)
        top.addWidget(self._refresh_btn)
        layout.addLayout(top)

        # ── 团队名称+角色 ──
        info_row = QHBoxLayout()
        self._team_name_label = QLabel("加载中...")
        self._team_name_label.setStyleSheet("font-size:20px;font-weight:bold;")
        info_row.addWidget(self._team_name_label)
        self._role_label = QLabel("")
        self._role_label.setStyleSheet("font-size:12px;padding:2px 8px;border-radius:3px;")
        info_row.addWidget(self._role_label)
        info_row.addStretch()
        layout.addLayout(info_row)

        # ── 我的申请状态 ──
        self._app_status_label = QLabel("")
        self._app_status_label.setObjectName("ApplyStatus")
        self._app_status_label.setStyleSheet("font-size:12px;color:#F5A623;padding:4px 8px;")
        self._app_status_label.setVisible(False)
        layout.addWidget(self._app_status_label)

        # ── 按钮行 ──
        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        create_btn = QPushButton("+ 创建团队")
        create_btn.setStyleSheet("QPushButton{background:#238636;color:#FFF;border:none;border-radius:4px;padding:6px 14px;font-size:12px;}")
        create_btn.setCursor(Qt.PointingHandCursor); create_btn.clicked.connect(self._on_create_team)
        btn_row.addWidget(create_btn)
        join_btn = QPushButton("📋 加入团队")
        join_btn.setStyleSheet("QPushButton{background:transparent;color:#4A90D9;border:1px solid #4A90D9;border-radius:4px;padding:6px 14px;font-size:12px;}")
        join_btn.setCursor(Qt.PointingHandCursor); join_btn.clicked.connect(self._on_join_team)
        btn_row.addWidget(join_btn)
        btn_row.addStretch()
        self._dismiss_btn = QPushButton("🗑 解散团队")
        self._dismiss_btn.setStyleSheet("QPushButton{background:transparent;color:#E74C3C;border:1px solid #E74C3C;border-radius:4px;padding:4px 10px;font-size:11px;}")
        self._dismiss_btn.setCursor(Qt.PointingHandCursor); self._dismiss_btn.clicked.connect(self._on_dissolve)
        self._dismiss_btn.setVisible(False)
        btn_row.addWidget(self._dismiss_btn)
        layout.addLayout(btn_row)

        # ── 双栏主体 ──
        splitter = QSplitter(Qt.Horizontal)

        # 左：成员列表
        left = QFrame(); left.setObjectName("MemberPanel")
        ll = QVBoxLayout(left); ll.setContentsMargins(10, 8, 10, 8)
        ll.addWidget(QLabel("👥 成员列表"))
        ll.itemAt(0).widget().setStyleSheet("font-size:13px;font-weight:bold;")
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["成员", "角色", "操作"])
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionMode(QAbstractItemView.NoSelection)
        self._table.setShowGrid(False); self._table.verticalHeader().setVisible(False)
        h = self._table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        h.setSectionResizeMode(1, QHeaderView.Fixed); self._table.setColumnWidth(1, 80)
        h.setSectionResizeMode(2, QHeaderView.Fixed); self._table.setColumnWidth(2, 80)
        self._table.setStyleSheet("QTableWidget{border:none;font-size:12px;} QTableWidget::item{padding:4px;}")
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        ll.addWidget(self._table)
        splitter.addWidget(left)

        # 右：审批面板
        right = QFrame(); right.setObjectName("ApprovalPanel")
        right.setObjectName("ApprovalPanel")
        rl = QVBoxLayout(right); rl.setContentsMargins(10, 8, 10, 8)
        rl.addWidget(QLabel("📋 入团申请"))
        rl.itemAt(0).widget().setStyleSheet("font-size:13px;font-weight:bold;")
        self._no_app_label = QLabel("暂无待审批申请")
        self._no_app_label.setStyleSheet("font-size:12px;color:#6E6E8E;padding:20px;")
        self._no_app_label.setAlignment(Qt.AlignCenter)
        self._app_table = QTableWidget()
        self._app_table.setColumnCount(4)
        self._app_table.setHorizontalHeaderLabels(["申请人", "时间", "", ""])
        self._app_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._app_table.setSelectionMode(QAbstractItemView.NoSelection)
        self._app_table.setShowGrid(False); self._app_table.verticalHeader().setVisible(False)
        ah = self._app_table.horizontalHeader()
        ah.setSectionResizeMode(0, QHeaderView.Stretch)
        ah.setSectionResizeMode(1, QHeaderView.Fixed); self._app_table.setColumnWidth(1, 80)
        ah.setSectionResizeMode(2, QHeaderView.Fixed); self._app_table.setColumnWidth(2, 70)
        ah.setSectionResizeMode(3, QHeaderView.Fixed); self._app_table.setColumnWidth(3, 70)
        self._app_table.setStyleSheet("QTableWidget{border:none;font-size:12px;}")
        rl.addWidget(self._app_table)
        rl.addWidget(self._no_app_label)
        splitter.addWidget(right)
        splitter.setSizes([400, 350])
        layout.addWidget(splitter, 1)

    # ═══ 成员填充 ═══
    def _populate_members(self):
        self._table.setRowCount(len(self._members))
        for row, m in enumerate(self._members):
            name = m.get("name") or m.get("username") or m.get("user_id", "?")
            role = m.get("role", "DEVELOPER")
            self._table.setItem(row, 0, QTableWidgetItem(name))
            ri = QTableWidgetItem(ROLE_LABELS.get(role, role))
            ri.setTextAlignment(Qt.AlignCenter)
            ri.setForeground(QBrush(QColor(ROLE_COLORS.get(role, "#8E8E9E"))))
            self._table.setItem(row, 1, ri)
            # 移除按钮 — TECH_LEAD 和 SCRUM_MASTER
            if self._current_role in ("TECH_LEAD", "SCRUM_MASTER"):
                uid = m.get("user_id"); r = row
                btn = QPushButton("移除")
                btn.setStyleSheet("QPushButton{color:#E74C3C;border:1px solid #E74C3C;border-radius:3px;padding:2px 6px;font-size:11px;background:transparent;}")
                btn.setCursor(Qt.PointingHandCursor)
                btn.clicked.connect(lambda checked, uid=uid, row=r: self._remove_member(uid, row))
                container = QWidget()
                cl = QHBoxLayout(container); cl.setContentsMargins(0, 0, 0, 0); cl.setAlignment(Qt.AlignCenter)
                cl.addWidget(btn); self._table.setCellWidget(row, 2, container)

        # 更新角色标签
        if self._current_role:
            self._role_label.setText(ROLE_LABELS.get(self._current_role, self._current_role))
            self._role_label.setStyleSheet(
                f"font-size:12px;padding:2px 8px;border-radius:3px;"
                f"color:{ROLE_COLORS.get(self._current_role,'#8E8E9E')};border:1px solid {ROLE_COLORS.get(self._current_role,'#8E8E9E')};"
            )

        # 更新我的申请状态
        if self._my_application:
            self._app_status_label.setText("⚠ 你的入团申请正在等待审核中")
            self._app_status_label.setVisible(True)
        else:
            self._app_status_label.setVisible(False)

    # ═══ 审批面板 ═══
    def _load_applications(self):
        if not self._current_team_id or not self.api_client: return
        if self._current_role not in ("TECH_LEAD", "SCRUM_MASTER"):
            self._app_table.setRowCount(0)
            self._no_app_label.setVisible(False)
            return
        apps = self.api_client.get_applications(self._current_team_id)
        self._app_table.setRowCount(len(apps))
        self._no_app_label.setVisible(len(apps) == 0)
        self._app_table.setVisible(len(apps) > 0)
        for row, a in enumerate(apps):
            self._app_table.setItem(row, 0, QTableWidgetItem(a.get("name", "?")))
            t = a.get("createdAt", "")[:16] if a.get("createdAt") else ""
            self._app_table.setItem(row, 1, QTableWidgetItem(t))
            aid = a.get("id")
            approve = QPushButton("✓ 批准")
            approve.setStyleSheet("QPushButton{color:#238636;border:1px solid #238636;border-radius:3px;padding:2px 6px;font-size:11px;background:transparent;} QPushButton:hover{background:#238636;color:#FFF;}")
            approve.setCursor(Qt.PointingHandCursor)
            approve.clicked.connect(lambda checked, aid=aid: self._on_approve(aid))
            self._app_table.setCellWidget(row, 2, approve)
            reject = QPushButton("✕ 拒绝")
            reject.setStyleSheet("QPushButton{color:#E74C3C;border:1px solid #E74C3C;border-radius:3px;padding:2px 6px;font-size:11px;background:transparent;} QPushButton:hover{background:#E74C3C;color:#FFF;}")
            reject.setCursor(Qt.PointingHandCursor)
            reject.clicked.connect(lambda checked, aid=aid: self._on_reject(aid))
            self._app_table.setCellWidget(row, 3, reject)

    # ═══ 右键菜单(仅技术主管) ═══
    def _on_context_menu(self, pos):
        if self._current_role != "TECH_LEAD": return
        row = self._table.indexAt(pos).row()
        if row < 0 or row >= len(self._members): return
        m = self._members[row]
        menu = QMenu(self)
        for role_key in ("SCRUM_MASTER", "DEVELOPER", "OBSERVER"):
            act = menu.addAction(f"改为{ROLE_LABELS[role_key]}")
            act.triggered.connect(lambda checked, uid=m["user_id"], r=role_key: self._on_change_role(uid, r))
        menu.exec(self._table.viewport().mapToGlobal(pos))

    # ═══ 操作 ═══
    def _on_team_changed(self, _idx):
        if self._combo.count() == 0: return
        self._load_data()
        if self._current_team_id:
            self._load_applications()

    def _on_create_team(self):
        dlg = CreateTeamDialog(self.api_client, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_teams()
            self._load_data()

    def _on_join_team(self):
        dlg = JoinTeamDialog(self.api_client, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_data()

    def _on_regenerate_code(self):
        if self._current_role != "TECH_LEAD":
            QMessageBox.warning(self, "提示", "只有技术主管可以重新生成邀请码"); return
        r = self.api_client.regenerate_invite_code(self._current_team_id)
        if r and r.get("code") == 200:
            new_code = r.get("data")
            if isinstance(new_code, str) and len(new_code) == 6:
                self._invite_code = new_code
            elif r.get("message"):
                self._invite_code = str(r["message"])
            self._invite_label.setText(f"📋 {self._invite_code}")

    def _on_approve(self, app_id):
        self.api_client.approve_application(self._current_team_id, app_id)
        self._load_data()
        self._load_applications()

    def _on_reject(self, app_id):
        self.api_client.reject_application(self._current_team_id, app_id)
        self._load_data()
        self._load_applications()

    def _on_change_role(self, user_id, new_role):
        r = self.api_client.change_member_role(self._current_team_id, user_id, new_role)
        if r and r.get("code") == 200: self._load_data()
        else:
            msg = r.get("message", "操作失败") if r else "后端无响应"
            QMessageBox.warning(self, "提示", msg)

    def _remove_member(self, user_id, row):
        try:
            import requests
            from api_client import APIClient
            requests.delete(
                f"{APIClient.base_url()}/api/teams/{self._current_team_id}/members/{user_id}",
                headers=self.api_client._headers(), timeout=5)
            if 0 <= row < len(self._members): del self._members[row]
            self._populate_members()
            self.member_removed.emit(str(user_id))
        except Exception as e:
            print(f"[TeamView] Remove member failed: {e}")

    def _on_dissolve(self):
        if self._current_role != "TECH_LEAD":
            QMessageBox.warning(self, "提示", "只有技术主管可以解散团队"); return
        reply = QMessageBox.question(self, "确认", "确定要解散团队吗？此操作不可撤销。", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes: return
        r = self.api_client.dissolve_team(self._current_team_id)
        if r and r.get("code") == 200:
            self._load_teams()
            self._clear_ui()
            self.team_dissolved.emit()
