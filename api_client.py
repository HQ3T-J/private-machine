# api_client.py — API 客户端
import requests
import os
import json
import logging
from typing import Optional

logger = logging.getLogger("StandupSync.APIClient")

# 可配置：环境变量 > 默认值
BASE_URL = os.environ.get("STANDUPSYNC_API", "http://localhost:8080")
TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".standupsync_session.json")


class APIClient:
    """单例 API 客户端。后端不可用时返回 None/空列表，不伪造数据。"""

    _instance: Optional["APIClient"] = None

    @staticmethod
    def base_url() -> str:
        return BASE_URL

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.token = None
            cls._instance.user_id = None
            cls._instance.role = None
            cls._instance.username = ""
            cls._instance._online = None
        return cls._instance

    # ═══ Token 持久化 ═══
    @staticmethod
    def load_session() -> Optional[dict]:
        """从本地文件加载会话(token+user)，用于自动登录"""
        try:
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def save_session(self, remember: bool = True):
        """保存会话到本地文件"""
        if not remember or not self.token:
            return
        try:
            with open(TOKEN_FILE, "w") as f:
                json.dump({
                    "token": self.token,
                    "userId": self.user_id,
                    "username": self.username,
                    "role": self.role,
                }, f)
        except Exception:
            pass

    @staticmethod
    def clear_session():
        """删除本地会话文件(退出登录时调用)"""
        try:
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
        except Exception:
            pass

    def try_auto_login(self) -> bool:
        """尝试用已保存的 token 自动登录"""
        session = self.load_session()
        if not session or not session.get("token"):
            return False
        self.token = session["token"]
        self.user_id = session.get("userId")
        self.username = session.get("username", "")
        self.role = session.get("role", "")
        # 验证 token 是否还有效
        profile = self.get_profile()
        if profile:
            self.username = profile.get("username", self.username)
            self.role = profile.get("role", self.role)
            return True
        # token 过期，清除
        self.token = None
        self.clear_session()
        return False

    # ═══ 基础 ═══
    @property
    def online(self) -> bool:
        """后端在线状态（惰性检测，由 _get/_post 自动更新）"""
        if self._online is None:
            self._check_online()
        return self._online

    def _check_online(self):
        """快速检测后端是否在线（1秒超时）"""
        try:
            r = requests.get(f"{BASE_URL}/", timeout=1)
            self._online = r.status_code < 500
        except Exception:
            self._online = False

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _get(self, path: str, fallback=None):
        try:
            r = requests.get(f"{BASE_URL}{path}", headers=self._headers(), timeout=5)
            self._online = True
            if r.status_code == 200:
                data = r.json()
                return data.get("data", data)
            if r.status_code >= 500:
                self._online = False
                return fallback
        except requests.ConnectionError:
            self._online = False
            logger.debug("Connection refused for %s %s", "GET", path)
            return fallback
        except Exception as e:
            logger.warning("[APIClient._get] %s: %s", path, e)
            return fallback
        return fallback

    def _post(self, path: str, body: dict, fallback=None):
        try:
            r = requests.post(f"{BASE_URL}{path}", json=body, headers=self._headers(), timeout=5)
            self._online = True
            if r.status_code != 200:
                return r.json()
            return r.json()
        except requests.ConnectionError:
            self._online = False
            logger.debug("Connection refused for POST %s", path)
            return fallback
        except Exception as e:
            logger.warning("[APIClient._post] %s: %s", path, e)
            return fallback

    def _parse_error(self, resp) -> str:
        """统一提取错误信息，兼容 msg / message 双字段"""
        if not isinstance(resp, dict): return str(resp)
        return resp.get("msg") or resp.get("message") or str(resp)

    # ═══════════════════════════════════════════════
    #  认证
    # ═══════════════════════════════════════════════
    def login(self, username: str, password: str) -> Optional[dict]:
        resp = self._post("/api/auth/login", {"username": username, "password": password})
        if resp and resp.get("code") == 200:
            data = resp["data"]
            self.token = data.get("token")
            self.user_id = data.get("userId")
            self.role = data.get("role")
            self.username = username
            return data
        return None

    def register(self, username: str, password: str, display_name: str = "") -> Optional[dict]:
        resp = self._post("/api/auth/register", {
            "username": username, "password": password, "displayName": display_name or username
        })
        if not resp:
            return None  # 网络不通
        if resp.get("code") == 200:
            data = resp["data"]
            self.token = data.get("token")
            self.user_id = data.get("userId")
            self.role = data.get("role")
            self.username = username
            return data
        # 返回完整响应给调用方显示错误信息
        return resp

    # ═══════════════════════════════════════════════
    #  团队
    # ═══════════════════════════════════════════════
    def get_teams(self) -> list:
        online = self._get("/api/teams")
        if online and isinstance(online, list):
            return online
        return []

    def get_team_members(self, team_id) -> list:
        online = self._get(f"/api/teams/{team_id}")
        if online and isinstance(online, dict):
            return online.get("members", [])
        return []

    def get_invite_code(self, team_id) -> Optional[str]:
        """获取团队邀请码（从团队详情中读取）"""
        data = self._get(f"/api/teams/{team_id}")
        if data and isinstance(data, dict):
            team = data.get("team", {})
            return team.get("inviteCode")
        return None

    # ═══════════════════════════════════════════════
    #  站会
    # ═══════════════════════════════════════════════
    def get_meetings(self, team_id) -> list:
        if not team_id:
            return []
        data = self._get(f"/api/meetings?teamId={team_id}")
        return data if isinstance(data, list) else []

    def create_meeting(self, team_id, sprint_no: str = None, title: str = None, participants: list = None) -> Optional[dict]:
        body = {"teamId": team_id}
        if sprint_no is not None:
            try:
                body["sprintNo"] = int(sprint_no)
            except (ValueError, TypeError):
                body["sprintNo"] = 1
        if title:
            body["title"] = title
        return self._post("/api/meetings", body)

    def start_meeting(self, meeting_id) -> Optional[dict]:
        return self._post(f"/api/meetings/{meeting_id}/start", {})

    def end_meeting(self, meeting_id) -> Optional[dict]:
        return self._post(f"/api/meetings/{meeting_id}/end", {})

    def submit_speech(self, meeting_id: str, yesterday: str, today: str, blockers: str) -> Optional[dict]:
        return self._post(f"/api/meetings/{meeting_id}/speeches", {
            "yesterday": yesterday, "today": today, "blockers": blockers
        })

    def submit_free_speech(self, meeting_id: str, text: str, input_method: str = "TEXT") -> Optional[dict]:
        """自由文本发言 — AI 自动解析"""
        return self._post(f"/api/meetings/{meeting_id}/speeches/free", {
            "text": text, "inputMethod": input_method
        })

    def get_speeches(self, meeting_id: str) -> list:
        online = self._get(f"/api/meetings/{meeting_id}/speeches")
        return online if isinstance(online, list) else []

    # ═══════════════════════════════════════════════
    #  AI
    # ═══════════════════════════════════════════════
    def analyze_meeting(self, meeting_id: str) -> Optional[dict]:
        return self._post(f"/api/meetings/{meeting_id}/analyze", {})

    def get_ai_status(self, meeting_id: str) -> Optional[dict]:
        return self._get(f"/api/meetings/{meeting_id}/ai-status")

    # ═══════════════════════════════════════════════
    #  待办
    # ═══════════════════════════════════════════════
    def get_todos(self, status: str = None) -> list:
        path = "/api/action-items"
        if status:
            path += f"?status={status}"
        online = self._get(path)
        return online if isinstance(online, list) else []

    def create_todo(self, content: str, assignee_id: str = None, priority: str = "MEDIUM") -> Optional[dict]:
        body = {"content": content, "priority": priority}
        if assignee_id:
            body["assigneeId"] = assignee_id
        return self._post("/api/action-items", body)

    def update_todo(self, todo_id: str, updates: dict) -> Optional[dict]:
        try:
            r = requests.put(f"{BASE_URL}/api/action-items/{todo_id}", json=updates, headers=self._headers(), timeout=5)
            return r.json()
        except Exception:
            return None

    def delete_todo(self, todo_id: str) -> Optional[dict]:
        try:
            r = requests.delete(f"{BASE_URL}/api/action-items/{todo_id}", headers=self._headers(), timeout=5)
            return r.json()
        except Exception:
            return None

    # ═══════════════════════════════════════════════
    #  看板
    # ═══════════════════════════════════════════════
    def get_dashboard_summary(self, team_id, sprint_no: str = None, date_from: str = None, date_to: str = None) -> Optional[dict]:
        url = f"/api/dashboard/summary?teamId={team_id}"
        if sprint_no: url += f"&sprintNo={sprint_no}"
        if date_from: url += f"&dateFrom={date_from}"
        if date_to: url += f"&dateTo={date_to}"
        return self._get(url)

    def get_dashboard_trend(self, team_id, trend_type="attendance", user_id: str = None) -> list:
        path = f"/api/dashboard/{trend_type}-trend?teamId={team_id}"
        if user_id: path += f"&userId={user_id}"
        data = self._get(path)
        return data if isinstance(data, list) else []

    def get_dashboard_blocker(self, team_id, blocker_type: str = None) -> list:
        """阻碍分布 — 使用独立端点 blocker-distribution"""
        path = f"/api/dashboard/blocker-distribution?teamId={team_id}"
        if blocker_type: path += f"&blockerType={blocker_type}"
        data = self._get(path)
        return data if isinstance(data, list) else []

    def get_member_ranking(self, team_id, sort_by: str = "completionRate") -> list:
        data = self._get(f"/api/dashboard/member-ranking?teamId={team_id}&sortBy={sort_by}")
        return data if isinstance(data, list) else []

    # ═══ Phase2: 站会增强 ═══
    def paste_chat(self, meeting_id: str, text: str) -> Optional[dict]:
        return self._post(f"/api/meetings/{meeting_id}/paste", {"text": text})

    def classify_text(self, meeting_id: str, text: str) -> Optional[dict]:
        return self._post(f"/api/meetings/{meeting_id}/classify", {"text": text})

    def generate_summary(self, meeting_id: str) -> Optional[dict]:
        return self._post(f"/api/meetings/{meeting_id}/summary/generate", {})

    def get_summary(self, meeting_id: str) -> Optional[dict]:
        return self._get(f"/api/meetings/{meeting_id}/summary")

    def update_summary_item(self, item_id: str, updates: dict) -> Optional[dict]:
        try:
            r = requests.put(
                f"{BASE_URL}/api/meetings/summary/items/{item_id}",
                json=updates, headers=self._headers(), timeout=5
            )
            return r.json()
        except Exception:
            return None

    # ═══ Phase3: 团队申请审批 ═══
    def apply_to_join(self, invite_code: str) -> Optional[dict]:
        return self._post("/api/teams/join", {"inviteCode": invite_code})

    def get_applications(self, team_id) -> Optional[list]:
        data = self._get(f"/api/teams/{team_id}/applications")
        return data if isinstance(data, list) else []

    def approve_application(self, team_id, app_id) -> Optional[dict]:
        return self._post(f"/api/teams/{team_id}/applications/{app_id}/approve", {})

    def reject_application(self, team_id, app_id) -> Optional[dict]:
        return self._post(f"/api/teams/{team_id}/applications/{app_id}/reject", {})

    def change_member_role(self, team_id, user_id: str, role: str) -> Optional[dict]:
        try:
            r = requests.put(
                f"{BASE_URL}/api/teams/{team_id}/members/{user_id}/role",
                json={"role": role}, headers=self._headers(), timeout=5
            )
            return r.json()
        except Exception:
            return None

    def update_team_name(self, team_id, name: str) -> Optional[dict]:
        try:
            r = requests.put(
                f"{BASE_URL}/api/teams/{team_id}",
                json={"name": name}, headers=self._headers(), timeout=5
            )
            return r.json()
        except Exception:
            return None

    def regenerate_invite_code(self, team_id) -> Optional[dict]:
        return self._post(f"/api/teams/{team_id}/invite-code", {})

    def dissolve_team(self, team_id) -> Optional[dict]:
        return self._post(f"/api/teams/{team_id}/dissolve", {})

    def remove_team_member(self, team_id, user_id: str) -> Optional[dict]:
        """移除团队成员"""
        try:
            r = requests.delete(
                f"{BASE_URL}/api/teams/{team_id}/members/{user_id}",
                headers=self._headers(), timeout=5
            )
            return r.json()
        except Exception:
            return None

    # ═══ Phase4: Auth ═══
    def get_profile(self) -> Optional[dict]:
        return self._get("/api/auth/profile")

    def logout(self) -> Optional[dict]:
        return self._post("/api/auth/logout", {})

    # ═══ Phase5: 待办+看板 ═══
    def get_unfinished_todos(self) -> list:
        data = self._get("/api/todos/unfinished")
        return data if isinstance(data, list) else []

    def get_team_todos(self, team_id, status: str = None) -> list:
        url = f"/api/action-items/team?teamId={team_id}"
        if status: url += f"&status={status}"
        data = self._get(url)
        return data if isinstance(data, list) else []

    def get_dashboard_kpi(self, team_id, sprint_no: str = None, date_from: str = None, date_to: str = None) -> Optional[dict]:
        url = f"/api/dashboard/kpi?teamId={team_id}"
        if sprint_no: url += f"&sprintNo={sprint_no}"
        if date_from: url += f"&dateFrom={date_from}"
        if date_to: url += f"&dateTo={date_to}"
        return self._get(url)

    def get_dashboard_trends(self, team_id, user_id: str = None) -> Optional[dict]:
        url = f"/api/dashboard/trends?teamId={team_id}"
        if user_id: url += f"&userId={user_id}"
        return self._get(url)

    # ═══════════════════════════════════════════════
    #  Phase6: 转交审批流 + 通知 + AI 生成
    # ═══════════════════════════════════════════════

    # ── 转交审批 ──
    def transfer_todo(self, todo_id, target_user_id: str, reason: str = "") -> Optional[dict]:
        return self._post(f"/api/action-items/{todo_id}/transfer",
                          {"targetUserId": target_user_id, "reason": reason})

    def approve_transfer(self, todo_id) -> Optional[dict]:
        return self._post(f"/api/action-items/{todo_id}/approve-transfer", {})

    def reject_transfer(self, todo_id, reason: str = "") -> Optional[dict]:
        return self._post(f"/api/action-items/{todo_id}/reject-transfer",
                          {"reason": reason})

    def cancel_transfer(self, todo_id) -> Optional[dict]:
        return self._post(f"/api/action-items/{todo_id}/cancel-transfer", {})

    def get_pending_transfers(self, team_id) -> list:
        data = self._get(f"/api/action-items/pending-transfers?teamId={team_id}")
        return data if isinstance(data, list) else []

    def get_reviewed_transfers(self, team_id) -> list:
        data = self._get(f"/api/action-items/reviewed-transfers?teamId={team_id}")
        return data if isinstance(data, list) else []

    def hide_transfer_record(self, todo_id) -> Optional[dict]:
        return self._post(f"/api/action-items/{todo_id}/hide-transfer-record", {})

    # ── 通知 ──
    def get_notifications(self) -> list:
        data = self._get("/api/notifications")
        return data if isinstance(data, list) else []

    def get_unread_notifications(self) -> list:
        data = self._get("/api/notifications/unread")
        return data if isinstance(data, list) else []

    def get_unread_notification_count(self) -> int:
        data = self._get("/api/notifications/count")
        return data.get("unreadCount", 0) if isinstance(data, dict) else 0

    def mark_notification_read(self, notification_id) -> Optional[dict]:
        return self._post(f"/api/notifications/{notification_id}/read", {})

    def mark_all_notifications_read(self) -> Optional[dict]:
        return self._post("/api/notifications/read-all", {})

    # ── AI 生成 ──
    def ai_generate_todos(self, content: str, team_id) -> Optional[dict]:
        return self._post("/api/action-items/ai-generate",
                          {"content": content, "teamId": team_id})

    # ═══ Phase7: 补齐缺失的 API ═══
    def get_meeting_detail(self, meeting_id: str) -> Optional[dict]:
        """获取单个会议详情（含参与人和发言状态）"""
        return self._get(f"/api/meetings/{meeting_id}")

    def get_unfinished_items(self, meeting_id: str) -> list:
        """获取上次站会未完成的待办项"""
        data = self._get(f"/api/meetings/{meeting_id}/unfinished-items")
        return data if isinstance(data, list) else []

    def confirm_items(self, meeting_id: str, items: list) -> Optional[dict]:
        """批量确认站会待办项状态"""
        try:
            r = requests.put(
                f"{BASE_URL}/api/meetings/{meeting_id}/confirm-items",
                json=items, headers=self._headers(), timeout=5
            )
            return r.json()
        except Exception:
            return None

    def update_action_item_status(self, item_id: str, status: str) -> Optional[dict]:
        """更新单个待办项状态（status 作为 query 参数传递）"""
        try:
            r = requests.put(
                f"{BASE_URL}/api/action-items/{item_id}/status?status={status}",
                headers=self._headers(), timeout=5
            )
            return r.json()
        except Exception:
            return None

    def generate_action_items(self, meeting_id: str) -> Optional[dict]:
        """从 AI 纪要自动生成待办项"""
        return self._post(f"/api/meetings/{meeting_id}/generate-action-items", {})
