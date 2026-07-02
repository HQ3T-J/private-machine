# views/todo_detail_view.py — 待办详情弹窗 + 转交操作面板
"""待办详情弹窗：基本信息 + 转交记录 + 操作按钮 + 转交面板。"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QFrame, QMessageBox,
)
from PySide6.QtCore import Qt

PRIORITY_COLORS = {"HIGH": "#E74C3C", "MEDIUM": "#F5A623", "LOW": "#52C41A"}
STATUS_LABELS = {
    "PENDING": "待处理", "IN_PROGRESS": "进行中",
    "REVIEWING": "审核中", "DONE": "已完成", "CANCELLED": "已取消",
}


class TodoDetailDialog(QDialog):
    """待办详情 + 转交操作。"""

    def __init__(self, todo, api_client=None, team_members=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.todo = todo
        self.team_members = team_members or []
        self._showing_transfer = False
        self.setWindowTitle("待办详情")
        self.setFixedSize(460, 520)
        self._setup_ui()
        self._show_todo()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # ── 基本信息区 ──
        self._content_label = QLabel("")
        self._content_label.setWordWrap(True)
        self._content_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self._content_label)

        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(6)

        self._labels = {}
        for key, title in [
            ("priority", "优先级"), ("status", "状态"), ("assignee", "责任人"),
            ("dueDate", "截止日期"), ("creator", "创建人"), ("createdAt", "创建时间"),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(f"{title}:")
            lbl.setFixedWidth(70)
            lbl.setStyleSheet("font-size: 12px; color: #8E8E9E;")
            row.addWidget(lbl)
            val = QLabel("--")
            val.setStyleSheet("font-size: 12px;")
            self._labels[key] = val
            row.addWidget(val, 1)
            info_layout.addLayout(row)

        layout.addWidget(info_frame)

        # ── 转交记录区 ──
        self._transfer_label = QLabel("")
        self._transfer_label.setWordWrap(True)
        self._transfer_label.setVisible(False)
        self._transfer_label.setStyleSheet(
            "font-size: 11px; padding: 8px; border:1px solid #2A2A4E; border-radius:4px;"
        )
        layout.addWidget(self._transfer_label)

        layout.addStretch()

        # ── 操作按钮 ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._complete_btn = QPushButton("标记完成")
        self._complete_btn.setStyleSheet(
            "QPushButton{background:#52C41A;color:#FFF;border:none;border-radius:4px;"
            "padding:6px 14px;font-size:12px;}QPushButton:hover{background:#45A818;}"
        )
        self._complete_btn.setCursor(Qt.PointingHandCursor)
        self._complete_btn.clicked.connect(lambda: self._mark_status("DONE"))
        btn_row.addWidget(self._complete_btn)

        self._progress_btn = QPushButton("标记进行中")
        self._progress_btn.setStyleSheet(
            "QPushButton{background:#F5A623;color:#FFF;border:none;border-radius:4px;"
            "padding:6px 14px;font-size:12px;}QPushButton:hover{background:#D4901E;}"
        )
        self._progress_btn.setCursor(Qt.PointingHandCursor)
        self._progress_btn.clicked.connect(lambda: self._mark_status("IN_PROGRESS"))
        btn_row.addWidget(self._progress_btn)

        self._transfer_btn = QPushButton("转交他人")
        self._transfer_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#4A9ED9;border:1px solid #4A9ED9;"
            "border-radius:4px;padding:6px 14px;font-size:12px;}"
            "QPushButton:hover{background:rgba(74,144,217,0.2);}"
        )
        self._transfer_btn.setCursor(Qt.PointingHandCursor)
        self._transfer_btn.clicked.connect(self._toggle_transfer)
        btn_row.addWidget(self._transfer_btn)

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#8E8E9E;border:1px solid #555;"
            "border-radius:4px;padding:6px 14px;font-size:12px;}"
        )
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

        # ── 转交面板（默认隐藏）──
        self._transfer_panel = QFrame()
        self._transfer_panel.setVisible(False)
        self._transfer_panel.setStyleSheet(
            "#TransferPanel{border:1px solid #F5A623;border-radius:6px;padding:10px;}"
        )
        self._transfer_panel.setObjectName("TransferPanel")
        tp_layout = QVBoxLayout(self._transfer_panel)
        tp_layout.setSpacing(8)

        tp_label = QLabel("转交待办")
        tp_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        tp_layout.addWidget(tp_label)

        member_row = QHBoxLayout()
        member_row.addWidget(QLabel("目标成员:"))
        self._member_combo = QComboBox()
        self._member_combo.setStyleSheet(
            "QComboBox{border-radius:4px;padding:4px 8px;font-size:12px;}"
        )
        for m in self.team_members:
            name = m.get("name") or m.get("displayName") or m.get("username", "?")
            self._member_combo.addItem(name, m.get("user_id") or m.get("userId"))
        member_row.addWidget(self._member_combo, 1)
        tp_layout.addLayout(member_row)

        reason_row = QHBoxLayout()
        reason_row.addWidget(QLabel("转交理由:"))
        self._reason_input = QLineEdit()
        self._reason_input.setPlaceholderText("可选")
        self._reason_input.setStyleSheet(
            "QLineEdit{border-radius:4px;padding:4px 8px;font-size:12px;}"
        )
        reason_row.addWidget(self._reason_input, 1)
        tp_layout.addLayout(reason_row)

        tp_hint = QLabel("非管理员转交需管理员审核后方可生效")
        tp_hint.setStyleSheet("font-size: 11px; color: #F5A623;")
        tp_layout.addWidget(tp_hint)

        tp_btn_row = QHBoxLayout()
        tp_btn_row.addStretch()
        tp_cancel = QPushButton("取消")
        tp_cancel.setStyleSheet(
            "QPushButton{background:transparent;color:#8E8E9E;border:1px solid #555;"
            "border-radius:4px;padding:4px 12px;font-size:11px;}"
        )
        tp_cancel.setCursor(Qt.PointingHandCursor)
        tp_cancel.clicked.connect(self._toggle_transfer)
        tp_btn_row.addWidget(tp_cancel)

        tp_confirm = QPushButton("确认转交")
        tp_confirm.setStyleSheet(
            "QPushButton{background:#F5A623;color:#FFF;border:none;border-radius:4px;"
            "padding:4px 12px;font-size:11px;font-weight:bold;}"
            "QPushButton:hover{background:#D4901E;}"
        )
        tp_confirm.setCursor(Qt.PointingHandCursor)
        tp_confirm.clicked.connect(self._on_transfer)
        tp_btn_row.addWidget(tp_confirm)
        tp_layout.addLayout(tp_btn_row)

        layout.addWidget(self._transfer_panel)

    def _show_todo(self):
        t = self.todo
        self._content_label.setText(t.get("content", ""))

        priority = t.get("priority", "--")
        self._labels["priority"].setText(priority)
        self._labels["priority"].setStyleSheet(
            f"color:{PRIORITY_COLORS.get(priority, '#8E8E9E')};font-size:12px;font-weight:bold;"
        )

        status = t.get("status", "--")
        self._labels["status"].setText(STATUS_LABELS.get(status, status))

        assignee = t.get("assignee", {}) or {}
        name = assignee.get("displayName", "--") if isinstance(assignee, dict) else str(assignee)
        self._labels["assignee"].setText(name)

        due = t.get("dueDate", "")
        self._labels["dueDate"].setText(str(due)[:10] if due else "--")

        assigner = t.get("assigner", {}) or {}
        creator_name = assigner.get("displayName", "--") if isinstance(assigner, dict) else "--"
        self._labels["creator"].setText(creator_name)

        created = t.get("createdAt", "")
        self._labels["createdAt"].setText(str(created)[:16] if created else "--")

        # Transfer history
        transfer_status = t.get("transferStatus", "NONE")
        if transfer_status == "NONE":
            self._transfer_label.setVisible(False)
        else:
            lines = []
            if transfer_status == "PENDING":
                tid = t.get("pendingAssigneeId", "?")
                lines.append(f"转交中 → {tid[:8]}... (审核中)")
            elif transfer_status == "APPROVED":
                lines.append("转交已批准")
                if t.get("transferApprovedAt"):
                    lines.append(f"审批时间: {str(t.get('transferApprovedAt'))[:16]}")
            elif transfer_status == "REJECTED":
                lines.append("转交被拒绝")
                if t.get("rejectReason"):
                    lines.append(f"理由: {t.get('rejectReason')}")
            if t.get("transferReason"):
                lines.append(f"转交理由: {t.get('transferReason')}")
            self._transfer_label.setText("\n".join(lines))
            self._transfer_label.setVisible(True)

        # Button state
        current_status = t.get("status", "")
        self._complete_btn.setEnabled(current_status != "DONE")
        self._progress_btn.setEnabled(current_status not in ("DONE", "REVIEWING"))
        self._transfer_btn.setEnabled(current_status not in ("DONE", "REVIEWING"))

    def _toggle_transfer(self):
        self._showing_transfer = not self._showing_transfer
        self._transfer_panel.setVisible(self._showing_transfer)
        self._transfer_btn.setText("取消转交" if self._showing_transfer else "转交他人")

    def _mark_status(self, new_status):
        if not self.api_client:
            return
        tid = self.todo.get("id")
        resp = self.api_client.update_todo(str(tid), {"status": new_status})
        if resp and resp.get("code") == 200:
            self.todo["status"] = new_status
            self._show_todo()
            self.accept()
        else:
            QMessageBox.warning(self, "错误", "状态更新失败")

    def _on_transfer(self):
        if not self.api_client:
            QMessageBox.warning(self, "提示", "未连接到后端")
            return
        target_id = self._member_combo.currentData()
        if not target_id:
            QMessageBox.warning(self, "提示", "请选择目标成员")
            return
        reason = self._reason_input.text().strip()
        tid = self.todo.get("id")
        resp = self.api_client.transfer_todo(tid, target_id, reason)
        if resp and resp.get("code") == 200:
            QMessageBox.information(self, "成功", "转交申请已提交")
            self.accept()
        else:
            msg = resp.get("message", "转交失败") if resp else "后端无响应"
            QMessageBox.warning(self, "错误", msg)
