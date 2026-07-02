# views/transfer_view.py — 转交审核面板（管理员专用）
"""待办转交审核：待审核 + 已审核 双栏布局。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QScrollArea, QInputDialog, QMessageBox, QTabWidget,
)
from PySide6.QtCore import Qt, Signal
from widgets import EmptyState


class TransferView(QWidget):
    """管理员转交审核面板。"""

    title = "转交审核"

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._pending = []
        self._reviewed = []
        self._setup_ui()

    def activate(self):
        if not self.api_client:
            return
        teams = self.api_client.get_teams()
        if not teams:
            self._pending = []
            self._reviewed = []
            self._refresh()
            return
        self._team_id = teams[0].get("id")
        self._load_all()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        title = QLabel("转交审核")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        self._tabs = QTabWidget()
        self._pending_tab = QWidget()
        self._reviewed_tab = QWidget()
        self._tabs.addTab(self._pending_tab, "待审核")
        self._tabs.addTab(self._reviewed_tab, "已审核")

        self._pending_layout = QVBoxLayout(self._pending_tab)
        self._pending_layout.setContentsMargins(0, 8, 0, 0)
        self._pending_scroll = QScrollArea()
        self._pending_scroll.setWidgetResizable(True)
        self._pending_container = QWidget()
        self._pending_container_layout = QVBoxLayout(self._pending_container)
        self._pending_container_layout.setSpacing(8)
        self._pending_container_layout.addStretch()
        self._pending_scroll.setWidget(self._pending_container)
        self._pending_layout.addWidget(self._pending_scroll)

        self._reviewed_layout = QVBoxLayout(self._reviewed_tab)
        self._reviewed_layout.setContentsMargins(0, 8, 0, 0)
        self._reviewed_scroll = QScrollArea()
        self._reviewed_scroll.setWidgetResizable(True)
        self._reviewed_container = QWidget()
        self._reviewed_container_layout = QVBoxLayout(self._reviewed_container)
        self._reviewed_container_layout.setSpacing(8)
        self._reviewed_container_layout.addStretch()
        self._reviewed_scroll.setWidget(self._reviewed_container)
        self._reviewed_layout.addWidget(self._reviewed_scroll)

        layout.addWidget(self._tabs)

    def _load_all(self):
        if not self.api_client or not hasattr(self, '_team_id'):
            return
        self._pending = self.api_client.get_pending_transfers(self._team_id)
        self._reviewed = self.api_client.get_reviewed_transfers(self._team_id)
        self._refresh()

    def _refresh(self):
        self._tabs.setTabText(0, f"待审核 ({len(self._pending)})")
        self._tabs.setTabText(1, f"已审核 ({len(self._reviewed)})")
        self._refresh_pending()
        self._refresh_reviewed()

    def _refresh_pending(self):
        # Clear
        while self._pending_container_layout.count() > 1:
            item = self._pending_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._pending:
            empty = EmptyState("", "暂无待审核转交", "")
            self._pending_container_layout.insertWidget(0, empty)
            return

        for item in self._pending:
            card = self._create_pending_card(item)
            self._pending_container_layout.insertWidget(
                self._pending_container_layout.count() - 1, card)

    def _create_pending_card(self, item):
        card = QFrame()
        card.setStyleSheet(
            "#TransferPendingCard{border:1px solid #2A2A4E;border-radius:8px;padding:12px;}"
        )
        card.setObjectName("TransferPendingCard")
        layout = QVBoxLayout(card)
        layout.setSpacing(6)

        content = QLabel(item.get("content", ""))
        content.setWordWrap(True)
        content.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(content)

        assignee = item.get("assignee", {}) or {}
        orig_name = assignee.get("displayName", "?")
        target_id = item.get("pendingAssigneeId", "?")
        info = QLabel(f"转交: {orig_name} → {target_id[:8]}...")
        info.setStyleSheet("font-size: 12px; color: #8E8E9E;")
        layout.addWidget(info)

        reason = item.get("transferReason", "")
        if reason:
            r = QLabel(f"理由: {reason}")
            r.setStyleSheet("font-size: 12px; color: #F5A623;")
            layout.addWidget(r)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        approve_btn = QPushButton("批准")
        approve_btn.setStyleSheet(
            "QPushButton{background:#238636;color:#FFF;border:none;border-radius:4px;"
            "padding:4px 16px;font-size:12px;}QPushButton:hover{background:#2EA043;}"
        )
        approve_btn.setCursor(Qt.PointingHandCursor)
        tid = item.get("id")
        approve_btn.clicked.connect(lambda checked, i=tid: self._on_approve(i))
        btn_row.addWidget(approve_btn)

        reject_btn = QPushButton("拒绝")
        reject_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#E74C3C;border:1px solid #E74C3C;"
            "border-radius:4px;padding:4px 16px;font-size:12px;}"
            "QPushButton:hover{background:#E74C3C;color:#FFF;}"
        )
        reject_btn.setCursor(Qt.PointingHandCursor)
        reject_btn.clicked.connect(lambda checked, i=tid: self._on_reject(i))
        btn_row.addWidget(reject_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        return card

    def _refresh_reviewed(self):
        while self._reviewed_container_layout.count() > 1:
            item = self._reviewed_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._reviewed:
            empty = EmptyState("", "暂无审核记录", "")
            self._reviewed_container_layout.insertWidget(0, empty)
            return

        for item in self._reviewed:
            card = self._create_reviewed_card(item)
            self._reviewed_container_layout.insertWidget(
                self._reviewed_container_layout.count() - 1, card)

    def _create_reviewed_card(self, item):
        card = QFrame()
        card.setStyleSheet(
            "#TransferReviewedCard{border:1px solid #2A2A4E;border-radius:8px;padding:12px;}"
        )
        card.setObjectName("TransferReviewedCard")
        layout = QVBoxLayout(card)
        layout.setSpacing(6)

        content = QLabel(item.get("content", ""))
        content.setWordWrap(True)
        content.setStyleSheet("font-size: 13px;")
        layout.addWidget(content)

        status = item.get("transferStatus", "NONE")
        status_text = "已批准" if status == "APPROVED" else "已拒绝"
        status_color = "#52C41A" if status == "APPROVED" else "#E74C3C"
        status_lbl = QLabel(status_text)
        status_lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {status_color};")
        layout.addWidget(status_lbl)

        if status == "REJECTED" and item.get("rejectReason"):
            rr = QLabel(f"拒绝理由: {item.get('rejectReason', '')}")
            rr.setStyleSheet("font-size: 11px; color: #E74C3C;")
            layout.addWidget(rr)

        time_str = str(item.get("transferApprovedAt", ""))[:16] if item.get("transferApprovedAt") else ""
        if time_str:
            tl = QLabel(time_str)
            tl.setStyleSheet("font-size: 11px; color: #6E6E8E;")
            layout.addWidget(tl)

        hide_btn = QPushButton("隐藏记录")
        hide_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#8E8E9E;border:1px solid #555;"
            "border-radius:4px;padding:2px 10px;font-size:11px;}"
            "QPushButton:hover{color:#FFF;border-color:#8E8E9E;}"
        )
        hide_btn.setCursor(Qt.PointingHandCursor)
        tid = item.get("id")
        hide_btn.clicked.connect(lambda checked, i=tid: self._on_hide(i))
        btn_row2 = QHBoxLayout()
        btn_row2.addStretch()
        btn_row2.addWidget(hide_btn)
        layout.addLayout(btn_row2)

        return card

    def _on_approve(self, todo_id):
        if self.api_client:
            resp = self.api_client.approve_transfer(todo_id)
            if resp and resp.get("code") == 200:
                self._load_all()
            else:
                msg = "操作失败"
                if resp:
                    msg = resp.get("message", msg)
                QMessageBox.warning(self, "错误", msg)

    def _on_reject(self, todo_id):
        reason, ok = QInputDialog.getText(self, "拒绝转交", "请输入拒绝理由（可选）:")
        if not ok:
            return
        if self.api_client:
            resp = self.api_client.reject_transfer(todo_id, reason)
            if resp and resp.get("code") == 200:
                self._load_all()
            else:
                msg = "操作失败"
                if resp:
                    msg = resp.get("message", msg)
                QMessageBox.warning(self, "错误", msg)

    def _on_hide(self, todo_id):
        if self.api_client:
            self.api_client.hide_transfer_record(todo_id)
            self._load_all()
