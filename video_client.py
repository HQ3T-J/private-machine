"""WebSocket video client for video conferencing"""
import asyncio
import json
import base64

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    cv2 = None
    np = None

from PySide6.QtCore import QObject, Signal, Slot, QThread

class VideoClient(QObject):
    frame_received = Signal(int, bytes)
    peer_count_changed = Signal(int)
    connected = Signal()
    disconnected = Signal()
    
    def __init__(self, meeting_id):
        super().__init__()
        self.meeting_id = meeting_id
        self.websocket = None
        self.running = False
        self.capture = None
        self.peer_frames = {}
        self._remote_client_ids = []
    
    async def connect_to_server(self):
        try:
            import websockets
            self.websocket = await websockets.connect(f"ws://localhost:8088/{self.meeting_id}")
            await self.websocket.send(json.dumps({"type": "start_stream"}))
            self.connected.emit()
            asyncio.create_task(self._receive_loop())
        except Exception as e:
            print(f"Failed to connect to video server: {e}")
    
    async def _receive_loop(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                if data["type"] == "remote_frame":
                    client_id = data["client_id"]
                    frame_data = base64.b64decode(data["frame"])
                    if client_id not in self._remote_client_ids:
                        self._remote_client_ids.append(client_id)
                    self.frame_received.emit(len(self._remote_client_ids) - 1, frame_data)
                elif data["type"] == "stream_started":
                    self.peer_count_changed.emit(data["peer_count"])
        except Exception as e:
            print(f"Receive loop error: {e}")
            self.disconnected.emit()
    
    async def send_frame(self, frame):
        if self.websocket and self.running:
            try:
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                await self.websocket.send(json.dumps({
                    "type": "video_frame",
                    "frame": frame_base64
                }))
            except Exception as e:
                print(f"Failed to send frame: {e}")
    
    async def disconnect(self):
        if self.websocket:
            try:
                await self.websocket.send(json.dumps({"type": "stop_stream"}))
                await self.websocket.close()
            except:
                pass
            self.websocket = None
            self.disconnected.emit()
    
    def start_capture(self):
        self.running = True
        self.capture = cv2.VideoCapture(0)
    
    def stop_capture(self):
        self.running = False
        if self.capture:
            self.capture.release()
            self.capture = None
    
    async def capture_and_send(self):
        while self.running and self.capture:
            ret, frame = self.capture.read()
            if ret:
                await self.send_frame(frame)
            await asyncio.sleep(0.033)

class VideoClientWrapper(QThread):
    frame_received = Signal(int, bytes)
    peer_count_changed = Signal(int)
    connected = Signal()
    disconnected = Signal()
    
    def __init__(self, meeting_id):
        super().__init__()
        self.video_client = VideoClient(meeting_id)
        self.video_client.frame_received.connect(self.frame_received.emit)
        self.video_client.peer_count_changed.connect(self.peer_count_changed.emit)
        self.video_client.connected.connect(self.connected.emit)
        self.video_client.disconnected.connect(self.disconnected.emit)
    
    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._start())
    
    async def _start(self):
        await self.video_client.connect_to_server()
        self.video_client.start_capture()
        await self.video_client.capture_and_send()
    
    def stop(self):
        self.video_client.stop_capture()
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.wait()