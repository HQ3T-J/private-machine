# StandupSync 产品全貌 V1.0

> 最后更新：2026-06-28 | 本文档为产品唯一真相源，后续所有研发决策以此为准

---

## 一、产品定义

| 维度 | 内容 |
|------|------|
| **产品名** | StandupSync —— 智能站会速记与待办追踪 |
| **一句话** | AI 驱动的敏捷团队站会工具：语音/文字输入 → AI 自动结构化纪要 → 待办自动分发追踪 |
| **锚定行业** | 敏捷开发协作工具 / Agile Team Collaboration |
| **核心价值** | 把站会从"记录型工具"升级为"管理型工具"——纪要自动生成、待办闭环追踪、数据驱动决策 |
| **平台** | PC 桌面（PySide6 + Java Spring Boot 后端 + MySQL，PyInstaller 打包独立 .exe） |
| **AI 引擎** | 用户自行配置 API Key 与模型（豆包/通义千问/OpenAI 等），后端统一代理调用 |

---

## 二、用户与角色

### 2.1 业务干系人（3 类，11 种子身份）

```
管理与协调层
├── Tech Lead          全权限，跨团队
└── Scrum Master       本团队，不可删数据/改身份

执行层（权限统一）
├── Frontend Developer
├── Backend Developer
├── UI/UX Designer
├── QA Engineer
└── DevOps Engineer

决策与观察层（全部只读）
├── Product Owner      关注功能交付，按 Sprint 筛选
├── CTO                 关注团队效能，按阻碍类型筛选 + 跨团队
├── Department Head     关注投入产出，跨团队 + 时间段对比
└── Instructor          关注进度与参与度，跨团队 + 排行
```

### 2.2 系统 RBAC 角色（4 种）

| 角色 | 团队管理 | 站会管理 | 站会发言 | AI 能力 | 待办范围 | 看板范围 | 数据删除 |
|------|:------:|:------:|:------:|:------:|:------:|:------:|:------:|
| Tech Lead | 全部 | 全部 | 有 | 有 | 全部人 | 跨团队 | 有 |
| Scrum Master | 本团队 | 本团队 | 有 | 有 | 全部人 | 本团队 | 无 |
| Developer | 无 | 无 | 有 | 无 | 仅自己 | 仅自己 | 无 |
| Observer | 无 | 无 | 无 | 无 | 只读 | 全团队 | 无 |

### 2.3 权限 → 界面映射

| 身份 | 底部 Tab | 侧边栏菜单 |
|------|---------|----------|
| Tech Lead | 站会 / 待办 / 看板 / 我的 (4) | 站会 / 待办 / 看板 / 团队 / 设置 (5) |
| Scrum Master | 同上 (4) | 同上 (5) |
| Developer | 站会 / 我的待办 / 我的数据 (3) | 站会 / 待办 / 看板 / 设置 (4) |
| Observer | 纪要 / 看板 (2) | 站会(只读) / 看板 / 设置 (3) |

---

## 三、技术架构

```
┌─────────────────────────────────────────┐
│     PC Desktop (PySide6, Python)         │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│  │ 站会  │ │ AI   │ │ 待办  │ │ 看板  │   │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘   │
│     └────────┴────────┴────────┘        │
│  ┌──────────────────────────────────┐   │
│  │ QTableView + QListWidget 列表     │   │
│  │ matplotlib 图表嵌入 Qt            │   │
│  │ requests + websockets 网络层      │   │
│  │ PySide6 原生主题（暗色默认）       │   │
│  └──────────────────────────────────┘   │
┌──────────────────┬──────────────────────┐
                   │ HTTP + WebSocket
┌──────────────────┴──────────────────────┐
│      Java Spring Boot 后端               │
│  ┌──────────┐ ┌──────────┐ ┌────────┐  │
│  │ REST API │ │WebSocket │ │AI Proxy│  │
│  │(SpringMVC)│ │(SpringWS)│ │(OkHttp)│  │
│  └────┬─────┘ └────┬─────┘ └───┬────┘  │
│       └────────────┴───────────┘        │
│  ┌──────────────────────────────────┐   │
│  │ Spring Data JPA + MySQL          │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

| 层 | 技术 | 理由 |
|----|------|------|
| Desktop | PySide6 (Qt for Python) | 原生桌面控件、暗色主题、PyInstaller 打包 .exe |
| 图表 | matplotlib 嵌入 PySide6 | 折线图/饼图/柱状图，交互式 Tooltip |
| 网络 | requests + websockets | HTTP REST + WebSocket，纯 Python |
| 打包 | PyInstaller | 单文件 .exe 分发 |
| 后端 | Java Spring Boot 3 + Spring Data JPA | 企业级框架，JPA 自动建表，Spring WebSocket 实时通信 |
| 数据库 | MySQL | Spring Data JPA 管理，桌面端通过 REST API 间接访问 |
| AI 代理 | OkHttp（Java HTTP 客户端） | 后端读取用户 AI 配置，代理调用各 AI 服务商 |
| 构建 | Maven | Java 项目标准构建工具 |

---

## 四、功能模块全景

### 4.1 模块拓扑

```
用户与认证 ──▶ 团队与成员 ──▶ 站会管理 ──▶ 站会发言+WS ──▶ AI 纪要 ──▶ 待办管理
                                                              │           │
                                                              ▼           ▼
系统配置（并行）                                           数据看板 ◄────────┘
                                                             │
                                                             ▼
                                                         数据筛选
                                                             │
                                                             ▼
                                                         数据管理
```

### 4.2 十大模块 71 项功能

| 一级模块 | 二级子模块 | 功能数 | 核心职责 |
|---------|-----------|:----:|---------|
| 团队与成员 | 团队管理、成员管理 | 5 | 团队 CRUD + 邀请码 + 角色分配 |
| 站会管理 | 站会生命周期、会议主持 | 8 | 创建/开始/结束站会 + 倒计时 + 发言顺序 |
| 站会发言 | 结构化输入、语音输入、粘贴记录、实时同步 | 9 | 三栏填写 + 语音转文字 + WebSocket 广播 |
| AI 纪要 | AI 结构化、纪要编辑与归档 | 6 | 三步 Prompt 流水线 + 结果编辑 + 容错降级 |
| 待办管理 | 待办生成、待办指派、状态流转、跨站会回顾、通知 | 16 | AI 自动生成 + 手动 + 状态机 + 回顾闭环 |
| 数据看板 | 关键指标、趋势图表、排行榜 | 7 | 4 卡片 + 折线图 + 饼图 + 排行 |
| 数据筛选 | 维度筛选、范围筛选 | 5 | Sprint/阻碍类型/时间段/跨团队/成员 |
| 数据管理 | 数据清理、数据导出 | 4 | 删除 + PNG/CSV 导出 |
| 用户与认证 | 账号管理 | 4 | 注册/登录/JWT/个人中心 |
| 系统配置 | 主题与通知、部署平台、离线同步 | 7 | 暗色模式/通知开关/离线队列 |
| **合计** | **20 个子模块** | **71** | |

### 4.3 核心业务闭环

```
站会 N 创建 → 成员轮流发言 → AI 整理纪要 → 确认归档
    │                                        │
    │                                  自动生成待办 → 分配责任人
    │                                        │
    │                                  成员完成/更新待办
    │                                        │
    └──── 站会 N+1 开始 → 自动弹出上次未完成待办 ← ┘
              │
         逐项确认 → 更新状态 → 统计完成率 → 写入看板
```

---

## 五、数据模型（核心表）

```
users ───┐
         ├── team_members (user_id, team_id, role)
teams ───┘
         │
meetings (team_id, status, form_type, ai_result)
         │
         ├── meeting_participants (meeting_id, user_id, speech_order, has_spoken)
         │
         └── meeting_speeches (meeting_id, speaker_id, yesterday, today, blockers)
                        │
                  AI 整理 → meetings.ai_result (JSON)
                        │
                  ┌─────┘
                  ▼
action_items (meeting_id, assignee_id, content, status, priority, due_date)
```

关键数据流：发言 → AI 纪要 → `ai_result` JSON → 提取 Action Item → `action_items` 表 → 看板聚合查询

---

## 六、界面设计

### 6.1 界面布局

PC Desktop 界面示例图位于 `E:\临时文件夹\diagrams\`（6 张 Excalidraw 图）。

| 维度 | 规范 |
|------|------|
| 导航 | 左侧 200px 固定侧边栏（Logo + 5 导航项 + 用户信息） |
| 设置菜单 | 包含个人信息、AI 设置（子菜单：API 服务商选择、模型名称、API Key）、通知开关、主题切换 |
| 详情展开 | 右侧固定详情面板（主从视图） |
| 主操作 | 顶部工具栏按钮 + Ctrl+快捷键 |
| 列表操作 | 右键菜单 + 批量勾选 |
| 筛选 | 工具栏下拉即时生效 |
| 图表 | matplotlib 嵌入 Qt（折线图、饼图、柱状图） |
| 键盘快捷键 | Ctrl+N/Ctrl+Enter/E/I/Delete/Space/Esc/Ctrl+F 等 11 个 |
| 字体 | 标题 18sp、正文 14sp、辅助 12sp |
| 圆角 | 卡片 12dp / 按钮 8dp |
| 暗色背景 | #1A1A2E / 卡片 #16213E（暗色默认） |
| 窗口 | 最小 800×600，标准 960×680，站会页 1024×720 |

---

## 七、研发方案

### 7.1 开发阶段

| 阶段 | 模块 | 工期 | 核心产出 |
|:--:|------|:--:|---------|
| P0 | 基础设施 | 1 天 | FastAPI 骨架 + PySide6 项目 + 数据库 |
| P1 | 用户与认证 | 1 天 | 注册/登录/JWT（后端 API + PySide6 UI） |
| P2 | 团队与成员 | 1 天 | 团队 CRUD + 邀请码 + 角色分配 |
| P3 | 站会管理 | 1.5 天 | 站会状态机 + WebSocket 房间 |
| P4 | 站会发言 | 2 天 | 三栏输入 + 粘贴聊天记录 + WS 实时同步 |
| P5 | AI 纪要 | 1.5 天 | 三步 Prompt 流水线 + 结果编辑 |
| P6 | 待办管理 | 2 天 | 自动生成 + 状态流转 + 跨站会回顾 |
| P7 | 数据看板 | 1.5 天 | 聚合查询 + matplotlib 图表 |
| P8 | 数据筛选 | 1 天 | 看板 API + 查询参数 + 筛选 UI |
| P9 | 数据管理 | 0.5 天 | 删除 + 导出 |
| PP | 系统配置 | 0.5 天 | 暗色模式 + 通知 + PyInstaller 打包 |
| **合计** | | **13 天** | |

### 7.2 模块独立化

每个一级模块拥有独立的三层接口：

| 层 | Desktop (PySide6) | 后端 (Spring Boot) |
|----|-------------------|---------------------|
| 本地 | 无（所有数据通过 API） | — |
| 远程 | requests + websockets | Spring MVC REST + Spring WebSocket |
| 实时 | websockets | Spring WebSocket |

模块间仅通过上述三层通信，不直接引用对方内部实现。

---

## 八、AI 方案

### 8.1 三步 Prompt 流水线

```
Step 1: 发言人识别（仅粘贴聊天记录场景）
  输入: 原始聊天文本
  输出: [{speaker, content}, ...]

Step 2: 逐人结构化
  输入: 单人发言文本
  输出: {speaker, yesterday: [], today: [], blockers: [{content, type}]}

Step 3: 汇总 + 提取 Action Item
  输入: 全员结构化结果
  输出: {summary, actions: [{content, assignee, priority, due_hint}]}
```

### 8.2 容错策略

| 场景 | 处理 |
|------|------|
| LLM 超时 | 30s 超时，重试 1 次 |
| 返回非 JSON | 正则提取，失败则标记 `ai_status=failed` |
| API 不可用 | 降级为原始文本 + "请手动整理" |
| 发言为空 | 不调 AI，返回空结构 |

---

## 九、关键设计决策

| 编号 | 决策 | 理由 |
|:--:|------|------|
| D1 | PySide6 桌面程序 | 原生 Qt 控件、暗色主题、PyInstaller 打包独立 .exe |
| D2 | matplotlib 嵌入 Qt | Python 原生图表库，支持交互式 Tooltip 与缩放 |
| D3 | 粘贴聊天记录为主入口 | 桌面端语音使用率低，IM 粘贴最务实 |
| D4 | 阻碍分类前置到 AI Prompt | 一次 LLM 调用同时输出分类标签，零额外成本 |
| D5 | P8 不新增 API | 数据筛选复用 P7 看板 API + query params |
| D6 | Spring Boot 后端 | 企业级 Java 框架，Spring Data JPA 自动建表，Spring WebSocket 原生支持 |
| D7 | MySQL 数据库 | FastAPI 后端统一访问，桌面端通过 API 间接读写 |
| D8 | OkHttp AI 代理 | Java HTTP 客户端，统一代理用户配置的各 AI 服务商 API |

---

## 十、产出物清单

| 文件 | 路径 | 说明 |
|------|------|------|
| 需求文档 | `.hermes/desktop-attachments/团队站会速记工具需求文档V1.0.md` | 原始需求 |
| 优化方案 | `.hermes/desktop-attachments/2026-06-27_StandupSync-智能站会速记-优化方案.md` | Web 端详细设计 |
| 移动端方案 | `.hermes/desktop-attachments/2026-06-27_StandupSync-移动端优化方案.md` | Android 架构设计 |
| 功能列表 | `E:\临时文件夹\StandupSync_功能列表_V1.0.xlsx` | 71 项功能 Excel |
| 研发方案 | `E:\临时文件夹\StandupSync_产品研发方案.md` | 13 天分阶段计划 |
| 个人方案 | `E:\临时文件夹\AI纪要_数据看板_数据筛选_个人研发方案.md` | P5+P7+P8 详细方案 |
| 界面方案 | `E:\临时文件夹\StandupSync_界面设计方案.md` | 移动+PC 完整 UI |
| 界面示例图 | `E:\临时文件夹\diagrams\` | 6 张 PC 端 Excalidraw 图 |
| 产品全貌 | `E:\临时文件夹\StandupSync_产品全貌.md` | 本文档 |

---

*本文档为 StandupSync 唯一真相源，后续修改需同步更新此文档。*
