# StandupSync 产品研发方案 V2.0

> 基于需求文档 V1.0 与功能列表（71 项功能）制定，适用于 PySide6 桌面 + FastAPI + MySQL 架构。

---

## 一、总体策略

### 1.1 核心原则

| 原则 | 说明 |
|------|------|
| **一级模块独立** | 每个一级模块拥有独立的数据库表、API 路由、PySide6 视图模块，可单独开发测试 |
| **接口先行** | 模块间仅通过 REST API / WebSocket 通信，不直接引用对方内部实现 |
| **依赖最小化** | 每个模块只依赖编号小于自身的模块，避免循环依赖 |
| **Mock 驱动并行** | 下游模块未就绪时，上游模块可用 Mock 数据独立开发和测试 |

### 1.2 模块开发顺序（拓扑排序）

```
Phase 0 ──── 基础设施（MySQL + FastAPI + PySide6 骨架）
  │
Phase 1 ──── 用户与认证 ──────┐
  │                            │
Phase 2 ──── 团队与成员 ◄──────┘
  │
Phase 3 ──── 站会管理
  │
Phase 4 ──── 站会发言 + WebSocket
  │
Phase 5 ──── AI 纪要 + AI 设置
  │
Phase 6 ──── 待办管理
  │
Phase 7 ──── 数据看板
  │
Phase 8 ──── 数据筛选
  │
Phase 9 ──── 数据管理（清理 + 导出）
  │
Parallel ── 系统配置（暗色模式、通知、PyInstaller 打包）—— 可在任意阶段并行开发
```

### 1.3 项目目录结构

```
standupsync/
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 入口，挂载所有路由
│   ├── core/                   # 配置、数据库连接、JWT 认证
│   │   ├── config.py
│   │   ├── database.py         # SQLAlchemy + MySQL
│   │   └── auth.py             # JWT 依赖注入
│   ├── models/                 # SQLAlchemy ORM 模型
│   │   ├── user.py
│   │   ├── team.py
│   │   ├── meeting.py
│   │   ├── speech.py
│   │   └── action_item.py
│   ├── schemas/                # Pydantic 请求/响应模型
│   ├── routers/                # API 路由（按模块拆分）
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── teams.py
│   │   ├── meetings.py
│   │   ├── speeches.py
│   │   ├── ai.py
│   │   ├── action_items.py
│   │   └── dashboard.py
│   ├── services/               # 业务逻辑层
│   │   ├── ai_service.py       # AI 代理调用（读取用户配置的 Key/模型）
│   │   └── dashboard_service.py
│   └── requirements.txt
│
├── desktop/                    # PySide6 桌面客户端
│   ├── main.py                 # 入口，启动 FastAPI 子进程 + 主窗口
│   ├── app.py                  # QApplication + 主窗口初始化
│   ├── views/                  # 页面视图（按模块拆分）
│   │   ├── login_view.py
│   │   ├── home_view.py        # 站会首页
│   │   ├── meeting_room_view.py
│   │   ├── ai_result_view.py
│   │   ├── todo_view.py
│   │   ├── dashboard_view.py
│   │   ├── team_view.py
│   │   └── settings_view.py    # 含 AI 设置子页面
│   ├── widgets/                # 可复用组件
│   │   ├── sidebar.py          # 左侧导航栏
│   │   ├── stat_card.py        # 关键数字卡片
│   │   ├── trend_chart.py      # matplotlib 折线图嵌入
│   │   ├── pie_chart.py        # matplotlib 饼图嵌入
│   │   ├── priority_badge.py
│   │   └── empty_state.py
│   ├── api/                    # 后端 API 调用封装
│   │   ├── client.py           # requests Session + WebSocket
│   │   ├── auth_api.py
│   │   ├── team_api.py
│   │   ├── meeting_api.py
│   │   ├── ai_api.py
│   │   ├── todo_api.py
│   │   └── dashboard_api.py
│   └── resources/              # 图标、样式
│
├── build.py                    # PyInstaller 打包脚本
└── requirements.txt            # 全项目依赖
```

---

## 二、Phase 0：基础设施搭建

**工期：1 天 | 依赖：无**

### 2.1 后端骨架

| 任务 | 内容 |
|:--:|------|
| P0-1 | FastAPI 项目初始化，创建目录结构和 `main.py` |
| P0-2 | MySQL 数据库创建 + SQLAlchemy 连接配置（`core/database.py`） |
| P0-3 | Alembic 迁移工具配置，初始迁移生成全部表 |
| P0-4 | JWT 认证中间件，`get_current_user` 依赖注入 |
| P0-5 | 统一响应格式 `{code, message, data}` |
| P0-6 | CORS 中间件配置（桌面端本地调用） |

### 2.2 桌面骨架

| 任务 | 内容 |
|:--:|------|
| P0-7 | PySide6 项目初始化，创建目录结构 |
| P0-8 | 主窗口框架（左侧 200px 侧边栏 + 右侧 QStackedWidget 内容区） |
| P0-9 | 侧边栏组件（Logo + 5 导航项 + 当前页高亮 + 用户信息区） |
| P0-10 | 全局暗色主题 QSS 样式表 |
| P0-11 | API 客户端封装（`requests.Session` + `websockets` 连接管理） |
| P0-12 | 后端自动启动：桌面 `main.py` 启动时 `subprocess.Popen` 拉起 FastAPI |

---

## 三、Phase 1：用户与认证

**工期：1 天 | 依赖：Phase 0**

### 3.1 数据库表

```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    avatar_url VARCHAR(500),
    ai_provider VARCHAR(50),          -- 用户配置的 AI 服务商
    ai_model VARCHAR(100),            -- 用户配置的模型名称
    ai_api_key VARCHAR(255),          -- 用户配置的 API Key（加密存储）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 API 端点

| 方法 | 路径 | 说明 |
|:--:|------|------|
| POST | `/api/auth/register` | 注册，返回用户信息 + JWT |
| POST | `/api/auth/login` | 登录，返回 JWT |
| GET | `/api/users/me` | 获取当前用户信息 |
| PUT | `/api/users/me` | 更新昵称、头像、AI 配置 |

### 3.3 桌面端

| 任务 | 内容 |
|:--:|------|
| P1-1 | 登录窗口（QDialog，用户名 + 密码 + 登录按钮） |
| P1-2 | 注册窗口（用户名 + 密码 + 确认密码 + 昵称） |
| P1-3 | Token 本地持久化（QSettings 存储 JWT），启动时自动登录 |
| P1-4 | 登录成功后切换到主窗口 |

---

## 四、Phase 2：团队与成员

**工期：1 天 | 依赖：Phase 1**

### 4.1 数据库表

```sql
CREATE TABLE teams (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    created_by VARCHAR(36) REFERENCES users(id),
    invite_code VARCHAR(6) UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE team_members (
    team_id VARCHAR(36) REFERENCES teams(id) ON DELETE CASCADE,
    user_id VARCHAR(36) REFERENCES users(id),
    role ENUM('tech_lead', 'scrum_master', 'developer', 'observer') DEFAULT 'developer',
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (team_id, user_id)
);
```

### 4.2 API 端点

| 方法 | 路径 | 说明 |
|:--:|------|------|
| GET | `/api/teams` | 我的团队列表 |
| POST | `/api/teams` | 创建团队（自动成为 Tech Lead） |
| GET | `/api/teams/{id}` | 团队详情（含成员列表和角色） |
| DELETE | `/api/teams/{id}` | 删除团队，仅 Tech Lead |
| POST | `/api/teams/{id}/invite` | 生成 6 位邀请码 |
| POST | `/api/teams/join` | 通过邀请码加入 |
| DELETE | `/api/teams/{id}/members/{uid}` | 移除成员 |
| PUT | `/api/teams/{id}/members/{uid}/role` | 修改成员角色，仅 Tech Lead |

### 4.3 桌面端

| 任务 | 内容 |
|:--:|------|
| P2-1 | 团队管理页面（QTableView 成员列表 + 邀请码展示区） |
| P2-2 | 创建团队对话框 |
| P2-3 | 邀请成员对话框（显示邀请码 + 复制按钮） |
| P2-4 | 加入团队对话框（输入邀请码） |
| P2-5 | 右键菜单：修改角色 / 移除成员（权限控制可见性） |

---

## 五、Phase 3：站会管理

**工期：1.5 天 | 依赖：Phase 2**

### 5.1 数据库表

```sql
CREATE TABLE meetings (
    id VARCHAR(36) PRIMARY KEY,
    team_id VARCHAR(36) REFERENCES teams(id) ON DELETE CASCADE,
    sprint_no VARCHAR(50),
    form_type ENUM('realtime', 'async') DEFAULT 'realtime',
    status ENUM('created', 'active', 'ended') DEFAULT 'created',
    ai_result TEXT,
    ai_status ENUM('idle', 'processing', 'done', 'failed') DEFAULT 'idle',
    ai_error TEXT,
    created_by VARCHAR(36) REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME
);

CREATE TABLE meeting_participants (
    meeting_id VARCHAR(36) REFERENCES meetings(id) ON DELETE CASCADE,
    user_id VARCHAR(36) REFERENCES users(id),
    speech_order INT,
    has_spoken BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (meeting_id, user_id)
);
```

### 5.2 API 端点

| 方法 | 路径 | 说明 |
|:--:|------|------|
| POST | `/api/meetings` | 创建站会 |
| GET | `/api/meetings/{id}` | 站会详情（含参会人和发言状态） |
| POST | `/api/meetings/{id}/start` | 开始站会，状态→active，WebSocket 广播 |
| POST | `/api/meetings/{id}/end` | 结束站会，归档 |
| PUT | `/api/meetings/{id}/order` | 更新发言顺序 |
| POST | `/api/meetings/{id}/skip/{uid}` | 跳过发言人 |
| GET | `/api/meetings?team_id=X` | 团队站会历史 |
| WS | `/ws/meetings/{id}` | 站会实时同步 |

### 5.3 桌面端

| 任务 | 内容 |
|:--:|------|
| P3-1 | 站会首页（并排卡片 + 历史 QTableView + 顶部工具栏按钮） |
| P3-2 | 创建站会对话框（选团队、日期、Sprint、参会人、实时/异步） |
| P3-3 | 站会状态机：已创建 → 进行中 → 已结束，按钮按状态动态切换 |
| P3-4 | 15 分钟倒计时器（QLabel，<2 分钟红色警告） |

---

## 六、Phase 4：站会发言 + WebSocket

**工期：2 天 | 依赖：Phase 3**

### 6.1 数据库表

```sql
CREATE TABLE meeting_speeches (
    id VARCHAR(36) PRIMARY KEY,
    meeting_id VARCHAR(36) REFERENCES meetings(id) ON DELETE CASCADE,
    speaker_id VARCHAR(36) REFERENCES users(id),
    yesterday TEXT,
    today TEXT,
    blockers TEXT,
    raw_text TEXT,
    input_method ENUM('text', 'paste') DEFAULT 'text',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2 WebSocket 消息协议

```json
{"type": "submit_speech", "speaker_id": "...", "yesterday": "...", "today": "...", "blockers": "..."}
{"type": "speech_update", "speaker_id": "...", "has_spoken": true}
{"type": "timer_sync", "remaining_seconds": 840}
{"type": "meeting_ended"}
```

### 6.3 桌面端

| 任务 | 内容 |
|:--:|------|
| P4-1 | 站会进行中页面（三栏分屏：参会成员 | 当前发言 | 已完成发言） |
| P4-2 | 三栏输入区（QTextEdit × 3：昨天 / 今天 / 阻碍） |
| P4-3 | 粘贴聊天记录入口（大文本输入框 → 发送到后端解析发言人） |
| P4-4 | WebSocket 实时同步（发言内容广播、状态更新、倒计时） |
| P4-5 | "发言完毕"按钮 → 提交发言 → 广播到其他成员 |
| P4-6 | 已完成发言区（右侧面板，只读摘要） |

---

## 七、Phase 5：AI 纪要 + AI 设置

**工期：1.5 天 | 依赖：Phase 4**

### 7.1 AI 服务设计

```
AIService (backend/services/ai_service.py)
├── analyze_meeting(speeches, api_config) → 三步流水线
│   Step 1: 发言人识别（粘贴场景）
│   Step 2: 逐人结构化
│   Step 3: 汇总 + Action Item
│
├── _call_llm(provider, model, api_key, messages) → 通用 LLM 调用
│   支持: 豆包 / 通义千问 / OpenAI 等 OpenAI 兼容 API
│
└── 容错: 30s 超时、重试 1 次、非 JSON 正则提取、失败降级
```

用户配置从 `users` 表读取 `ai_provider` / `ai_model` / `ai_api_key`，每次 AI 调用时动态传入，不硬编码。

### 7.2 API 端点

| 方法 | 路径 | 说明 |
|:--:|------|------|
| POST | `/api/meetings/{id}/analyze` | 触发 AI 整理（读取用户配置的 Key） |
| GET | `/api/meetings/{id}/ai-status` | 轮询 AI 状态（idle/processing/done/failed） |
| PUT | `/api/meetings/{id}/ai-result` | 保存人工编辑后的结果 |

### 7.3 桌面端

| 任务 | 内容 |
|:--:|------|
| P5-1 | AI 纪要结果页（2×2 网格：昨日完成 | 今日计划 / 阻碍汇总 | Action Item） |
| P5-2 | "AI 整理"按钮 → 加载动画 → 轮询状态 → 展示结果 |
| P5-3 | 点击条目内联编辑（QTextEdit 替换 QLabel） |
| P5-4 | AI 容错界面（失败时降级为原始文本 + 手动调整提示） |
| P5-5 | 设置页 → AI 设置子页面（服务商下拉 + 模型名称 + API Key 输入框 + 测试连接按钮） |
| P5-6 | AI 配置持久化（PUT `/api/users/me` 写入 `ai_*` 字段） |

---

## 八、Phase 6：待办管理

**工期：2 天 | 依赖：Phase 5**

### 8.1 数据库表

```sql
CREATE TABLE action_items (
    id VARCHAR(36) PRIMARY KEY,
    meeting_id VARCHAR(36) REFERENCES meetings(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    assignee_id VARCHAR(36) REFERENCES users(id),
    assigner_id VARCHAR(36) REFERENCES users(id),
    team_id VARCHAR(36) REFERENCES teams(id) ON DELETE CASCADE,
    due_date DATETIME,
    status ENUM('pending', 'in_progress', 'done', 'cancelled') DEFAULT 'pending',
    priority ENUM('high', 'medium', 'low') DEFAULT 'medium',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);
```

### 8.2 API 端点

| 方法 | 路径 | 说明 |
|:--:|------|------|
| GET | `/api/action-items` | 我的待办（按身份返回范围不同） |
| POST | `/api/action-items` | 手动创建待办 |
| PUT | `/api/action-items/{id}` | 更新待办状态/内容/责任人 |
| DELETE | `/api/action-items/{id}` | 删除待办，仅 Tech Lead |
| GET | `/api/meetings/{id}/unfinished-items` | 跨站会待办回顾 |
| PUT | `/api/meetings/{id}/confirm-items` | 批量确认待办状态 |

### 8.3 桌面端

| 任务 | 内容 |
|:--:|------|
| P6-1 | 待办管理页面（主从视图：左侧 QTableView + 右侧详情面板） |
| P6-2 | Tab 筛选栏（全部/待处理/进行中/已完成，带数量角标） |
| P6-3 | 批量操作（Shift/Ctrl 多选 → 标记完成/进行中） |
| P6-4 | 右键菜单（标记完成 / 进行中 / 编辑 / 转交 / 删除） |
| P6-5 | 新建待办对话框（内容 + 责任人 + 截止日期 + 优先级） |
| P6-6 | 跨站会回顾弹窗（新站会开始时自动弹出未完成待办列表） |

---

## 九、Phase 7：数据看板

**工期：1.5 天 | 依赖：Phase 3 + 4 + 6**

### 9.1 API 端点

| 方法 | 路径 | 说明 |
|:--:|------|------|
| GET | `/api/dashboard/summary?team_id=X` | 4 个关键数字（站会次数/出勤率/完成率/阻碍数） |
| GET | `/api/dashboard/attendance-trend?team_id=X` | 出勤率趋势数据 |
| GET | `/api/dashboard/completion-trend?team_id=X` | 完成率趋势数据 |
| GET | `/api/dashboard/blocker-distribution?team_id=X` | 阻碍类型分布 |
| GET | `/api/dashboard/member-ranking?team_id=X` | 成员完成排行 |

### 9.2 桌面端

| 任务 | 内容 |
|:--:|------|
| P7-1 | 看板页面（4 张 StatCard + 2 折线图 + 饼图 + 排行榜） |
| P7-2 | 折线图组件（matplotlib FigureCanvas 嵌入 QWidget，悬停 Tooltip） |
| P7-3 | 饼图组件（matplotlib 饼图，点击扇形高亮） |
| P7-4 | 排行榜组件（QTableWidget，前三名金银铜色标记） |
| P7-5 | Sprint 选择器（QComboBox 顶部工具栏） |

---

## 十、Phase 8：数据筛选

**工期：1 天 | 依赖：Phase 7**

不新增 API 端点，扩展 Phase 7 看板 API 的查询参数：

| 已有 API | 新增参数 |
|---------|---------|
| `/dashboard/summary` | `+ date_from`, `+ date_to` |
| `/dashboard/attendance-trend` | `+ user_id` |
| `/dashboard/completion-trend` | `+ user_id` |
| `/dashboard/blocker-distribution` | `+ blocker_type` |
| `/dashboard/member-ranking` | `+ sort_by` |

桌面端：

| 任务 | 内容 |
|:--:|------|
| P8-1 | 工具栏筛选下拉（Sprint / 阻碍类型 / 成员 / 时间范围） |
| P8-2 | 活跃筛选标签展示（可单独 × 移除） |
| P8-3 | 跨团队对比模式（并排两个看板视图） |
| P8-4 | 筛选无结果时的空状态 |

---

## 十一、Phase 9：数据管理

**工期：0.5 天 | 依赖：Phase 3 + 6**

| API | 说明 |
|-----|------|
| DELETE `/api/meetings/{id}` | 已有，Phase 3 |
| DELETE `/api/action-items/{id}` | 已有，Phase 6 |
| GET `/api/dashboard/export?team_id=X&format=csv` | 导出统计数据 |

桌面端：

| 任务 | 内容 |
|:--:|------|
| P9-1 | 右键删除（QTableView 中选中行 → 右键删除，权限控制） |
| P9-2 | 导出按钮（QFileDialog 选择保存路径 → 导出 CSV） |
| P9-3 | 图表导出（matplotlib 工具栏自带保存 PNG/SVG） |

---

## 十二、Parallel Phase：系统配置

**工期：0.5 天 | 可在任意阶段并行**

| 任务 | 内容 |
|:--:|------|
| PP-1 | 暗色/浅色主题切换（QSS 样式表动态替换） |
| PP-2 | 通知设置（桌面 Toast 弹窗：站会提醒/待办到期/分配通知，可开关） |
| PP-3 | AI 设置子页面（服务商下拉：豆包/通义/OpenAI/自定义 + 模型名 + API Key + 测试连接） |
| PP-4 | PyInstaller 打包配置（`build.py`，打包 FastAPI + 前端为单个 .exe） |

---

## 十三、依赖关系图

```
                    [系统配置 并行]
                         │
用户与认证 ──▶ 团队与成员 ──▶ 站会管理 ──▶ 站会发言+WS ──▶ AI纪要+设置 ──▶ 待办管理
                                                              │               │
                                                              ▼               ▼
                                                         数据看板 ◄────────────┘
                                                             │
                                                             ▼
                                                         数据筛选
                                                             │
                                                             ▼
                                                         数据管理
```

---

## 十四、工期汇总

| 阶段 | 模块 | 工期 | 累计 |
|:--:|------|:--:|:--:|
| P0 | 基础设施 | 1 天 | 1 天 |
| P1 | 用户与认证 | 1 天 | 2 天 |
| P2 | 团队与成员 | 1 天 | 3 天 |
| P3 | 站会管理 | 1.5 天 | 4.5 天 |
| P4 | 站会发言 + WebSocket | 2 天 | 6.5 天 |
| P5 | AI 纪要 + AI 设置 | 1.5 天 | 8 天 |
| P6 | 待办管理 | 2 天 | 10 天 |
| P7 | 数据看板 | 1.5 天 | 11.5 天 |
| P8 | 数据筛选 | 1 天 | 12.5 天 |
| P9 | 数据管理 | 0.5 天 | 13 天 |
| PP | 系统配置（并行） | 0.5 天 | — |
| **合计** | | **13 天** | |

---

*方案版本：V2.0 | 制定日期：2026-06-28 | 技术栈：PySide6 + FastAPI + MySQL*
