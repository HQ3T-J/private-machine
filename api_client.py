# api_client.py — API 客户端
import requests
import os
from typing import Optional

# 可配置：环境变量 > 默认值
BASE_URL = os.environ.get("STANDUPSYNC_API", "http://localhost:8080")


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

    @property
    def online(self) -> bool:
        if self._online is None:
            try:
                r = requests.get(f"{BASE_URL}/", timeout=2)
                self._online = r.status_code < 500
            except Exception:
                self._online = False
        return self._online

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _get(self, path: str, fallback=None):
        if not self.online:
            return fallback
        try:
            r = requests.get(f"{BASE_URL}{path}", headers=self._headers(), timeout=5)
            if r.status_code == 200:
                data = r.json()
                return data.get("data", data)
        except Exception:
            pass
        return fallback

    def _post(self, path: str, body: dict, fallback=None):
        if not self.online:
            return fallback
        try:
            r = requests.post(f"{BASE_URL}{path}", json=body, headers=self._headers(), timeout=5)
            return r.json()
        except Exception:
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
        if resp and resp.get("code") == 200:
            data = resp["data"]
            self.token = data.get("token")
            self.user_id = data.get("userId")
            self.role = data.get("role")
            self.username = username
            return data
        return None

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
        online = self._post(f"/api/teams/{team_id}/invite", {})
        if online and isinstance(online, dict):
            data = online.get("data", online)
            return data.get("code") or data.get("inviteCode")
        return None

    # ═══════════════════════════════════════════════
    #  站会
    # ═══════════════════════════════════════════════
    def get_meetings(self, team_id) -> list:
        online = self._get(f"/api/meetings?teamId={team_id}")
        if online and isinstance(online, list):
            return online
        return []

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
    def get_dashboard_summary(self, team_id) -> Optional[dict]:
        return self._get(f"/api/dashboard/summary?teamId={team_id}")

    def get_dashboard_trend(self, team_id, trend_type="attendance") -> list:
        if trend_type == "blocker":
            path = f"/api/dashboard/blocker-distribution?teamId={team_id}"
        else:
            path = f"/api/dashboard/{trend_type}-trend?teamId={team_id}"
        online = self._get(path)
        return online if isinstance(online, list) else []

    def get_member_ranking(self, team_id) -> list:
        online = self._get(f"/api/dashboard/member-ranking?teamId={team_id}")
        return online if isinstance(online, list) else []

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
        return self._post(f"/api/meetings/summary/items/{item_id}", updates)

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
        return self._post(f"/api/teams/{team_id}/members/{user_id}/role", {"role": role})

    def update_team_name(self, team_id, name: str) -> Optional[dict]:
        return self._post(f"/api/teams/{team_id}", {"name": name})

    def regenerate_invite_code(self, team_id) -> Optional[dict]:
        return self._post(f"/api/teams/{team_id}/invite-code", {})

    def dissolve_team(self, team_id) -> Optional[dict]:
        return self._post(f"/api/teams/{team_id}/dissolve", {})

    # ═══ Phase4: Auth ═══
    def get_profile(self) -> Optional[dict]:
        return self._get("/api/auth/profile")

    def logout(self) -> Optional[dict]:
        return self._post("/api/auth/logout", {})

    # ═══ Phase5: 待办+看板 ═══
    def get_unfinished_todos(self) -> list:
        data = self._get("/api/todos/unfinished")
        return data if isinstance(data, list) else []

    def get_dashboard_kpi(self, team_id) -> Optional[dict]:
        return self._get(f"/api/dashboard/kpi?teamId={team_id}")

    def get_dashboard_trends(self, team_id) -> Optional[dict]:
        return self._get(f"/api/dashboard/trends?teamId={team_id}")
