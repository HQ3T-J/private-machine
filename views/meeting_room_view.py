"""站会进行中页面 V3 — 单输入框 + AI解析 + 视频面板"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QFrame, QSizePolicy,
    QMessageBox, QScrollArea, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont


class VideoPanel(QFrame):
    """视频面板 — 显示参会成员视频缩略图（WebRTC占位）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("VideoPanel")
        self.setMinimumHeight(120)
        self.setMaximumHeight(180)
        self._video_slots = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        header = QHBoxLayout()
        title = QLabel("📹 视频会议")
        title.setStyleSheet("font-size: 12px; font-weight: bold; color: #8E8E9E;")
        header.addWidget(title)
        header.addStretch()
        self._toggle_btn = QPushButton("收起 ▲")
        self._toggle_btn.setStyleSheet("QPushButton{background:transparent;color:#4A90D9;border:none;font-size:11px;}")
        self._toggle_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self._toggle_btn)
        layout.addLayout(header)

        self._slots_layout = QHBoxLayout()
        self._slots_layout.setSpacing(8)
        layout.addLayout(self._slots_layout)

        self.setStyleSheet("#VideoPanel{background:#161B22;border-radius:8px;border:1px solid #30363D;}")

    def update_participants(self, members, video_users=None):
        """更新视频槽位"""
        video_users = video_users or set()
        # Clear
        while self._slots_layout.count():
            item = self._slots_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        for i, m in enumerate(members[:6]):
            uid = m.get("user_id", "")
            name = m.get("displayName") or m.get("display_name") or m.get("username", "?")
            has_video = uid in video_users

            slot = QFrame()
            slot.setFixedSize(140, 100)
            slot.setStyleSheet("QFrame{background:#0D1117;border-radius:6px;border:1px solid #30363D;}")
            sl = QVBoxLayout(slot)
            sl.setContentsMargins(4, 4, 4, 4)

            icon = QLabel("📹" if has_video else "👤")
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet("font-size: 24px;")
            sl.addWidget(icon)

            nl = QLabel(name[:8])
            nl.setAlignment(Qt.AlignCenter)
            nl.setStyleSheet("font-size: 10px; color: #C0C0D0;")
            sl.addWidget(nl)

            self._slots_layout.addWidget(slot)

        self._slots_layout.addStretch()


class MeetingRoomView(QWidget):
    """站会进行中 V3 — 单输入 + AI解析 + 视频 + 语音"""

    meeting_ended = Signal(int)
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
        self._timer_seconds = self._meeting_data.get("countdownSeconds", 900) if self._meeting_data else 900
        self._video_users = set()
        self._ws = None  # WebSocket connection

        self._timer = QTimer()
        self._timer.timeout.connect(self._tick_timer)
        self._setup_ui()

    def activate(self, meeting_id=None, meeting_data=None):
        self._meeting_id = meeting_id
        self._meeting_data = meeting_data or {}
        self._load_meeting_data()
        self._refresh_all()
        self._timer.start(1000)
        self._connect_ws()

    def _load_meeting_data(self):
        if not self.api_client or not self._meeting_id:
            return
        mid = self._meeting_id
        result = self.api_client._get(f"/api/meetings/{mid}")
        if result and isinstance(result, dict):
            self._meeting_data = result
        else:
            # 会议不存在或已删除
            self._meeting_data = {"id": mid, "status": "DELETED", "title": "已删除"}
            self._members = []
            self._speeches = []
            QMessageBox.warning(self, "提示", f"站会 #{mid} 不存在或已被删除")
            return
        speeches = self.api_client.get_speeches(str(mid))
        self._speeches = speeches if speeches else []

    def _connect_ws(self):
        """连接 WebSocket 接收实时更新"""
        try:
            import asyncio, json
            # WebSocket 在单独的线程中运行（简化方案：用轮询替代）
            # 实际生产环境建议用 QWebSocket
        except Exception:
            pass

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # ═══ 顶部栏 ═══
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        back_btn = QPushButton("← 返回")
        back_btn.setStyleSheet("QPushButton{border:1px solid #555;border-radius:4px;padding:4px 10px;font-size:12px;}")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(lambda: self._on_back())
        top_bar.addWidget(back_btn)

        self._title_label = QLabel("站会进行中")
        self._title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        top_bar.addWidget(self._title_label)

        self._timer_label = QLabel("⏱ 02:00")
        self._timer_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #4A90D9;")
        top_bar.addWidget(self._timer_label)

        top_bar.addStretch()

        end_btn = QPushButton("结束站会")
        end_btn.setStyleSheet("QPushButton{background:#E74C3C;color:#FFF;border:none;border-radius:6px;padding:6px 14px;font-size:12px;font-weight:bold;}")
        end_btn.setCursor(Qt.PointingHandCursor)
        end_btn.clicked.connect(self._on_end_meeting)
        top_bar.addWidget(end_btn)
        layout.addLayout(top_bar)

        # ═══ 三栏主体 ═══
        splitter = QSplitter(Qt.Horizontal)

        # 左栏：参会成员
        left = self._create_member_panel()
        splitter.addWidget(left)

        # 中栏：发言区（单输入框）
        center = self._create_speech_panel()
        splitter.addWidget(center)

        # 右栏：已完成发言
        right = self._create_completed_panel()
        splitter.addWidget(right)

        splitter.setSizes([200, 500, 300])
        layout.addWidget(splitter, 1)

        # ═══ 视频面板 ═══
        self._video_panel = VideoPanel()
        self._video_panel._toggle_btn.clicked.connect(self._toggle_video)
        self._video_panel.setVisible(False)
        layout.addWidget(self._video_panel)

        # ═══ 底部提示 ═══
        hint = QLabel("💡 输入自由文本描述你的工作进展，AI 会自动解析为结构化发言")
        hint.setStyleSheet("font-size: 11px; color: #6E6E8E; padding: 4px 0;")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

    def _create_member_panel(self):
        panel = QFrame()
        panel.setStyleSheet("QFrame{background:#161B22;border-radius:8px;}")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        title = QLabel("👥 参会成员")
        title.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(title)

        self.member_list = QListWidget()
        self.member_list.setStyleSheet("QListWidget{border:none;background:transparent;font-size:12px;} QListWidget::item{padding:6px 8px;border-radius:4px;}")
        layout.addWidget(self.member_list, 1)

        self._video_btn = QPushButton("📹 开启视频会议")
        self._video_btn.setStyleSheet("QPushButton{background:transparent;color:#4A90D9;border:1px solid #4A90D9;border-radius:4px;padding:4px;font-size:11px;}")
        self._video_btn.setCursor(Qt.PointingHandCursor)
        self._video_btn.clicked.connect(self._on_toggle_video)
        layout.addWidget(self._video_btn)

        return panel

    def _create_speech_panel(self):
        panel = QFrame()
        panel.setStyleSheet("QFrame{background:#161B22;border-radius:8px;}")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # 当前发言人
        self._speaker_label = QLabel("🎤 等待发言")
        self._speaker_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #4A90D9; padding: 10px; border:2px solid #4A90D9; border-radius:8px;")
        layout.addWidget(self._speaker_label)

        # AI 解析结果预览
        self._ai_preview = QLabel("")
        self._ai_preview.setStyleSheet("font-size: 11px; color: #52C41A; padding: 4px 8px; background:#0D1117; border-radius:4px;")
        self._ai_preview.setWordWrap(True)
        self._ai_preview.setVisible(False)
        layout.addWidget(self._ai_preview)

        # 单输入框
        input_label = QLabel("📝 自由发言")
        input_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #8E8E9E;")
        layout.addWidget(input_label)

        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText("描述你的工作进展，AI 会自动分类为 昨天/今天/阻碍\n如: 昨天修了登录bug，今天做dashboard，需要等review")
        self._text_edit.setStyleSheet("QTextEdit{border-radius:8px;padding:10px;font-size:13px;background:#0D1117;border:1px solid #30363D;}")
        self._text_edit.setMinimumHeight(100)
        layout.addWidget(self._text_edit)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        voice_btn = QPushButton("🎙 语音输入")
        voice_btn.setStyleSheet("QPushButton{background:transparent;color:#F5A623;border:1px solid #F5A623;border-radius:6px;padding:6px 14px;font-size:12px;}")
        voice_btn.setCursor(Qt.PointingHandCursor)
        voice_btn.clicked.connect(self._on_voice_input)
        btn_row.addWidget(voice_btn)

        paste_btn = QPushButton("📋 粘贴")
        paste_btn.setStyleSheet("QPushButton{background:transparent;color:#8E8E9E;border:1px solid #555;border-radius:6px;padding:6px 14px;font-size:12px;}")
        paste_btn.setCursor(Qt.PointingHandCursor)
        paste_btn.clicked.connect(self._on_paste)
        btn_row.addWidget(paste_btn)

        btn_row.addStretch()

        skip_btn = QPushButton("跳过")
        skip_btn.setStyleSheet("QPushButton{background:transparent;color:#8E8E9E;border:1px solid #555;border-radius:6px;padding:6px 14px;font-size:12px;}")
        skip_btn.setCursor(Qt.PointingHandCursor)
        skip_btn.clicked.connect(self._on_skip_speaker)
        btn_row.addWidget(skip_btn)

        self._submit_btn = QPushButton("提交发言 ✨")
        self._submit_btn.setStyleSheet("QPushButton{background:#238636;color:#FFF;border:none;border-radius:6px;padding:8px 20px;font-size:13px;font-weight:bold;} QPushButton:hover{background:#2EA043;}")
        self._submit_btn.setCursor(Qt.PointingHandCursor)
        self._submit_btn.clicked.connect(self._on_submit_speech)
        btn_row.addWidget(self._submit_btn)

        layout.addLayout(btn_row)
        layout.addStretch()
        return panel

    def _create_completed_panel(self):
        panel = QFrame()
        panel.setStyleSheet("QFrame{background:#161B22;border-radius:8px;}")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        title = QLabel("✅ 已完成发言")
        title.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(title)

        self.completed_edit = QTextEdit()
        self.completed_edit.setReadOnly(True)
        self.completed_edit.setStyleSheet("QTextEdit{border:none;background:transparent;font-size:11px;color:#C0C0D0;}")
        layout.addWidget(self.completed_edit, 1)
        return panel

    # ── 数据刷新 ──
    def _refresh_all(self):
        self._refresh_title()
        self._refresh_members()
        self._refresh_completed()
        self._highlight_current_speaker()
        self._video_panel.update_participants(self._members, self._video_users)

    def _refresh_title(self):
        title = self._meeting_data.get("title", "") or f"Sprint#{self._meeting_data.get('sprintNo','?')}"
        self._title_label.setText(f"站会 · {title}")

    def _refresh_members(self):
        self.member_list.clear()
        spoken_ids = {s.get("speaker", {}).get("id", "") for s in self._speeches}
        for i, m in enumerate(self._members):
            uid = m.get("user_id", "")
            name = m.get("displayName") or m.get("display_name") or m.get("username", f"M{i+1}")
            if uid in spoken_ids:
                prefix, suffix = "🟢", "  ✓"
            elif i == self._current_speaker_idx:
                prefix, suffix = "🔵", "  发言中"
            else:
                prefix, suffix = "⚪", ""
            self.member_list.addItem(f"{prefix} {name}{suffix}")

    def _refresh_completed(self):
        lines = []
        for s in self._speeches:
            sp = s.get("speaker", {}) or {}
            name = sp.get("displayName") or sp.get("username", "?")
            y = s.get("yesterday") or ""
            t = s.get("today") or ""
            b = s.get("blockers") or ""
            raw = s.get("rawText") or ""
            lines.append(f"── {name} ──")
            if y: lines.append(f"  昨天: {y[:60]}")
            if t: lines.append(f"  今天: {t[:60]}")
            if b: lines.append(f"  阻碍: {b[:60]}")
            if not y and not t and not b and raw:
                lines.append(f"  {raw[:80]}")
            lines.append("")
        self.completed_edit.setPlainText("\n".join(lines) if lines else "暂无发言")

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

        text = self._text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入发言内容")
            return

        self._submit_btn.setEnabled(False)
        self._submit_btn.setText("AI 解析中...")

        # 使用自由文本端点
        resp = self.api_client.submit_free_speech(
            str(self._meeting_id), text, "TEXT"
        )

        if resp and resp.get("code") == 200:
            data = resp.get("data", {})
            parsed = data.get("parsed", {})
            ai_mode = data.get("aiMode", "rule")
            y, t, b = parsed.get("yesterday", ""), parsed.get("today", ""), parsed.get("blockers", "")
            preview = []
            if y: preview.append(f"昨天: {y[:40]}")
            if t: preview.append(f"今天: {t[:40]}")
            if b: preview.append(f"阻碍: {b[:40]}")
            icon = "🤖" if ai_mode == "llm" else "🔍"
            mode_text = "DeepSeek AI" if ai_mode == "llm" else "智能解析"
            self._ai_preview.setText(f"{icon} {mode_text}: " + " | ".join(preview))
            self._ai_preview.setStyleSheet(
                "font-size: 11px; color: #52C41A; padding: 4px 8px; background:#0D1117; border-radius:4px;"
                if ai_mode == "llm" else
                "font-size: 11px; color: #F5A623; padding: 4px 8px; background:#0D1117; border-radius:4px;"
            )
            self._ai_preview.setVisible(True)

            self._text_edit.clear()
            self._current_speaker_idx += 1
            self._load_meeting_data()
            self._refresh_all()
            self._timer_seconds = self._meeting_data.get("countdownSeconds", 900) if self._meeting_data else 900
            self._timer_label.setText("⏱ 02:00")
        else:
            msg = resp.get("message", "未知错误") if isinstance(resp, dict) else (
                "未连接" if not self.api_client else
                ("不在线" if self.api_client and not self.api_client.online else
                 f"请求异常 (mid={self._meeting_id})"))
            QMessageBox.warning(self, "提交失败", msg)

        self._submit_btn.setEnabled(True)
        self._submit_btn.setText("提交发言 ✨")

    def _on_skip_speaker(self):
        self._current_speaker_idx += 1
        self._ai_preview.setVisible(False)
        self._text_edit.clear()
        self._refresh_all()
        self._timer_seconds = self._meeting_data.get("countdownSeconds", 900) if self._meeting_data else 900
        self._timer_label.setText("⏱ 02:00")

    def _on_voice_input(self):
        QMessageBox.information(self, "语音输入", "语音输入功能将在后续版本中通过浏览器 WebRTC 实现。\n当前请使用文本输入。")

    def _on_paste(self):
        import sys
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self._text_edit.setPlainText(text)

    def _on_toggle_video(self):
        visible = not self._video_panel.isVisible()
        self._video_panel.setVisible(visible)
        self._video_btn.setText("📹 关闭视频会议" if visible else "📹 开启视频会议")
        if visible:
            self._video_panel.update_participants(self._members, self._video_users)

    def _toggle_video(self):
        self._video_panel.setVisible(not self._video_panel.isVisible())

    def _on_end_meeting(self):
        if not self._meeting_id: return
        reply = QMessageBox.question(self, "确认", "确定结束本次站会？", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes: return
        if self.api_client:
            self.api_client.end_meeting(str(self._meeting_id))
        self._timer.stop()
        self.meeting_ended.emit(self._meeting_id)
        self.navigate_back.emit()

    def _on_back(self):
        self._timer.stop()
        self.navigate_back.emit()

    def _tick_timer(self):
        if self._timer_seconds <= 0:
            self._timer.stop()
            self._timer_label.setText("⏱ 超时")
            return
        self._timer_seconds -= 1
        m, s = divmod(self._timer_seconds, 60)
        self._timer_label.setText(f"⏱ {m:02d}:{s:02d}")

    def closeEvent(self, event):
        self._timer.stop()
        super().closeEvent(event)
