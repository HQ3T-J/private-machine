"""StandupSync - Team Standup Meeting Tool with Video Conferencing"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QTableWidget, 
    QTableWidgetItem, QHeaderView, QDialog, QLineEdit, QComboBox,
    QMessageBox, QTextEdit, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtMultimedia import QMediaCaptureSession, QCamera
from datetime import datetime
from PySide6.QtMultimediaWidgets import QVideoWidget
import pyaudio
import numpy as np

DARK_STYLE = """
QWidget { background-color: #0D1117; color: #C9D1D9; }
QPushButton { background-color: #238636; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-size: 13px; }
QPushButton:hover { background-color: #2EA043; }
QComboBox { background-color: #161B22; color: #C9D1D9; border: 1px solid #30363D; border-radius: 6px; padding: 8px; }
QTableWidget { background-color: #161B22; border: 1px solid #30363D; border-radius: 6px; }
QHeaderView::section { background-color: #21262D; color: #8B949E; padding: 8px; border: none; }
QDialog { background-color: #161B22; }
QTextEdit { background-color: #161B22; color: #C9D1D9; border: 1px solid #30363D; border-radius: 6px; }
QListWidget { background-color: #161B22; border: 1px solid #30363D; border-radius: 6px; }
QVideoWidget { background-color: #161B22; }
"""

class AudioThread(QThread):
    volume_changed = Signal(float)
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._running = False
        self._pyaudio = None
        self._stream = None
        self._chunk_size = 512
        self._sample_rate = 44100
        self._input_device_index = None
        self._device_sample_rate = 44100
    
    def _find_working_microphone(self):
        pa = pyaudio.PyAudio()
        best_device = None
        best_amplitude = 0
        best_sample_rate = 44100
        
        for i in range(pa.get_device_count()):
            dev = pa.get_device_info_by_index(i)
            if dev['maxInputChannels'] <= 0:
                continue
            
            stream = None
            try:
                sample_rate = int(dev['defaultSampleRate'])
                stream = pa.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    input=True,
                    input_device_index=i,
                    frames_per_buffer=512
                )
                
                total_amp = 0
                for _ in range(5):
                    data = stream.read(512, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    total_amp += np.mean(np.abs(audio_data))
                
                stream.close()
                mean_amp = total_amp / 5
                
                print(f"Device {i}: {dev['name']}, amp={mean_amp:.2f}, rate={sample_rate}")
                
                if mean_amp > best_amplitude and mean_amp > 10:
                    best_amplitude = mean_amp
                    best_device = i
                    best_sample_rate = sample_rate
                    
            except Exception as e:
                print(f"Device {i}: {dev['name']} - error: {e}")
                if stream:
                    stream.close()
        
        pa.terminate()
        self._device_sample_rate = best_sample_rate
        return best_device
    
    def run(self):
        try:
            self._pyaudio = pyaudio.PyAudio()
            
            self._input_device_index = self._find_working_microphone()
            self._sample_rate = self._device_sample_rate
            
            if self._input_device_index is not None:
                device_info = self._pyaudio.get_device_info_by_index(self._input_device_index)
                print(f"Using device {self._input_device_index}: {device_info['name']} @ {self._sample_rate}Hz")
            else:
                device_info = self._pyaudio.get_default_input_device_info()
                self._input_device_index = device_info.get('index', 0)
                self._sample_rate = int(device_info.get('defaultSampleRate', 44100))
                print(f"Using default device {self._input_device_index}: {device_info['name']} @ {self._sample_rate}Hz")
            
            channels = 1
            
            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=self._sample_rate,
                input=True,
                input_device_index=self._input_device_index,
                frames_per_buffer=self._chunk_size
            )
            
            self._running = True
            self._smoothed_volume = 0.0
            
            while self._running:
                try:
                    data = self._stream.read(self._chunk_size, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    
                    raw_volume = np.mean(np.abs(audio_data))
                    
                    if raw_volume < 10:
                        target = 0.0
                    elif raw_volume < 200:
                        target = raw_volume / 200.0 * 0.5
                    elif raw_volume < 1000:
                        target = 0.5 + (raw_volume - 200) / 800.0 * 0.4
                    else:
                        target = min(1.0, 0.9 + (raw_volume - 1000) / 5000.0)
                    
                    self._smoothed_volume = self._smoothed_volume * 0.7 + target * 0.3
                    
                    print(f"Raw: {raw_volume:.2f}, Target: {target:.3f}, Smoothed: {self._smoothed_volume:.3f}")
                    
                    self.volume_changed.emit(self._smoothed_volume)
                except Exception as e:
                    if self._running:
                        self.error_occurred.emit(f"读取音频数据失败: {str(e)}")
                    break
                    
        except Exception as e:
            self.error_occurred.emit(f"麦克风初始化失败: {str(e)}")
        finally:
            self._cleanup()
    
    def stop(self):
        self._running = False
        self.wait(3000)
    
    def _cleanup(self):
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except:
                pass
            self._stream = None
        if self._pyaudio:
            try:
                self._pyaudio.terminate()
            except:
                pass
            self._pyaudio = None

class MockAPIClient:
    def __init__(self):
        self._teams = [{"id": "1", "name": "核心开发组", "role": "tech_lead"}]
        self._team_members = {
            "1": [
                {"id": "1", "name": "张三", "role": "Tech Lead", "attendance": 0.95, "completion": 0.92},
                {"id": "2", "name": "李四", "role": "Scrum Master", "attendance": 0.88, "completion": 0.75},
                {"id": "3", "name": "王五", "role": "Developer", "attendance": 0.90, "completion": 0.60},
                {"id": "4", "name": "赵六", "role": "Developer", "attendance": 0.72, "completion": 0.45},
            ]
        }
        self._meetings = []
    
    def get_teams(self): return self._teams
    def get_team_members(self, team_id): return self._team_members.get(team_id, [])
    def create_team(self, name):
        new_id = str(len(self._teams) + 1)
        self._teams.append({"id": new_id, "name": name, "role": "tech_lead"})
        self._team_members[new_id] = [{"id": "1", "name": "张三", "role": "Tech Lead", "attendance": 1.0, "completion": 1.0}]
        return {"success": True, "team": {"id": new_id, "name": name}}
    
    def delete_team(self, team_id):
        self._teams = [t for t in self._teams if t["id"] != team_id]
        self._team_members.pop(team_id, None)
        self._meetings = [m for m in self._meetings if m["team_id"] != team_id]
        return {"success": True}
    
    def add_member(self, team_id, name, role="Developer"):
        members = self._team_members.get(team_id, [])
        new_id = str(len(members) + 1)
        members.append({"id": new_id, "name": name, "role": role, "attendance": 1.0, "completion": 0.0})
        return {"success": True}
    
    def remove_member(self, team_id, member_id):
        members = self._team_members.get(team_id, [])
        self._team_members[team_id] = [m for m in members if m["id"] != member_id]
        return {"success": True}
    
    def update_member_role(self, team_id, member_id, new_role):
        for m in self._team_members.get(team_id, []):
            if m["id"] == member_id:
                m["role"] = new_role
        return {"success": True}
    
    def get_meetings(self, team_id=None):
        if team_id:
            return [m for m in self._meetings if m["team_id"] == team_id]
        return self._meetings
    
    def create_meeting(self, team_id, title, **kwargs):
        new_id = str(len(self._meetings) + 1)
        self._meetings.append({
            "id": new_id, "team_id": team_id, "date": datetime.now().strftime("%Y-%m-%d"), 
            "sprint": kwargs.get("sprint_no", ""), "title": title, 
            "status": "created", "attendance": "0/4", "completion": "0%", "blockers": 0,
            "participants": [m["id"] for m in self._team_members.get(team_id, [])]
        })
        return {"success": True, "meeting": {"id": new_id, "title": title}}
    
    def start_meeting(self, meeting_id):
        for m in self._meetings:
            if m["id"] == meeting_id:
                m["status"] = "active"
        return {"success": True}
    
    def delete_meeting(self, meeting_id):
        self._meetings = [m for m in self._meetings if m["id"] != meeting_id]
        return {"success": True}

class MeetingRoomPage(QWidget):
    meeting_ended = Signal()
    
    def __init__(self, api_client, meeting, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.meeting = meeting
        self._camera_on = False
        self._mic_on = False
        self._camera = None
        self._capture_session = None
        self._audio_thread = AudioThread()
        self._audio_thread.volume_changed.connect(self._on_volume_changed)
        self._audio_thread.error_occurred.connect(self._on_audio_error)
        self._current_volume = 0
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        top_bar = QHBoxLayout()
        self.meeting_title = QLabel(f"<h2>{self.meeting['title']}</h2>")
        top_bar.addWidget(self.meeting_title)
        top_bar.addStretch()
        
        self.countdown_label = QLabel("15:00")
        self.countdown_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #58A6FF;")
        top_bar.addWidget(self.countdown_label)
        layout.addLayout(top_bar)
        
        main_content = QHBoxLayout()
        
        video_area = QVBoxLayout()
        self.video_container = QWidget()
        self.video_container.setStyleSheet("background-color: #161B22; border: 2px solid #30363D; border-radius: 12px;")
        self.video_container.setFixedSize(640, 480)
        self.video_layout = QGridLayout(self.video_container)
        self.video_layout.setContentsMargins(8, 8, 8, 8)
        self.video_layout.setSpacing(6)
        
        self._video_slots = []
        
        self._setup_video_grid()
        
        self._show_video_placeholder()
        
        video_area.addWidget(self.video_container)
        
        participants_layout = QVBoxLayout()
        participants_label = QLabel("<h3>参会成员</h3>")
        participants_layout.addWidget(participants_label)
        
        self.participants_list = QListWidget()
        self.participants_list.setFixedHeight(150)
        members = self.api_client.get_team_members(self.meeting["team_id"])
        for m in members:
            item = QListWidgetItem(f"🟢 {m['name']} - {m['role']}")
            item.setForeground(Qt.GlobalColor.green)
            self.participants_list.addItem(item)
        participants_layout.addWidget(self.participants_list)
        video_area.addLayout(participants_layout)
        main_content.addLayout(video_area)
        
        right_panel = QVBoxLayout()
        
        speech_area = QVBoxLayout()
        speech_label = QLabel("<h3>站会发言</h3>")
        speech_area.addWidget(speech_label)
        
        self.yesterday_edit = QTextEdit()
        self.yesterday_edit.setPlaceholderText("昨天完成了什么...")
        self.yesterday_edit.setFixedHeight(80)
        speech_area.addWidget(QLabel("✅ 昨日完成:"))
        speech_area.addWidget(self.yesterday_edit)
        
        self.today_edit = QTextEdit()
        self.today_edit.setPlaceholderText("今天计划做什么...")
        self.today_edit.setFixedHeight(80)
        speech_area.addWidget(QLabel("📋 今日计划:"))
        speech_area.addWidget(self.today_edit)
        
        self.blockers_edit = QTextEdit()
        self.blockers_edit.setPlaceholderText("遇到什么阻碍...")
        self.blockers_edit.setFixedHeight(80)
        speech_area.addWidget(QLabel("🚧 遇到阻碍:"))
        speech_area.addWidget(self.blockers_edit)
        
        self.submit_btn = QPushButton("提交发言")
        self.submit_btn.clicked.connect(self._on_submit_speech)
        speech_area.addWidget(self.submit_btn)
        right_panel.addLayout(speech_area)
        
        chat_area = QVBoxLayout()
        chat_label = QLabel("<h3>会议聊天</h3>")
        chat_area.addWidget(chat_label)
        
        self.chat_list = QListWidget()
        self.chat_list.setFixedHeight(150)
        chat_area.addWidget(self.chat_list)
        
        chat_input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("输入消息...")
        self.chat_input.returnPressed.connect(self._on_send_chat)
        chat_input_layout.addWidget(self.chat_input)
        
        send_btn = QPushButton("发送")
        send_btn.clicked.connect(self._on_send_chat)
        chat_input_layout.addWidget(send_btn)
        chat_area.addLayout(chat_input_layout)
        right_panel.addLayout(chat_area)
        
        main_content.addLayout(right_panel)
        layout.addLayout(main_content)
        
        controls_bar = QHBoxLayout()
        controls_bar.addStretch()
        
        self.camera_btn = QPushButton("📹 开启摄像头")
        self.camera_btn.clicked.connect(self._on_toggle_camera)
        controls_bar.addWidget(self.camera_btn)
        
        self.mic_btn = QPushButton("🎙️ 开启麦克风")
        self.mic_btn.setStyleSheet("background-color: #F85149;")
        self.mic_btn.clicked.connect(self._on_toggle_mic)
        controls_bar.addWidget(self.mic_btn)
        
        self.volume_label = QLabel("📊")
        self.volume_label.setStyleSheet("font-size: 16px;")
        controls_bar.addWidget(self.volume_label)
        
        self.volume_bar = QWidget()
        self.volume_bar.setFixedSize(60, 10)
        self.volume_bar.setStyleSheet("background-color: #30363D; border-radius: 5px;")
        self.volume_fill = QWidget(self.volume_bar)
        self.volume_fill.setFixedSize(0, 10)
        self.volume_fill.setStyleSheet("background-color: #238636; border-radius: 5px;")
        controls_bar.addWidget(self.volume_bar)
        
        self.raise_hand_btn = QPushButton("✋ 举手")
        self.raise_hand_btn.clicked.connect(self._on_raise_hand)
        controls_bar.addWidget(self.raise_hand_btn)
        
        end_btn = QPushButton("🔴 结束会议")
        end_btn.setStyleSheet("background-color: #F85149; color: white; padding: 8px 24px; border-radius: 6px;")
        end_btn.clicked.connect(self._on_end_meeting)
        controls_bar.addWidget(end_btn)
        
        controls_bar.addStretch()
        layout.addLayout(controls_bar)
        
        self._start_countdown()
    
    def _show_video_placeholder(self):
        if not self._camera_on and self._video_slots:
            for slot in self._video_slots:
                if slot['is_self'] and not slot['camera_on']:
                    slot['video_frame'].setText("📷 点击开启摄像头")
    
    def _start_countdown(self):
        self._time_left = 15 * 60
        self._countdown_timer = QTimer()
        self._countdown_timer.timeout.connect(self._update_countdown)
        self._countdown_timer.start(1000)
    
    def _update_countdown(self):
        self._time_left -= 1
        minutes = self._time_left // 60
        seconds = self._time_left % 60
        self.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")
        
        if self._time_left <= 120:
            self.countdown_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #F85149;")
        if self._time_left <= 0:
            self._countdown_timer.stop()
            QMessageBox.information(self, "时间到", "站会时间已结束！")
    
    def _setup_video_grid(self):
        self._clear_video_grid()
        
        self._video_slots.append(self._create_video_slot("我", is_self=True))
        
        members = self.api_client.get_team_members(self.meeting["team_id"])
        for m in members:
            if m["name"] != "张三":
                self._video_slots.append(self._create_video_slot(m["name"], is_self=False))
        
        self._update_video_grid_layout()
    
    def _create_video_slot(self, name, is_self=False):
        slot_widget = QWidget()
        slot_layout = QVBoxLayout(slot_widget)
        slot_layout.setContentsMargins(2, 2, 2, 2)
        slot_layout.setSpacing(2)
        
        video_frame = QLabel()
        video_frame.setStyleSheet("""
            QLabel {
                background-color: #0D1117;
                border: 1px solid #30363D;
                border-radius: 6px;
            }
        """)
        video_frame.setAlignment(Qt.AlignCenter)
        video_frame.setScaledContents(True)
        
        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: {'#58A6FF' if is_self else '#8B949E'};
                font-weight: {'bold' if is_self else 'normal'};
                padding: 2px 4px;
                background-color: rgba(0,0,0,0.5);
                border-radius: 3px;
            }}
        """)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setMaximumHeight(20)
        
        status_icon = QLabel("🔴")
        status_icon.setStyleSheet("font-size: 10px;")
        status_icon.setAlignment(Qt.AlignRight)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(name_label)
        header_layout.addWidget(status_icon)
        header_layout.addStretch()
        
        slot_layout.addLayout(header_layout)
        slot_layout.addWidget(video_frame, 1)
        
        return {
            'name': name,
            'widget': slot_widget,
            'video_frame': video_frame,
            'status_icon': status_icon,
            'is_self': is_self,
            'camera_on': False
        }
    
    def _clear_video_grid(self):
        for slot in self._video_slots:
            slot['widget'].setParent(None)
        self._video_slots.clear()
        
        for i in reversed(range(self.video_layout.count())):
            item = self.video_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()
    
    def _get_grid_dimensions(self, count):
        if count == 1:
            return (1, 1)
        elif count == 2:
            return (1, 2)
        elif count == 3:
            return (2, 2)
        elif count == 4:
            return (2, 2)
        elif count <= 6:
            return (2, 3)
        elif count <= 9:
            return (3, 3)
        else:
            rows = ((count + 2) // 3)
            return (rows, 3)
    
    def _update_video_grid_layout(self):
        for i in reversed(range(self.video_layout.count())):
            item = self.video_layout.takeAt(i)
            if item.widget():
                item.widget().setParent(None)
        
        count = len(self._video_slots)
        rows, cols = self._get_grid_dimensions(count)
        
        slot_width = (640 - 8 * 2 - 6 * (cols - 1)) // cols
        slot_height = (480 - 8 * 2 - 6 * (rows - 1)) // rows
        
        for idx, slot in enumerate(self._video_slots):
            row = idx // cols
            col = idx % cols
            slot['widget'].setFixedSize(slot_width, slot_height)
            self.video_layout.addWidget(slot['widget'], row, col)
    
    def _on_toggle_camera(self):
        self._camera_on = not self._camera_on
        if self._camera_on:
            self.camera_btn.setText("📹 关闭摄像头")
            self._start_camera()
        else:
            self.camera_btn.setText("📹 开启摄像头")
            self._stop_camera()
    
    def _start_camera(self):
        try:
            self._camera = QCamera()
            self._capture_session = QMediaCaptureSession()
            self._capture_session.setCamera(self._camera)
            
            if self._video_slots:
                self._video_slots[0]['camera_on'] = True
                self._video_slots[0]['status_icon'].setText("🟢")
                
                if self._video_slots[0]['video_frame']:
                    video_frame = self._video_slots[0]['video_frame']
                    from PySide6.QtMultimediaWidgets import QVideoWidget
                    
                    video_widget = QVideoWidget()
                    video_widget.setStyleSheet("background-color: transparent;")
                    
                    layout = video_frame.layout()
                    if layout:
                        for i in reversed(range(layout.count())):
                            item = layout.takeAt(i)
                            if item.widget():
                                item.widget().deleteLater()
                    else:
                        layout = QVBoxLayout(video_frame)
                        layout.setContentsMargins(0, 0, 0, 0)
                    
                    layout.addWidget(video_widget)
                    self._capture_session.setVideoOutput(video_widget)
                    video_widget.show()
                    self._video_slots[0]['video_widget'] = video_widget
            
            self._camera.start()
        except Exception as e:
            print(f"Camera error: {e}")
            QMessageBox.warning(self, "摄像头错误", f"无法启动摄像头: {str(e)}")
            self._camera_on = False
            self.camera_btn.setText("📹 开启摄像头")
    
    def _stop_camera(self):
        if self._camera:
            self._camera.stop()
            self._camera = None
            self._capture_session = None
        
        if self._video_slots:
            self._video_slots[0]['camera_on'] = False
            self._video_slots[0]['status_icon'].setText("🔴")
            
            video_frame = self._video_slots[0]['video_frame']
            layout = video_frame.layout()
            if layout:
                for i in reversed(range(layout.count())):
                    item = layout.takeAt(i)
                    if item.widget():
                        item.widget().deleteLater()
            
            video_frame.setText("📷 摄像头已关闭")
        self.video_placeholder.show()
        self._show_video_placeholder()
    
    def _on_toggle_mic(self):
        self._mic_on = not self._mic_on
        if self._mic_on:
            self.mic_btn.setText("🎙️ 关闭麦克风")
            self.mic_btn.setStyleSheet("")
            self._audio_thread.start()
        else:
            self.mic_btn.setText("🎙️ 开启麦克风")
            self.mic_btn.setStyleSheet("background-color: #F85149;")
            self._audio_thread.stop()
            self._current_volume = 0
            self.volume_fill.setFixedSize(0, 10)
            self.volume_fill.setStyleSheet("background-color: #238636; border-radius: 5px;")
    
    def _on_volume_changed(self, volume):
        self._current_volume = volume
        bar_width = int(self._current_volume * 60)
        self.volume_fill.setFixedSize(bar_width, 10)
        
        if self._current_volume > 0.8:
            self.volume_fill.setStyleSheet("background-color: #F85149; border-radius: 5px;")
        elif self._current_volume > 0.5:
            self.volume_fill.setStyleSheet("background-color: #D29922; border-radius: 5px;")
        else:
            self.volume_fill.setStyleSheet("background-color: #238636; border-radius: 5px;")
    
    def _on_audio_error(self, error_msg):
        QMessageBox.warning(self, "麦克风错误", error_msg)
        self._mic_on = False
        self.mic_btn.setText("🎙️ 开启麦克风")
        self.mic_btn.setStyleSheet("background-color: #F85149;")
        self._current_volume = 0
        self.volume_fill.setFixedSize(0, 10)
    
    def _on_raise_hand(self):
        if self.raise_hand_btn.styleSheet() == "":
            self.raise_hand_btn.setStyleSheet("background-color: #D29922;")
            self.raise_hand_btn.setText("✋ 放下手")
            QMessageBox.information(self, "举手成功", "您已举手，主持人将注意到您的请求")
            self.chat_list.addItem(QListWidgetItem("🖐️ 张三 举起了手"))
        else:
            self.raise_hand_btn.setStyleSheet("")
            self.raise_hand_btn.setText("✋ 举手")
            QMessageBox.information(self, "已放下手", "您已放下手")
            self.chat_list.addItem(QListWidgetItem("🖐️ 张三 放下了手"))
    
    def _on_submit_speech(self):
        yesterday = self.yesterday_edit.toPlainText()
        today = self.today_edit.toPlainText()
        blockers = self.blockers_edit.toPlainText()
        
        if yesterday or today or blockers:
            self.chat_list.addItem(QListWidgetItem(f"📝 张三发言:"))
            if yesterday:
                self.chat_list.addItem(QListWidgetItem(f"  ✅ {yesterday}"))
            if today:
                self.chat_list.addItem(QListWidgetItem(f"  📋 {today}"))
            if blockers:
                self.chat_list.addItem(QListWidgetItem(f"  🚧 {blockers}"))
            self.chat_list.scrollToBottom()
            
            self.yesterday_edit.clear()
            self.today_edit.clear()
            self.blockers_edit.clear()
    
    def _on_send_chat(self):
        msg = self.chat_input.text().strip()
        if msg:
            self.chat_list.addItem(QListWidgetItem(f"💬 张三: {msg}"))
            self.chat_list.scrollToBottom()
            self.chat_input.clear()
    
    def _on_end_meeting(self):
        reply = QMessageBox.question(self, "确认结束", "确定要结束这次会议吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._stop_camera()
            self._audio_thread.stop()
            self._countdown_timer.stop()
            self.meeting_ended.emit()

class HomePage(QWidget):
    meeting_started = Signal(dict)
    
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._current_team = "1"
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        top_bar = QHBoxLayout()
        self.team_combo = QComboBox()
        for t in self.api_client.get_teams():
            self.team_combo.addItem(t["name"], t["id"])
        self.team_combo.currentIndexChanged.connect(self._on_team_changed)
        top_bar.addWidget(self.team_combo)
        top_bar.addStretch()
        self.new_btn = QPushButton("+ 新建站会")
        self.new_btn.clicked.connect(self._on_new_meeting)
        top_bar.addWidget(self.new_btn)
        layout.addLayout(top_bar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["日期", "Sprint", "标题", "出勤", "状态", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        QTimer.singleShot(100, self._load_meetings)
    
    def _load_meetings(self):
        meetings = self.api_client.get_meetings(self._current_team)
        self.table.setRowCount(len(meetings))
        for i, m in enumerate(meetings):
            self.table.setItem(i, 0, QTableWidgetItem(m["date"][5:]))
            self.table.setItem(i, 1, QTableWidgetItem(m["sprint"]))
            self.table.setItem(i, 2, QTableWidgetItem(m["title"]))
            self.table.setItem(i, 3, QTableWidgetItem(m["attendance"]))
            
            status = m["status"]
            status_text = {"created": "已创建", "active": "进行中", "ended": "已结束"}.get(status, status)
            status_item = QTableWidgetItem(status_text)
            if status == "active":
                status_item.setForeground(Qt.GlobalColor.green)
            elif status == "ended":
                status_item.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(i, 4, status_item)
            
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(4)
            
            join_btn = QPushButton("进入会议")
            join_btn.setStyleSheet("background-color: #238636; color: white; padding: 6px 16px; border-radius: 4px; font-size: 12px;")
            join_btn.setMinimumWidth(80)
            join_btn.clicked.connect(lambda checked, mid=m.copy(): self._on_join_meeting(mid))
            btn_layout.addWidget(join_btn)
            
            delete_btn = QPushButton("删除")
            delete_btn.setStyleSheet("background-color: #F85149; color: white; padding: 6px 16px; border-radius: 4px; font-size: 12px;")
            delete_btn.setMinimumWidth(60)
            delete_btn.clicked.connect(lambda checked, mid=m["id"]: self._on_delete_meeting(mid))
            btn_layout.addWidget(delete_btn)
            
            cell_widget = QWidget()
            cell_widget.setLayout(btn_layout)
            self.table.setCellWidget(i, 5, cell_widget)
    
    def _on_team_changed(self):
        self._current_team = self.team_combo.currentData()
        self._load_meetings()
    
    def _on_new_meeting(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("新建站会")
        dlg.resize(400, 200)
        layout = QVBoxLayout(dlg)
        
        layout.addWidget(QLabel("站会标题:"))
        title_edit = QLineEdit()
        title_edit.setText("每日站会")
        layout.addWidget(title_edit)
        
        layout.addWidget(QLabel("Sprint编号:"))
        sprint_edit = QLineEdit()
        sprint_edit.setText("Sprint #13")
        layout.addWidget(sprint_edit)
        
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dlg.close)
        create_btn = QPushButton("创建")
        create_btn.clicked.connect(lambda: self._create_meeting(title_edit.text(), sprint_edit.text(), dlg))
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(create_btn)
        layout.addLayout(btn_layout)
        
        dlg.exec()
    
    def _create_meeting(self, title, sprint, dlg):
        self.api_client.create_meeting(self._current_team, title, sprint_no=sprint)
        dlg.close()
        self._load_meetings()
    
    def _on_start_meeting(self, meeting):
        self.api_client.start_meeting(meeting["id"])
        self.meeting_started.emit(meeting)
        self._load_meetings()
    
    def _on_join_meeting(self, meeting):
        print(f"DEBUG: _on_join_meeting called, meeting={meeting}")
        self.meeting_started.emit(meeting)
    
    def _on_delete_meeting(self, meeting_id):
        reply = QMessageBox.question(self, "确认删除", "确定要删除这个站会吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.api_client.delete_meeting(meeting_id)
            self._load_meetings()

class TeamPage(QWidget):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._current_team = "1"
        self._invite_code = self._generate_numeric_code()
        self._init_ui()
    
    def _generate_numeric_code(self):
        import random
        return ''.join(random.choices('0123456789', k=6))
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        top_bar = QHBoxLayout()
        self.team_combo = QComboBox()
        self._update_team_combo()
        self.team_combo.currentIndexChanged.connect(self._on_team_changed)
        top_bar.addWidget(self.team_combo)
        
        self.new_team_btn = QPushButton("+ 创建团队")
        self.new_team_btn.clicked.connect(self._on_new_team)
        top_bar.addWidget(self.new_team_btn)
        
        self.delete_team_btn = QPushButton("解散团队")
        self.delete_team_btn.setStyleSheet("background-color: #F85149; color: white; padding: 8px 16px; border-radius: 6px;")
        self.delete_team_btn.clicked.connect(self._on_delete_team)
        top_bar.addWidget(self.delete_team_btn)
        
        top_bar.addStretch()
        layout.addLayout(top_bar)
        
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
        
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet("color: #2A2A4A;")
        invite_layout.addWidget(separator2)
        
        join_section = QVBoxLayout()
        join_section.setSpacing(4)
        
        join_label = QLabel("➕ 加入团队")
        join_label.setStyleSheet("color: #8E8E9E; font-size: 13px; font-weight: bold;")
        join_section.addWidget(join_label)
        
        join_input_layout = QHBoxLayout()
        join_input_layout.setSpacing(6)
        
        self._join_code_input = QLineEdit()
        self._join_code_input.setPlaceholderText("输入6位邀请码")
        self._join_code_input.setMaxLength(6)
        self._join_code_input.setStyleSheet("""
            QLineEdit {
                background-color: #0D1117;
                border: 1px solid #2A2A4A;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
                color: #E0E0E0;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QLineEdit:focus {
                border-color: #4A9ED9;
                outline: none;
            }
        """)
        join_input_layout.addWidget(self._join_code_input)
        
        self._btn_join_team = QPushButton("加入")
        self._btn_join_team.setCursor(Qt.PointingHandCursor)
        self._btn_join_team.clicked.connect(self._on_join_team)
        self._btn_join_team.setStyleSheet("""
            QPushButton {
                background-color: #52C41A;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #43A017;
            }
        """)
        join_input_layout.addWidget(self._btn_join_team)
        
        join_section.addLayout(join_input_layout)
        
        self._join_status_label = QLabel("")
        self._join_status_label.setStyleSheet("font-size: 11px; color: #E74C3C;")
        join_section.addWidget(self._join_status_label)
        
        invite_layout.addLayout(join_section)
        
        invite_layout.addStretch()
        layout.addWidget(invite_frame)
        
        member_top_bar = QHBoxLayout()
        member_top_bar.addWidget(QLabel("<h3>团队成员</h3>"))
        member_top_bar.addStretch()
        self.add_member_btn = QPushButton("+ 添加成员")
        self.add_member_btn.clicked.connect(self._on_add_member)
        member_top_bar.addWidget(self.add_member_btn)
        layout.addLayout(member_top_bar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["姓名", "角色", "出勤率", "完成率", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        QTimer.singleShot(100, self._load_members)
    
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
        self._invite_code = self._generate_numeric_code()
        self._invite_code_label.setText(self._invite_code)
        self._invite_link_label.setText(self._generate_invite_link())
        QMessageBox.information(self, "成功", "邀请码和邀请链接已刷新")
    
    def _on_join_team(self):
        code = self._join_code_input.text().strip()
        
        if not code or len(code) != 6 or not code.isdigit():
            self._join_status_label.setText("❌ 请输入6位数字邀请码")
            return
        
        self._join_status_label.setText("")
        
        if code == self._invite_code:
            QMessageBox.information(self, "成功", f"已成功加入团队")
            self._join_code_input.clear()
            self._load_members()
        else:
            self._join_status_label.setText("❌ 邀请码无效")
    
    def _update_team_combo(self):
        self.team_combo.clear()
        for t in self.api_client.get_teams():
            self.team_combo.addItem(t["name"], t["id"])
    
    def _load_members(self):
        members = self.api_client.get_team_members(self._current_team)
        self.table.setRowCount(len(members))
        roles = ["Tech Lead", "Scrum Master", "Developer", "Observer"]
        
        for i, m in enumerate(members):
            self.table.setItem(i, 0, QTableWidgetItem(m["name"]))
            
            role_combo = QComboBox()
            role_combo.addItems(roles)
            role_combo.setCurrentText(m["role"])
            role_combo.currentTextChanged.connect(lambda text, mid=m["id"]: self._on_role_change(mid, text))
            self.table.setCellWidget(i, 1, role_combo)
            
            self.table.setItem(i, 2, QTableWidgetItem(f"{int(float(m['attendance'])*100)}%"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{int(float(m['completion'])*100)}%"))
            
            remove_btn = QPushButton("移除")
            remove_btn.setStyleSheet("background-color: #F85149; color: white; padding: 4px 12px; border-radius: 4px;")
            remove_btn.clicked.connect(lambda checked, mid=m["id"]: self._on_remove_member(mid))
            self.table.setCellWidget(i, 4, remove_btn)
    
    def _on_team_changed(self):
        self._current_team = self.team_combo.currentData()
        self._load_members()
    
    def _on_new_team(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("创建团队")
        dlg.resize(300, 120)
        layout = QVBoxLayout(dlg)
        
        layout.addWidget(QLabel("团队名称:"))
        name_edit = QLineEdit()
        layout.addWidget(name_edit)
        
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dlg.close)
        create_btn = QPushButton("创建")
        create_btn.clicked.connect(lambda: self._create_team(name_edit.text(), dlg))
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(create_btn)
        layout.addLayout(btn_layout)
        
        dlg.exec()
    
    def _create_team(self, name, dlg):
        if name.strip():
            result = self.api_client.create_team(name)
            if result.get("success"):
                team_id = result.get("team", {}).get("id", "1")
                self._current_team = team_id
                self._invite_code = self._generate_numeric_code()
                self._invite_code_label.setText(self._invite_code)
                self._invite_link_label.setText(self._generate_invite_link())
            self._update_team_combo()
        dlg.close()
    
    def _on_delete_team(self):
        team_name = self.team_combo.currentText()
        reply = QMessageBox.question(self, "确认解散", f"确定要解散团队 '{team_name}' 吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.api_client.delete_team(self._current_team)
            self._update_team_combo()
            if self.api_client.get_teams():
                self._current_team = self.api_client.get_teams()[0]["id"]
                self._load_members()
            else:
                self.table.setRowCount(0)
    
    def _on_add_member(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("添加成员")
        dlg.resize(300, 150)
        layout = QVBoxLayout(dlg)
        
        layout.addWidget(QLabel("成员姓名:"))
        name_edit = QLineEdit()
        layout.addWidget(name_edit)
        
        layout.addWidget(QLabel("角色:"))
        role_combo = QComboBox()
        role_combo.addItems(["Tech Lead", "Scrum Master", "Developer", "Observer"])
        role_combo.setCurrentText("Developer")
        layout.addWidget(role_combo)
        
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dlg.close)
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(lambda: self._add_member(name_edit.text(), role_combo.currentText(), dlg))
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(add_btn)
        layout.addLayout(btn_layout)
        
        dlg.exec()
    
    def _add_member(self, name, role, dlg):
        if name.strip():
            self.api_client.add_member(self._current_team, name, role)
            self._load_members()
        dlg.close()
    
    def _on_remove_member(self, member_id):
        reply = QMessageBox.question(self, "确认移除", "确定要移除该成员吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.api_client.remove_member(self._current_team, member_id)
            self._load_members()
    
    def _on_role_change(self, member_id, new_role):
        self.api_client.update_member_role(self._current_team, member_id, new_role)

class MainWindow(QMainWindow):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._init_ui()
    
    def _init_ui(self):
        self.setWindowTitle("StandupSync - 团队站会速记工具")
        self.resize(1200, 800)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        
        sidebar = QFrame()
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet("background-color: #161B22;")
        sidebar_layout = QVBoxLayout(sidebar)
        
        logo = QLabel("StandupSync")
        logo.setStyleSheet("font-size: 18px; font-weight: bold; color: #58A6FF; padding: 20px;")
        sidebar_layout.addWidget(logo)
        
        self.nav_btns = []
        for name, page_idx in [("站会", 0), ("待办", 1), ("看板", 2), ("团队", 3), ("设置", 4)]:
            btn = QPushButton(name)
            btn.setStyleSheet("text-align: left; padding: 10px 20px; border: none; background: transparent; color: #8B949E;")
            btn.clicked.connect(lambda checked, idx=page_idx: self._navigate(idx))
            btn.setCursor(Qt.PointingHandCursor)
            self.nav_btns.append(btn)
            sidebar_layout.addWidget(btn)
        
        sidebar_layout.addStretch()
        user_info = QLabel("张三\nTech Lead")
        user_info.setStyleSheet("color: #8B949E; font-size: 12px; padding: 10px 20px;")
        sidebar_layout.addWidget(user_info)
        layout.addWidget(sidebar)
        
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        self.home_page = HomePage(self.api_client)
        self.home_page.meeting_started.connect(self._on_meeting_started)
        
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(QLabel("待办页面"))
        self.stack.addWidget(QLabel("看板页面"))
        self.stack.addWidget(TeamPage(self.api_client))
        self.stack.addWidget(QLabel("设置页面"))
    
    def _navigate(self, page_idx):
        self.stack.setCurrentIndex(page_idx)
        for i, btn in enumerate(self.nav_btns):
            btn.setStyleSheet(f"""
                text-align: left; padding: 10px 20px; border: none; 
                background: {'#0F3460' if i == page_idx else 'transparent'}; 
                color: {'#FFFFFF' if i == page_idx else '#8B949E'};
                border-left: 3px solid {'#4A9ED9' if i == page_idx else 'transparent'};
            """)
    
    def _on_meeting_started(self, meeting):
        print(f"DEBUG: _on_meeting_started called, meeting={meeting}")
        try:
            self.meeting_room = MeetingRoomPage(self.api_client, meeting)
            print("DEBUG: MeetingRoomPage created successfully")
            self.meeting_room.meeting_ended.connect(self._on_meeting_ended)
            self.stack.addWidget(self.meeting_room)
            print(f"DEBUG: MeetingRoomPage added to stack, stack count={self.stack.count()}")
            self.stack.setCurrentWidget(self.meeting_room)
            print(f"DEBUG: Current widget set, index={self.stack.currentIndex()}")
        except Exception as e:
            print(f"ERROR: _on_meeting_started failed: {e}")
    
    def _on_meeting_ended(self):
        self.stack.removeWidget(self.meeting_room)
        self._navigate(0)
        self.home_page._load_meetings()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(DARK_STYLE)
    
    api_client = MockAPIClient()
    window = MainWindow(api_client)
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())