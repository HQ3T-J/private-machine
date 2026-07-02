#!/usr/bin/env python
"""StandupSync 核心 API 测试套件 — 覆盖认证/团队/站会/待办/看板 5 条链路"""
import requests
import sys
import time

BASE = "http://localhost:8080"
PASS, FAIL = 0, 0
TEST_USER = f"test_{int(time.time()) % 100000}"

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name}  {detail}")

# ═══ 1. 认证 (4 tests) ═══
print("\n═══ 认证 ═══")

# 1.1 Login
r = requests.post(f"{BASE}/api/auth/login",
    json={"username": "admin", "password": "123456"}, timeout=5)
d = r.json()
check("登录成功", d.get("code") == 200, d.get("message"))
token = d["data"]["token"]
uid = d["data"]["userId"]
h = {"Authorization": f"Bearer {token}"}

# 1.2 Register
r = requests.post(f"{BASE}/api/auth/register",
    json={"username": TEST_USER, "password": "test1234", "displayName": "Test"}, timeout=5)
check("注册成功", r.json().get("code") == 200, r.json().get("message"))

# 1.3 Profile
r = requests.get(f"{BASE}/api/auth/profile", headers=h, timeout=5)
check("获取个人信息", r.json().get("code") == 200)

# 1.4 No passwordHash leak
profile = r.json().get("data", {})
check("passwordHash不泄露", profile.get("passwordHash") is None)

# ═══ 2. 团队 (6 tests) ═══
print("\n═══ 团队 ═══")

# 2.1 Create
r = requests.post(f"{BASE}/api/teams", json={"name": "AutoTest"}, headers=h, timeout=5)
check("创建团队", r.json().get("code") == 200, r.json().get("message"))
tid = r.json()["data"]["id"]

# 2.2 List
r = requests.get(f"{BASE}/api/teams", headers=h, timeout=5)
check("团队列表", isinstance(r.json().get("data"), list))

# 2.3 Detail with members
r = requests.get(f"{BASE}/api/teams/{tid}", headers=h, timeout=5)
detail = r.json().get("data", {})
members = detail.get("members", [])
check("团队详情含成员", len(members) > 0)

# 2.4 Members have required fields
check("成员含user_id", all("user_id" in m for m in members))
check("成员含role", all("role" in m for m in members))

# 2.5 Invite code
r = requests.post(f"{BASE}/api/teams/{tid}/invite", json={}, headers=h, timeout=5)
check("获取邀请码", r.json().get("code") == 200)

# ═══ 3. 站会 (5 tests) ═══
print("\n═══ 站会 ═══")

# 3.1 Create meeting
r = requests.post(f"{BASE}/api/meetings",
    json={"teamId": tid, "title": "AutoTest Standup", "sprintNo": 1}, headers=h, timeout=5)
check("创建站会", r.json().get("code") == 200, r.json().get("message"))
mid = r.json()["data"]["id"]

# 3.2 List
r = requests.get(f"{BASE}/api/meetings?teamId={tid}", headers=h, timeout=5)
check("站会列表", isinstance(r.json().get("data"), list))

# 3.3 Detail with participants
r = requests.get(f"{BASE}/api/meetings/{mid}", headers=h, timeout=5)
md = r.json().get("data", {})
check("站会详情含参与者", len(md.get("participants", [])) > 0)
# Team should only expose id+name
team_info = md.get("team", {})
check("team仅暴露id+name", set(team_info.keys()).issubset({"id", "name"}), str(team_info.keys()))

# 3.4 Start
r = requests.post(f"{BASE}/api/meetings/{mid}/start", json={}, headers=h, timeout=5)
check("开始站会", r.json().get("code") == 200)

# ═══ 4. 待办 (5 tests) ═══
print("\n═══ 待办 ═══")

# 4.1 Create
r = requests.post(f"{BASE}/api/action-items",
    json={"content": "测试待办", "priority": "HIGH", "teamId": tid}, headers=h, timeout=5)
check("创建待办", r.json().get("code") == 200)
aid = r.json()["data"]["id"]

# 4.2 List
r = requests.get(f"{BASE}/api/action-items", headers=h, timeout=5)
check("待办列表", isinstance(r.json().get("data"), list))

# 4.3 Update
r = requests.put(f"{BASE}/api/action-items/{aid}",
    json={"content": "已更新"}, headers=h, timeout=5)
check("更新待办", r.json().get("code") == 200)

# 4.4 Status via query param
r = requests.put(f"{BASE}/api/action-items/{aid}/status?status=done", headers=h, timeout=5)
check("状态更新(query param)", r.json().get("code") == 200)

# 4.5 Delete with auth
r = requests.delete(f"{BASE}/api/action-items/{aid}", headers=h, timeout=5)
check("删除待办", r.json().get("code") in (200, 403), f"code={r.json().get('code')}")

# ═══ 5. 看板 (3 tests) ═══
print("\n═══ 看板 ═══")

r = requests.get(f"{BASE}/api/dashboard/summary?teamId={tid}", headers=h, timeout=5)
check("看板汇总", r.json().get("code") == 200)

r = requests.get(f"{BASE}/api/dashboard/attendance-trend?teamId={tid}", headers=h, timeout=5)
check("出勤趋势", isinstance(r.json().get("data"), list))

r = requests.get(f"{BASE}/api/dashboard/member-ranking?teamId={tid}&sortBy=completionRate", headers=h, timeout=5)
check("成员排行", isinstance(r.json().get("data"), list))

# ═══ 6. 安全 (3 tests) ═══
print("\n═══ 安全 ═══")

r = requests.delete(f"{BASE}/api/action-items/99999", timeout=5)
check("未认证删除被拒", r.status_code == 401)

r = requests.post(f"{BASE}/api/auth/login",
    json={"username": "admin", "password": "wrong"}, timeout=5)
check("错误密码被拒", r.json().get("code") == 401)

r = requests.get(f"{BASE}/api/teams", timeout=5)
check("未认证访问被拦", r.status_code == 401)

# ═══ Summary ═══
total = PASS + FAIL
print(f"\n{'='*40}")
print(f"  {PASS}/{total} 通过" if FAIL == 0 else f"  {PASS}/{total} 通过, {FAIL} 失败")
print(f"{'='*40}")
sys.exit(0 if FAIL == 0 else 1)
