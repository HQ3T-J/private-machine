"""站会进行中页面（三栏分屏）- StandupSync"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QFrame, QSizePolicy,
    QMessageBox, QDialog, QMenu, QGridLayout
)
from PySide6.QtGui import QAction, QImage, QPixmap, QPainter
from PySide6.QtCore import Qt, Signal, QTimer, QSize, QThread, QMutex, QWaitCondition
from PySide6.QtGui import QKeyEvent
import cv2
import threading
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from video_client import VideoClientWrapper


class VideoCaptureThread(QThread):
    frame_ready = Signal(QImage)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cap = None
        self._running = False
        self._mutex = QMutex()
        self._condition = QWaitCondition()

    def start_capture(self, camera_index=0):
        self._mutex.lock()
        if not self._running:
            self._cap = cv2.VideoCapture(camera_index)
            self._running = True
            self.start()
        self._mutex.unlock()

    def stop_capture(self):
        self._mutex.lock()
        self._running = False
        self._condition.wakeAll()
        self._mutex.unlock()
        self.wait()
        if self._cap:
            self._cap.release()
            self._cap = None

    def run(self):
        while self._running:
            ret, frame = self._cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.frame_ready.emit(q_image)
            time.sleep(0.033)


class MeetingRoomView(QWidget):
    """站会进行中页面"""

    speech_submitted = Signal(dict)
    meeting_ended = Signal()

    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._meeting_id = None
        self._current_speaker_index = 0
        self._participants = []
        self._completed_speeches = []
        self._is_read_only = False
        self.title = "站会进行中"
        self.setStyleSheet(self._base_style())
        self._setup_ui()
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_timer)
        self._remaining_seconds = 15 * 60  # 15分钟倒计时
        
        self._video_thread = VideoCaptureThread()
        self._video_thread.frame_ready.connect(self._update_video_frame)
        self._camera_on = False
        self._mic_on = True
        self._screen_share_on = False
        
        self._video_client = None
        self._is_online = False
        
        self._is_gallery_layout = True
        self._chat_open = False
        self._is_recording = False
        self._hand_raised = False
        self._chat_messages = []

    def set_meeting_id(self, meeting_id: str, is_read_only: bool = False):
        self._meeting_id = meeting_id
        self._is_read_only = is_read_only
        self._load_meeting_data()

    def _update_read_only_mode(self):
        if self._is_read_only:
            self._title_label.setText(f"← 站会详情")
            self._skip_btn.hide()
            self._paste_btn.hide()
            self._ai_btn.hide()
            self._end_btn.hide()
            self.yesterday_edit.setReadOnly(True)
            self.today_edit.setReadOnly(True)
            self.blocker_edit.setReadOnly(True)
            submit_btn = self.findChild(QPushButton)
            if submit_btn and submit_btn.text() == "提交发言":
                submit_btn.hide()
            self.title = "站会详情"
            self._timer.stop()

    def _base_style(self):
        return """
            QWidget {
                background-color: #1A1A2E;
                color: #E0E0E0;
            }
        """

    def activate(self):
        self._load_meeting_data()
        self._start_timer()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        back_btn = QPushButton("← 返回")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4A9ED9;
                border: 1px solid #4A9ED9;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(74, 144, 217, 0.2);
            }
        """)
        back_btn.clicked.connect(self._on_back)
        top_bar.addWidget(back_btn)
        
        self._title_label = QLabel("站会  ⏱ 00:00")
        self._title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        top_bar.addWidget(self._title_label)
        
        top_bar.addStretch()

        btn_style = """
            QPushButton {
                background-color: #0F3460;
                color: #E0E0E0;
                border: 1px solid #16213E;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1A4A7A;
            }
        """

        self._skip_btn = QPushButton("跳过此人")
        self._skip_btn.setStyleSheet(btn_style)
        self._skip_btn.setCursor(Qt.PointingHandCursor)
        self._skip_btn.clicked.connect(self._on_skip_speaker)
        top_bar.addWidget(self._skip_btn)

        self._paste_btn = QPushButton("粘贴记录")
        self._paste_btn.setStyleSheet(btn_style)
        self._paste_btn.setCursor(Qt.PointingHandCursor)
        self._paste_btn.clicked.connect(self._on_paste_chat)
        top_bar.addWidget(self._paste_btn)

        self._ai_btn = QPushButton("AI 整理")
        self._ai_btn.setStyleSheet(btn_style.replace("#0F3460", "#4A90D9").replace("#1A4A7A", "#5BA0E9"))
        self._ai_btn.setCursor(Qt.PointingHandCursor)
        self._ai_btn.clicked.connect(self._on_ai_analyze)
        top_bar.addWidget(self._ai_btn)

        self._end_btn = QPushButton("结束站会")
        self._end_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        self._end_btn.setCursor(Qt.PointingHandCursor)
        self._end_btn.clicked.connect(self._on_end_meeting)
        top_bar.addWidget(self._end_btn)

        video_bar = QHBoxLayout()
        video_bar.setSpacing(8)
        
        self._camera_btn = QPushButton("📹 开启摄像头")
        self._camera_btn.setStyleSheet("""
            QPushButton {
                background-color: #16213E;
                color: #E0E0E0;
                border: 1px solid #0F3460;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1A4A7A;
            }
            QPushButton#camera_on {
                background-color: #52C41A;
                color: #FFFFFF;
                border-color: #52C41A;
            }
        """)
        self._camera_btn.setCursor(Qt.PointingHandCursor)
        self._camera_btn.clicked.connect(self._on_toggle_camera)
        video_bar.addWidget(self._camera_btn)
        
        self._mic_btn = QPushButton("🎙️ 麦克风")
        self._mic_btn.setStyleSheet("""
            QPushButton {
                background-color: #52C41A;
                color: #FFFFFF;
                border: 1px solid #52C41A;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #43A017;
            }
            QPushButton#mic_off {
                background-color: #E74C3C;
                border-color: #E74C3C;
            }
        """)
        self._mic_btn.setCursor(Qt.PointingHandCursor)
        self._mic_btn.clicked.connect(self._on_toggle_mic)
        video_bar.addWidget(self._mic_btn)
        
        self._screen_share_btn = QPushButton("🖥️ 屏幕共享")
        self._screen_share_btn.setStyleSheet("""
            QPushButton {
                background-color: #16213E;
                color: #E0E0E0;
                border: 1px solid #0F3460;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1A4A7A;
            }
            QPushButton#share_on {
                background-color: #4A90D9;
                color: #FFFFFF;
                border-color: #4A90D9;
            }
        """)
        self._screen_share_btn.setCursor(Qt.PointingHandCursor)
        self._screen_share_btn.clicked.connect(self._on_toggle_screen_share)
        video_bar.addWidget(self._screen_share_btn)
        
        self._online_btn = QPushButton("🟢 开始线上会议")
        self._online_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: #FFFFFF;
                border: 1px solid #27AE60;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ECC71;
            }
            QPushButton#online_on {
                background-color: #E74C3C;
                border-color: #E74C3C;
            }
        """)
        self._online_btn.setCursor(Qt.PointingHandCursor)
        self._online_btn.clicked.connect(self._on_toggle_online_meeting)
        video_bar.addWidget(self._online_btn)
        
        self._layout_btn = QPushButton("📐 画廊视图")
        self._layout_btn.setStyleSheet("""
            QPushButton {
                background-color: #16213E;
                color: #E0E0E0;
                border: 1px solid #0F3460;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1A4A7A;
            }
            QPushButton#layout_presenter {
                background-color: #4A90D9;
                color: #FFFFFF;
                border-color: #4A90D9;
            }
        """)
        self._layout_btn.setCursor(Qt.PointingHandCursor)
        self._layout_btn.clicked.connect(self._on_toggle_layout)
        video_bar.addWidget(self._layout_btn)
        
        self._chat_btn = QPushButton("💬 聊天")
        self._chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #16213E;
                color: #E0E0E0;
                border: 1px solid #0F3460;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1A4A7A;
            }
            QPushButton#chat_open {
                background-color: #4A90D9;
                color: #FFFFFF;
                border-color: #4A90D9;
            }
        """)
        self._chat_btn.setCursor(Qt.PointingHandCursor)
        self._chat_btn.clicked.connect(self._on_toggle_chat)
        video_bar.addWidget(self._chat_btn)
        
        self._record_btn = QPushButton("⏺️ 录制")
        self._record_btn.setStyleSheet("""
            QPushButton {
                background-color: #16213E;
                color: #E0E0E0;
                border: 1px solid #0F3460;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #E74C3C;
            }
            QPushButton#recording {
                background-color: #E74C3C;
                color: #FFFFFF;
                border-color: #E74C3C;
            }
        """)
        self._record_btn.setCursor(Qt.PointingHandCursor)
        self._record_btn.clicked.connect(self._on_toggle_recording)
        video_bar.addWidget(self._record_btn)
        
        self._hand_btn = QPushButton("✋ 举手")
        self._hand_btn.setStyleSheet("""
            QPushButton {
                background-color: #16213E;
                color: #E0E0E0;
                border: 1px solid #0F3460;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #F39C12;
            }
            QPushButton#hand_raised {
                background-color: #F39C12;
                color: #FFFFFF;
                border-color: #F39C12;
            }
        """)
        self._hand_btn.setCursor(Qt.PointingHandCursor)
        self._hand_btn.clicked.connect(self._on_toggle_hand)
        video_bar.addWidget(self._hand_btn)
        
        video_bar.addStretch()
        layout.addLayout(video_bar)

        video_area = QFrame()
        video_area.setStyleSheet("""
            QFrame {
                background-color: #0A0A0F;
                border: 1px solid #0F3460;
                border-radius: 8px;
            }
        """)
        video_layout = QGridLayout(video_area)
        video_layout.setContentsMargins(12, 12, 12, 12)
        video_layout.setSpacing(8)
        
        self._video_labels = []
        for i in range(4):
            video_label = QLabel()
            video_label.setStyleSheet("""
                QLabel {
                    background-color: #16213E;
                    border: 1px solid #0F3460;
                    border-radius: 6px;
                }
            """)
            video_label.setAlignment(Qt.AlignCenter)
            video_label.setMinimumSize(180, 135)
            video_label.setMaximumSize(240, 180)
            video_label.setScaledContents(True)
            
            participant_name = QLabel()
            participant_name.setStyleSheet("font-size: 11px; color: #888888;")
            participant_name.setAlignment(Qt.AlignCenter)
            
            row = i // 2
            col = i % 2
            video_layout.addWidget(video_label, row * 2, col)
            video_layout.addWidget(participant_name, row * 2 + 1, col)
            
            self._video_labels.append((video_label, participant_name))
        
        self._video_labels[0][1].setText("我")
        self._video_labels[1][1].setText("张三")
        self._video_labels[2][1].setText("李四")
        self._video_labels[3][1].setText("王五")
        
        layout.addWidget(video_area)

        three_col = QHBoxLayout()
        three_col.setSpacing(12)

        left_col = self._create_member_list()
        three_col.addWidget(left_col, 1)

        center_col = self._create_speech_area()
        three_col.addWidget(center_col, 2)

        right_col = self._create_completed_area()
        three_col.addWidget(right_col, 1)

        layout.addLayout(three_col, 1)

        hint_label = QLabel("💡 Ctrl+Enter 提交发言")
        hint_label.setStyleSheet("font-size: 12px; color: #888888; padding: 4px 0;")
        hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint_label)

    def _create_member_list(self):
        container = QWidget()
        container.setFixedWidth(210)
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)

        member_label = QLabel("👥 参会成员")
        member_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #CCCCCC;")
        cl.addWidget(member_label)

        self.member_list = QListWidget()
        self.member_list.setStyleSheet("""
            QListWidget {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 8px;
                padding: 6px;
                color: #E0E0E0;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-radius: 4px;
                margin: 2px 0;
                font-size: 13px;
            }
            QListWidget::item:hover {
                background-color: #1A3A5E;
            }
            QListWidget::item:selected {
                background-color: #0F3460;
            }
        """)
        self.member_list.setDragDropMode(QListWidget.InternalMove)
        self.member_list.setDefaultDropAction(Qt.MoveAction)
        self.member_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.member_list.customContextMenuRequested.connect(self._on_member_context_menu)
        cl.addWidget(self.member_list, 1)

        self._sort_mode = False
        self._sort_btn = QPushButton("🔄 拖拽排序")
        self._sort_btn.setStyleSheet("""
            QPushButton {
                background-color: #16213E;
                color: #AAAAAA;
                border: 1px solid #0F3460;
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
            QPushButton:hover, QPushButton#sort_active {
                color: #4A9ED9;
                border-color: #4A9ED9;
            }
        """)
        self._sort_btn.setCursor(Qt.PointingHandCursor)
        self._sort_btn.clicked.connect(self._toggle_sort_mode)
        cl.addWidget(self._sort_btn)

        return container

    def _create_speech_area(self):
        container = QWidget()
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(10)

        self._speaker_label = QLabel("🎤 正在等待发言")
        self._speaker_label.setStyleSheet("""
            font-size: 16px; font-weight: bold; color: #4A90D9;
            padding: 12px;
            background-color: #16213E;
            border: 2px solid #4A90D9;
            border-radius: 8px;
        """)
        cl.addWidget(self._speaker_label)

        yesterday_label = QLabel("✅ 昨天")
        yesterday_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #AAAAAA;")
        cl.addWidget(yesterday_label)

        self.yesterday_edit = QTextEdit()
        self.yesterday_edit.setPlaceholderText("完成了登录模块重构...")
        self.yesterday_edit.setStyleSheet("""
            QTextEdit {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 6px;
                padding: 8px;
                color: #E0E0E0;
                font-size: 13px;
            }
            QTextEdit:focus {
                border-color: #4A90D9;
            }
        """)
        self.yesterday_edit.setMaximumHeight(80)
        cl.addWidget(self.yesterday_edit)

        today_label = QLabel("📋 今天")
        today_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #AAAAAA;")
        cl.addWidget(today_label)

        self.today_edit = QTextEdit()
        self.today_edit.setPlaceholderText("开始做权限管理模块...")
        self.today_edit.setStyleSheet("""
            QTextEdit {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 6px;
                padding: 8px;
                color: #E0E0E0;
                font-size: 13px;
            }
            QTextEdit:focus {
                border-color: #4A90D9;
            }
        """)
        self.today_edit.setMaximumHeight(80)
        cl.addWidget(self.today_edit)

        blocker_label = QLabel("🚧 阻碍")
        blocker_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #AAAAAA;")
        cl.addWidget(blocker_label)

        self.blocker_edit = QTextEdit()
        self.blocker_edit.setPlaceholderText("空")
        self.blocker_edit.setStyleSheet("""
            QTextEdit {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 6px;
                padding: 8px;
                color: #E0E0E0;
                font-size: 13px;
            }
            QTextEdit:focus {
                border-color: #4A90D9;
            }
        """)
        self.blocker_edit.setMaximumHeight(60)
        cl.addWidget(self.blocker_edit)

        submit_btn = QPushButton("提交发言")
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90D9;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5BA0E9;
            }
        """)
        submit_btn.setCursor(Qt.PointingHandCursor)
        submit_btn.clicked.connect(self._on_submit_speech)
        cl.addWidget(submit_btn)

        cl.addStretch()
        return container

    def _create_completed_area(self):
        container = QWidget()
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)

        completed_label = QLabel("✅ 已完成发言")
        completed_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #CCCCCC;")
        cl.addWidget(completed_label)

        self.completed_edit = QTextEdit()
        self.completed_edit.setReadOnly(True)
        self.completed_edit.setStyleSheet("""
            QTextEdit {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 8px;
                padding: 10px;
                color: #AAAAAA;
                font-size: 12px;
            }
        """)
        cl.addWidget(self.completed_edit, 1)

        return container

    def _load_meeting_data(self):
        if self._meeting_id and self.api_client:
            try:
                meeting = self.api_client.get_meeting(self._meeting_id)
                self._participants = meeting.get("participants", [])
                self._title_label.setText(f"← {meeting.get('title', '站会')}  ⏱ 00:00")
            except Exception as e:
                print(f"Failed to load meeting: {e}")
                self._participants = [
                    {"user_id": "1", "display_name": "张三", "has_spoken": False},
                    {"user_id": "2", "display_name": "李四", "has_spoken": False},
                    {"user_id": "3", "display_name": "王五", "has_spoken": False},
                    {"user_id": "4", "display_name": "赵六", "has_spoken": False},
                    {"user_id": "5", "display_name": "钱七", "has_spoken": False},
                ]
        else:
            self._participants = [
                {"user_id": "1", "display_name": "张三", "has_spoken": False},
                {"user_id": "2", "display_name": "李四", "has_spoken": False},
                {"user_id": "3", "display_name": "王五", "has_spoken": False},
                {"user_id": "4", "display_name": "赵六", "has_spoken": False},
                {"user_id": "5", "display_name": "钱七", "has_spoken": False},
            ]
        
        self._refresh_member_list()
        self._update_current_speaker()
        
        if self._is_read_only:
            self._load_historical_speeches()
            self._update_read_only_mode()

    def _refresh_member_list(self):
        self.member_list.clear()
        for idx, participant in enumerate(self._participants):
            has_spoken = participant.get("has_spoken", False)
            is_current = idx == self._current_speaker_index and not has_spoken
            
            if has_spoken:
                status_icon = "🟢"
                status_text = "已发言"
                bg_color = "#1E3A5F"
                font_weight = "normal"
            elif is_current:
                status_icon = "🔵"
                status_text = "发言中"
                bg_color = "#4A9ED9"
                font_weight = "bold"
            else:
                status_icon = "⚪"
                status_text = "等待中"
                bg_color = "transparent"
                font_weight = "normal"
            
            item_text = f"{status_icon} {participant.get('display_name', '')}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, participant.get("user_id"))
            item.setData(Qt.UserRole + 1, idx)
            
            if is_current:
                item.setSizeHint(QSize(0, 40))
                item.setToolTip(f"🎤 {participant.get('display_name')} 正在发言")
            else:
                item.setSizeHint(QSize(0, 32))
                item.setToolTip(status_text)
            
            self.member_list.addItem(item)
            self._update_item_style(idx, is_current, has_spoken)

    def _update_item_style(self, idx, is_current, has_spoken):
        item = self.member_list.item(idx)
        if item:
            if is_current:
                item.setText(f"<b>{item.text()}</b>")
            elif has_spoken:
                item.setText(f"<span style='color:#52C41A'>{item.text()}</span>")
            else:
                item.setText(f"<span style='color:#8E8E9E'>{item.text()}</span>")

    def _toggle_sort_mode(self):
        self._sort_mode = not self._sort_mode
        if self._sort_mode:
            self._sort_btn.setText("✅ 排序中")
            self._sort_btn.setObjectName("sort_active")
            self.member_list.setSelectionMode(QListWidget.SingleSelection)
            QMessageBox.information(self, "提示", "拖拽成员列表调整发言顺序")
        else:
            self._sort_btn.setText("🔄 拖拽排序")
            self._sort_btn.setObjectName("")
            self.member_list.setSelectionMode(QListWidget.NoSelection)
            self._save_speaker_order()

    def _save_speaker_order(self):
        new_order = []
        for i in range(self.member_list.count()):
            item = self.member_list.item(i)
            user_id = item.data(Qt.UserRole)
            original_idx = item.data(Qt.UserRole + 1)
            new_order.append({
                "user_id": user_id,
                "original_index": original_idx,
                "new_index": i
            })
        
        self._participants.sort(key=lambda p: next((o["new_index"] for o in new_order if o["user_id"] == p.get("user_id")), 0))
        
        if self.api_client and self._meeting_id:
            try:
                participant_ids = [p["user_id"] for p in self._participants]
                self.api_client.update_meeting_participants(self._meeting_id, participant_ids)
            except Exception as e:
                print(f"Failed to update speaker order: {e}")

    def _on_member_context_menu(self, pos):
        item = self.member_list.itemAt(pos)
        if not item:
            return
        
        menu = QMenu(self)
        
        user_id = item.data(Qt.UserRole)
        idx = item.data(Qt.UserRole + 1)
        participant = next((p for p in self._participants if p.get("user_id") == user_id), None)
        
        if participant and not participant.get("has_spoken"):
            act_skip = QAction("跳过此人", menu)
            act_skip.triggered.connect(lambda: self._skip_specific_member(user_id))
            menu.addAction(act_skip)
            
            if participant.get("has_spoken"):
                act_insert = QAction("重新插入发言", menu)
                act_insert.triggered.connect(lambda: self._reinsert_member(user_id))
                menu.addAction(act_insert)
        
        menu.exec(self.member_list.mapToGlobal(pos))

    def _skip_specific_member(self, user_id):
        participant = next((p for p in self._participants if p.get("user_id") == user_id), None)
        if participant and not participant.get("has_spoken"):
            participant["has_spoken"] = True
            self._refresh_member_list()
            self._update_current_speaker()
            QMessageBox.information(self, "提示", f"{participant.get('display_name')} 已跳过")

    def _reinsert_member(self, user_id):
        participant = next((p for p in self._participants if p.get("user_id") == user_id), None)
        if participant and participant.get("has_spoken"):
            participant["has_spoken"] = False
            self._refresh_member_list()
            QMessageBox.information(self, "提示", f"{participant.get('display_name')} 已重新插入")

    def _update_current_speaker(self):
        if self._participants:
            current = None
            for idx, p in enumerate(self._participants):
                if not p.get("has_spoken"):
                    current = p
                    self._current_speaker_index = idx
                    break
            
            if current:
                self._speaker_label.setText(f"🎤 {current.get('display_name', '')} 正在发言")
            else:
                self._speaker_label.setText("🎉 所有成员已完成发言")
                self._skip_btn.setEnabled(False)
        else:
            self._speaker_label.setText("🎤 正在等待发言")

    def _load_historical_speeches(self):
        if self._meeting_id and self.api_client:
            try:
                speeches = self.api_client.get_speeches(self._meeting_id)
                for speech in speeches:
                    self._completed_speeches.append({
                        "speaker": speech.get("display_name", speech.get("speaker_name", "Unknown")),
                        "yesterday": speech.get("yesterday", ""),
                        "today": speech.get("today", ""),
                        "blockers": speech.get("blockers", "")
                    })
                self._update_completed_area()
            except Exception as e:
                print(f"Failed to load historical speeches: {e}")

    def _start_timer(self):
        self._remaining_seconds = 15 * 60
        self._timer.start(1000)

    def _update_timer(self):
        if self._remaining_seconds > 0:
            self._remaining_seconds -= 1
        
        minutes = self._remaining_seconds // 60
        seconds = self._remaining_seconds % 60
        
        if self._remaining_seconds <= 0:
            self._timer.stop()
            self._on_timeout()
            return
        
        if self._remaining_seconds <= 2 * 60:
            self._title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #E74C3C;")
            timer_display = f"⚠️ {minutes:02d}:{seconds:02d}"
        else:
            self._title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
            timer_display = f"{minutes:02d}:{seconds:02d}"
        
        title_text = f"← 站会  ⏱ {timer_display}"
        self._title_label.setText(title_text)

    def _on_back(self):
        """返回首页"""
        self.meeting_ended.emit()

    def _on_timeout(self):
        reply = QMessageBox.question(
            self, "⏰ 站会超时", 
            "站会时间已到！是否延长5分钟？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._remaining_seconds = 5 * 60
            self._timer.start(1000)
            QMessageBox.information(self, "提示", "站会延长5分钟")
        else:
            self._on_end_meeting()

    def _on_submit_speech(self):
        yesterday = self.yesterday_edit.toPlainText().strip()
        today = self.today_edit.toPlainText().strip()
        blockers = self.blocker_edit.toPlainText().strip()

        if not yesterday and not today:
            QMessageBox.warning(self, "警告", "请至少填写昨天或今天的内容")
            return

        if self._meeting_id and self.api_client:
            try:
                result = self.api_client.submit_speech(
                    self._meeting_id, yesterday, today, blockers
                )
                if result.get("success"):
                    self._mark_as_spoken()
                    QMessageBox.information(self, "成功", "发言提交成功")
                else:
                    QMessageBox.warning(self, "失败", result.get("error", "提交失败"))
            except Exception as e:
                QMessageBox.warning(self, "失败", f"提交发言失败: {str(e)}")
        else:
            self._mark_as_spoken()
            QMessageBox.information(self, "成功", "发言提交成功（模拟）")

    def _mark_as_spoken(self):
        if self._current_speaker_index < len(self._participants):
            participant = self._participants[self._current_speaker_index]
            participant["has_spoken"] = True
            
            speaker_name = participant.get("display_name", "")
            self._completed_speeches.append({
                "speaker": speaker_name,
                "yesterday": self.yesterday_edit.toPlainText(),
                "today": self.today_edit.toPlainText(),
                "blockers": self.blocker_edit.toPlainText()
            })
            
            self._update_completed_area()
            self.yesterday_edit.clear()
            self.today_edit.clear()
            self.blocker_edit.clear()
            
            self._refresh_member_list()
            self._update_current_speaker()

    def _update_completed_area(self):
        text = ""
        for speech in self._completed_speeches:
            text += f"{speech['speaker']} ✅\n"
            if speech['yesterday']:
                text += f"  昨天：{speech['yesterday']}\n"
            if speech['today']:
                text += f"  今天：{speech['today']}\n"
            blockers_text = speech['blockers'] if speech['blockers'] else "无"
            text += f"  阻碍：{blockers_text}\n\n"
        self.completed_edit.setPlainText(text)

    def _on_skip_speaker(self):
        if self._current_speaker_index < len(self._participants):
            participant = self._participants[self._current_speaker_index]
            if self._meeting_id and self.api_client:
                try:
                    result = self.api_client.skip_speaker(self._meeting_id, participant.get("user_id"))
                    if result.get("success"):
                        self._mark_as_spoken()
                    else:
                        QMessageBox.warning(self, "失败", result.get("error", "操作失败"))
                except Exception as e:
                    QMessageBox.warning(self, "失败", f"跳过失败: {str(e)}")
            else:
                self._mark_as_spoken()

    def _on_paste_chat(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("粘贴聊天记录")
        dialog.setFixedSize(450, 300)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1A1A2E;
            }
            QLabel {
                color: #E0E0E0;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(QLabel("粘贴聊天记录（格式：姓名: 内容）:"))
        
        chat_edit = QTextEdit()
        chat_edit.setPlaceholderText("张三: 昨天完成了登录模块，今天做权限管理\n李四: 昨天做了后端联调")
        chat_edit.setStyleSheet("""
            QTextEdit {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 6px;
                padding: 8px;
                color: #E0E0E0;
                font-size: 13px;
            }
        """)
        layout.addWidget(chat_edit)

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

        parse_btn = QPushButton("解析")
        parse_btn.clicked.connect(lambda: self._parse_chat(dialog, chat_edit.toPlainText()))
        parse_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90D9;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 13px;
            }
        """)
        btn_layout.addWidget(parse_btn)
        layout.addLayout(btn_layout)

        dialog.exec()

    def _parse_chat(self, dialog, chat_text):
        if self._meeting_id and self.api_client:
            try:
                result = self.api_client.parse_chat(self._meeting_id, chat_text)
                speeches = result.get("speeches", [])
                QMessageBox.information(self, "成功", f"解析出 {len(speeches)} 条发言")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"解析失败: {str(e)}")
        else:
            lines = chat_text.split('\n')
            count = sum(1 for line in lines if ':' in line)
            QMessageBox.information(self, "成功", f"解析出 {count} 条发言（模拟）")
        dialog.close()

    def _on_ai_analyze(self):
        if self._meeting_id and self.api_client:
            try:
                result = self.api_client.analyze_meeting(self._meeting_id)
                if result.get("success"):
                    QMessageBox.information(self, "成功", "AI分析完成")
                else:
                    QMessageBox.warning(self, "失败", "AI分析失败")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"AI分析失败: {str(e)}")
        else:
            QMessageBox.information(self, "成功", "AI分析完成（模拟）")

    def _on_end_meeting(self):
        reply = QMessageBox.question(
            self, "确认结束", "确定要结束本次站会吗？\n\n系统将自动进行AI分析并生成待办事项",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._timer.stop()
            
            ai_result = self._perform_ai_summary()
            
            confirm_reply = QMessageBox.question(
                self, "AI纪要确认", 
                f"AI已完成站会纪要分析\n\n待办事项数: {ai_result.get('action_items_count', 0)}\n需要归档站会吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            
            if confirm_reply == QMessageBox.Yes:
                if self._meeting_id and self.api_client:
                    try:
                        result = self.api_client.end_meeting(self._meeting_id)
                        if result.get("success"):
                            QMessageBox.information(self, "成功", "站会已结束，纪要已归档，待办已分发")
                            self.meeting_ended.emit()
                        else:
                            QMessageBox.warning(self, "失败", result.get("error", "结束失败"))
                    except Exception as e:
                        QMessageBox.warning(self, "失败", f"结束站会失败: {str(e)}")
                else:
                    QMessageBox.information(self, "成功", "站会已结束，纪要已归档，待办已分发（模拟）")
                    self.meeting_ended.emit()

    def _perform_ai_summary(self):
        if self._meeting_id and self.api_client:
            try:
                result = self.api_client.analyze_meeting(self._meeting_id)
                if result.get("success"):
                    data = result.get("data", {})
                    return {
                        "action_items_count": len(data.get("action_items", [])),
                        "summary": data.get("summary", "")
                    }
            except Exception as e:
                print(f"AI summary failed: {e}")
        
        return {"action_items_count": len(self._completed_speeches), "summary": ""}

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Return and event.modifiers() & Qt.ControlModifier:
            self._on_submit_speech()
        else:
            super().keyPressEvent(event)

    def _on_toggle_camera(self):
        self._camera_on = not self._camera_on
        if self._camera_on:
            self._camera_btn.setText("📹 关闭摄像头")
            self._camera_btn.setObjectName("camera_on")
            try:
                self._video_thread.start_capture(0)
                if self._is_online and self._meeting_id:
                    self._start_video_stream()
            except Exception as e:
                QMessageBox.warning(self, "警告", f"无法打开摄像头: {str(e)}")
                self._camera_on = False
                self._camera_btn.setText("📹 开启摄像头")
                self._camera_btn.setObjectName("")
        else:
            self._camera_btn.setText("📹 开启摄像头")
            self._camera_btn.setObjectName("")
            self._video_thread.stop_capture()
            self._stop_video_stream()
            self._video_labels[0][0].clear()
            self._video_labels[0][0].setText("📷 摄像头已关闭")

    def _on_toggle_mic(self):
        self._mic_on = not self._mic_on
        if self._mic_on:
            self._mic_btn.setText("🎙️ 麦克风")
            self._mic_btn.setObjectName("")
            QMessageBox.information(self, "提示", "麦克风已开启")
        else:
            self._mic_btn.setText("🔇 麦克风已静音")
            self._mic_btn.setObjectName("mic_off")
            QMessageBox.information(self, "提示", "麦克风已静音")

    def _on_toggle_screen_share(self):
        self._screen_share_on = not self._screen_share_on
        if self._screen_share_on:
            self._screen_share_btn.setText("🖥️ 停止共享")
            self._screen_share_btn.setObjectName("share_on")
            QMessageBox.information(self, "提示", "屏幕共享已开启（模拟）")
        else:
            self._screen_share_btn.setText("🖥️ 屏幕共享")
            self._screen_share_btn.setObjectName("")
            QMessageBox.information(self, "提示", "屏幕共享已停止")

    def _on_toggle_online_meeting(self):
        self._is_online = not self._is_online
        if self._is_online:
            self._online_btn.setText("🔴 结束线上会议")
            self._online_btn.setObjectName("online_on")
            self._start_online_meeting()
        else:
            self._online_btn.setText("🟢 开始线上会议")
            self._online_btn.setObjectName("")
            self._stop_online_meeting()

    def _start_online_meeting(self):
        if self._meeting_id:
            try:
                self._video_client = VideoClientWrapper(self._meeting_id)
                self._video_client.frame_received.connect(self._on_remote_frame)
                self._video_client.peer_count_changed.connect(self._on_peer_count_changed)
                self._video_client.connected.connect(self._on_video_connected)
                self._video_client.disconnected.connect(self._on_video_disconnected)
                self._video_client.start()
            except Exception as e:
                QMessageBox.warning(self, "警告", f"无法连接视频服务器: {str(e)}")
                self._is_online = False
                self._online_btn.setText("🟢 开始线上会议")

    def _stop_online_meeting(self):
        if self._video_client:
            self._video_client.stop()
            self._video_client = None
            for i in range(1, len(self._video_labels)):
                self._video_labels[i][0].clear()
                self._video_labels[i][0].setText(f"参会者 {i}")

    def _start_video_stream(self):
        pass

    def _stop_video_stream(self):
        pass

    def _on_remote_frame(self, peer_index, frame_data):
        if peer_index < len(self._video_labels) - 1:
            try:
                pixmap = QPixmap()
                pixmap.loadFromData(frame_data)
                self._video_labels[peer_index + 1][0].setPixmap(pixmap)
            except Exception as e:
                print(f"Failed to display remote frame: {e}")

    def _on_peer_count_changed(self, count):
        QMessageBox.information(self, "提示", f"当前在线人数: {count}")

    def _on_video_connected(self):
        QMessageBox.information(self, "成功", "已连接到视频会议服务器")

    def _on_video_disconnected(self):
        QMessageBox.warning(self, "警告", "视频连接已断开")
        self._is_online = False
        if self._online_btn:
            self._online_btn.setText("🟢 开始线上会议")
            self._online_btn.setObjectName("")

    def _update_video_frame(self, frame):
        if self._camera_on and self._video_labels:
            pixmap = QPixmap.fromImage(frame)
            self._video_labels[0][0].setPixmap(pixmap)

    def _on_toggle_layout(self):
        self._is_gallery_layout = not self._is_gallery_layout
        if self._is_gallery_layout:
            self._layout_btn.setText("📐 画廊视图")
            self._layout_btn.setObjectName("")
            QMessageBox.information(self, "提示", "已切换到画廊视图")
        else:
            self._layout_btn.setText("👤 演讲者视图")
            self._layout_btn.setObjectName("layout_presenter")
            QMessageBox.information(self, "提示", "已切换到演讲者视图")

    def _on_toggle_chat(self):
        self._chat_open = not self._chat_open
        if self._chat_open:
            self._chat_btn.setText("💬 关闭聊天")
            self._chat_btn.setObjectName("chat_open")
            self._show_chat_dialog()
        else:
            self._chat_btn.setText("💬 聊天")
            self._chat_btn.setObjectName("")

    def _show_chat_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("会议聊天")
        dialog.setMinimumSize(400, 400)
        layout = QVBoxLayout(dialog)
        
        self._chat_list = QListWidget()
        self._chat_list.setStyleSheet("""
            QListWidget {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 6px;
                color: #E0E0E0;
            }
        """)
        layout.addWidget(self._chat_list)
        
        chat_input = QLineEdit()
        chat_input.setPlaceholderText("输入消息...")
        chat_input.setStyleSheet("""
            QLineEdit {
                background-color: #16213E;
                border: 1px solid #0F3460;
                border-radius: 4px;
                padding: 6px;
                color: #E0E0E0;
            }
        """)
        layout.addWidget(chat_input)
        
        send_btn = QPushButton("发送")
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90D9;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
            }
        """)
        send_btn.clicked.connect(lambda: self._send_chat_message(chat_input.text(), dialog))
        layout.addWidget(send_btn)
        
        dialog.exec()

    def _send_chat_message(self, message, dialog):
        if message.strip():
            self._chat_messages.append({"user": "我", "message": message, "time": time.strftime("%H:%M")})
            self._chat_list.addItem(f"[{time.strftime('%H:%M')}] 我: {message}")
            dialog.findChild(QLineEdit).clear()
            self._chat_list.scrollToBottom()

    def _on_toggle_recording(self):
        self._is_recording = not self._is_recording
        if self._is_recording:
            self._record_btn.setText("⏹️ 停止录制")
            self._record_btn.setObjectName("recording")
            QMessageBox.information(self, "提示", "会议录制已开始")
        else:
            self._record_btn.setText("⏺️ 录制")
            self._record_btn.setObjectName("")
            QMessageBox.information(self, "提示", "会议录制已停止")

    def _on_toggle_hand(self):
        self._hand_raised = not self._hand_raised
        if self._hand_raised:
            self._hand_btn.setText("✋ 放下手")
            self._hand_btn.setObjectName("hand_raised")
            QMessageBox.information(self, "提示", "已举手")
        else:
            self._hand_btn.setText("✋ 举手")
            self._hand_btn.setObjectName("")
            QMessageBox.information(self, "提示", "已放下手")

    def closeEvent(self, event):
        self._video_thread.stop_capture()
        self._stop_online_meeting()
        super().closeEvent(event)
