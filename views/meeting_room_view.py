"""站会进行中页面 - StandupSync"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QFrame, QSizePolicy,
    QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal


class MeetingRoomView(QWidget):
    """站会进行中页面 — 对接后端API"""

    meeting_ended = Signal(int)  # meeting_id
    navigate_back = Signal()

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.title = "站会进行中"
        self._meeting_id = None
        self._meeting_data = {}
        self._members = []
        self._speeches = []
        self._current_speaker_idx = 0
        self._timer_seconds = 120
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick_timer)
        self._setup_ui()

    def activate(self, meeting_id=None, meeting_data=None):
        """进入站会室：加载真实数据"""
        self._meeting_id = meeting_id
        self._meeting_data = meeting_data or {}
        self._load_meeting_data()
        self._refresh_all()

    def _load_meeting_data(self):
        if not self.api_client or not self._meeting_id:
            return
        # 加载参会成员
        mid = self._meeting_id
        result = self.api_client._get(f"/api/meetings/{mid}")
        if result and isinstance(result, dict):
            self._meeting_data = result
            self._members = result.get("participants", [])
        # 加载已有发言
        speeches = self.api_client.get_speeches(str(mid))
        self._speeches = speeches if speeches else []

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # ---- 顶部标题栏 ----
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        back_btn = QPushButton("← 返回")
        back_btn.setStyleSheet("""
            QPushButton { border: 1px solid #555; border-radius: 4px; padding: 4px 10px; font-size: 12px; }
        """)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(lambda: self.navigate_back.emit())
        top_bar.addWidget(back_btn)

        self._title_label = QLabel("站会进行中")
        self._title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        top_bar.addWidget(self._title_label)

        self._timer_label = QLabel("⏱ 02:00")
        self._timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4A90D9;")
        top_bar.addWidget(self._timer_label)

        top_bar.addStretch()

        btn_style = """
            QPushButton { border-radius: 6px; padding: 6px 14px; font-size: 13px; }
        """

        skip_btn = QPushButton("跳过此人")
        skip_btn.setStyleSheet(btn_style)
        skip_btn.setCursor(Qt.PointingHandCursor)
        skip_btn.clicked.connect(self._on_skip_speaker)
        top_bar.addWidget(skip_btn)

        paste_btn = QPushButton("粘贴记录")
        paste_btn.setStyleSheet(btn_style)
        paste_btn.setCursor(Qt.PointingHandCursor)
        paste_btn.clicked.connect(self._on_paste_chat)
        top_bar.addWidget(paste_btn)

        end_btn = QPushButton("结束站会")
        end_btn.setStyleSheet("""
            QPushButton { background: #E74C3C; color: #FFF; border: none;
                border-radius: 6px; padding: 6px 14px; font-size: 13px; font-weight: bold; }
            QPushButton:hover { background: #C0392B; }
        """)
        end_btn.setCursor(Qt.PointingHandCursor)
        end_btn.clicked.connect(self._on_end_meeting)
        top_bar.addWidget(end_btn)

        layout.addLayout(top_bar)

        # ---- 三栏分屏 ----
        three_col = QHBoxLayout()
        three_col.setSpacing(12)

        left_col = self._create_member_list()
        three_col.addWidget(left_col, 1)

        center_col = self._create_speech_area()
        three_col.addWidget(center_col, 2)

        right_col = self._create_completed_area()
        three_col.addWidget(right_col, 1)

        layout.addLayout(three_col, 1)

        hint_label = QLabel("Ctrl+Enter 提交发言")
        hint_label.setStyleSheet("font-size: 12px; padding: 4px 0;")
        hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint_label)

        # Ctrl+Enter shortcut
        self._submit_shortcut = None

    def _create_member_list(self):
        container = QWidget()
        container.setFixedWidth(210)
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)

        member_label = QLabel("👥 参会成员")
        member_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        cl.addWidget(member_label)

        self.member_list = QListWidget()
        self.member_list.setStyleSheet("""
            QListWidget { border-radius: 8px; padding: 6px; }
            QListWidget::item { padding: 8px 10px; border-radius: 4px; margin: 2px 0; }
        """)
        cl.addWidget(self.member_list, 1)
        return container

    def _create_speech_area(self):
        container = QWidget()
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(10)

        self._speaker_label = QLabel("🎤 等待发言")
        self._speaker_label.setStyleSheet("""
            font-size: 16px; font-weight: bold; color: #4A90D9;
            padding: 12px; border: 2px solid #4A90D9; border-radius: 8px;
        """)
        cl.addWidget(self._speaker_label)

        yesterday_label = QLabel("✅ 昨天完成了什么")
        yesterday_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        cl.addWidget(yesterday_label)

        self.yesterday_edit = QTextEdit()
        self.yesterday_edit.setPlaceholderText("例如: 完成了登录模块重构...")
        self.yesterday_edit.setStyleSheet("""
            QTextEdit { border-radius: 6px; padding: 8px; font-size: 13px; }
        """)
        self.yesterday_edit.setMaximumHeight(80)
        cl.addWidget(self.yesterday_edit)

        today_label = QLabel("📋 今天计划做什么")
        today_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        cl.addWidget(today_label)

        self.today_edit = QTextEdit()
        self.today_edit.setPlaceholderText("例如: 开始做权限管理模块...")
        self.today_edit.setStyleSheet("""
            QTextEdit { border-radius: 6px; padding: 8px; font-size: 13px; }
        """)
        self.today_edit.setMaximumHeight(80)
        cl.addWidget(self.today_edit)

        blocker_label = QLabel("🚧 阻碍")
        blocker_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        cl.addWidget(blocker_label)

        self.blocker_edit = QTextEdit()
        self.blocker_edit.setPlaceholderText("无（如有阻碍请填写）")
        self.blocker_edit.setStyleSheet("""
            QTextEdit { border-radius: 6px; padding: 8px; font-size: 13px; }
        """)
        self.blocker_edit.setMaximumHeight(60)
        cl.addWidget(self.blocker_edit)

        # 提交按钮
        submit_bar = QHBoxLayout()
        submit_bar.addStretch()
        self._submit_btn = QPushButton("提交发言")
        self._submit_btn.setStyleSheet("""
            QPushButton { background-color: #52C41A; color: #FFF; border: none;
                border-radius: 6px; padding: 8px 20px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background-color: #45A818; }
        """)
        self._submit_btn.setCursor(Qt.PointingHandCursor)
        self._submit_btn.clicked.connect(self._on_submit_speech)
        submit_bar.addWidget(self._submit_btn)
        cl.addLayout(submit_bar)

        cl.addStretch()
        return container

    def _create_completed_area(self):
        container = QWidget()
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)

        completed_label = QLabel("✅ 已完成发言")
        completed_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        cl.addWidget(completed_label)

        self.completed_edit = QTextEdit()
        self.completed_edit.setReadOnly(True)
        self.completed_edit.setStyleSheet("""
            QTextEdit { border-radius: 8px; padding: 10px; font-size: 12px; }
        """)
        cl.addWidget(self.completed_edit, 1)
        return container

    # ── 数据刷新 ──
    def _refresh_all(self):
        self._refresh_title()
        self._refresh_members()
        self._refresh_completed()
        self._highlight_current_speaker()

    def _refresh_title(self):
        title = self._meeting_data.get("title", "") or f"Sprint#{self._meeting_data.get('sprintNo', '?')}"
        self._title_label.setText(f"站会 · {title}")

    def _refresh_members(self):
        self.member_list.clear()
        spoken_ids = {s.get("speaker", {}).get("id", "") for s in self._speeches}
        for i, m in enumerate(self._members):
            uid = m.get("user_id", "")
            name = m.get("displayName") or m.get("display_name") or m.get("username", f"成员{i+1}")
            if uid in spoken_ids:
                prefix = "🟢"
                suffix = "  已发言"
            elif i == self._current_speaker_idx:
                prefix = "🔵"
                suffix = "  发言中"
            else:
                prefix = "⚪"
                suffix = "  等待中"
            self.member_list.addItem(f"{prefix} {name}{suffix}")

    def _refresh_completed(self):
        lines = []
        for s in self._speeches:
            sp = s.get("speaker", {}) or {}
            speaker = sp.get("displayName") or sp.get("username") or s.get("speaker_id", "?")
            y = s.get("yesterday", "") or ""
            t = s.get("today", "") or ""
            b = s.get("blockers", "") or ""
            lines.append(f"{speaker} ✅")
            if y: lines.append(f"  昨天: {y[:80]}")
            if t: lines.append(f"  今天: {t[:80]}")
            if b: lines.append(f"  阻碍: {b[:80]}")
            lines.append("")
        self.completed_edit.setPlainText("\n".join(lines))

    def _highlight_current_speaker(self):
        if 0 <= self._current_speaker_idx < len(self._members):
            m = self._members[self._current_speaker_idx]
            name = m.get("displayName") or m.get("display_name") or m.get("username", "?")
            self._speaker_label.setText(f"🎤 {name} 正在发言")
        else:
            self._speaker_label.setText("🎤 全部发言完毕")

    # ── 操作 ──
    def _on_submit_speech(self):
        if not self.api_client or not self._meeting_id:
            QMessageBox.warning(self, "提示", "未连接到后端")
            return

        yesterday = self.yesterday_edit.toPlainText().strip()
        today = self.today_edit.toPlainText().strip()
        blockers = self.blocker_edit.toPlainText().strip()

        if not yesterday and not today:
            QMessageBox.warning(self, "提示", "请至少填写'昨天'或'今天'")
            return

        resp = self.api_client.submit_speech(str(self._meeting_id), yesterday, today, blockers)
        if resp and resp.get("code") == 200:
            # 清空输入
            self.yesterday_edit.clear()
            self.today_edit.clear()
            self.blocker_edit.clear()
            # 推进发言人
            self._current_speaker_idx += 1
            # 重新加载
            self._load_meeting_data()
            self._refresh_all()
            # 重置计时器
            self._timer_seconds = 120
            self._timer_label.setText("⏱ 02:00")
        else:
            QMessageBox.warning(self, "提交失败", resp.get("message", "未知错误") if resp else "后端无响应")

    def _on_skip_speaker(self):
        self._current_speaker_idx += 1
        self._refresh_all()
        self._timer_seconds = 120
        self._timer_label.setText("⏱ 02:00")

    def _on_paste_chat(self):
        QMessageBox.information(self, "粘贴记录", "请将聊天记录粘贴到发言区，\n格式: Name: content")

    def _on_end_meeting(self):
        if not self._meeting_id:
            return
        reply = QMessageBox.question(self, "确认", "确定结束本次站会？",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        if self.api_client:
            self.api_client.end_meeting(str(self._meeting_id))
        self._timer.stop()
        self.meeting_ended.emit(self._meeting_id)
        self.navigate_back.emit()

    def _tick_timer(self):
        if self._timer_seconds <= 0:
            self._timer.stop()
            self._timer_label.setText("⏱ 超时")
            return
        self._timer_seconds -= 1
        m = self._timer_seconds // 60
        s = self._timer_seconds % 60
        self._timer_label.setText(f"⏱ {m:02d}:{s:02d}")
