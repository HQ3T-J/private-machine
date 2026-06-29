# StandupSync Desktop — 基础框架构建规格

## 目标
构建可运行的 PySide6 桌面程序骨架：完整 UI 布局 + 页面切换 + 预留功能槽位，零业务逻辑。

## 项目路径
`E:\临时文件夹\standupsync_desktop\`

## 目录结构
```
standupsync_desktop/
├── main.py                    # 入口
├── theme.py                   # QSS 暗色主题样式
├── app.py                     # 主窗口 + 侧边栏 + 页面路由
├── api_client.py              # API 客户端桩（所有方法返回占位数据）
├── views/
│   ├── login_view.py          # 登录窗口
│   ├── home_view.py           # 站会首页
│   ├── meeting_room_view.py   # 站会进行中（三栏分屏）
│   ├── ai_result_view.py      # AI 纪要结果（2x2网格）
│   ├── todo_view.py           # 待办管理（表格+详情面板）
│   ├── dashboard_view.py      # 数据看板（4卡片+图表占位）
│   ├── team_view.py           # 团队管理（表格+权限按钮）
│   └── settings_view.py       # 设置（含 AI 设置子页）
└── widgets.py                 # StatCard, EmptyState, Toast
```

## 组件接口规范

### Sidebar (app.py 内)
- 信号: `navigated(page_index: int)` — 0=站会 1=待办 2=看板 3=团队 4=设置
- 方法: `set_active(index)`, `update_user(name, role)`, `set_notification(page_index, count)`

### 每个 View
- 构造函数: `__init__(self, api_client=None, parent=None)`
- 方法: `activate()` — 页面显示时调用（刷新数据等）
- 属性: `title` — 页面标题字符串

### API Client
- 单例，所有方法返回空占位数据
- 方法签名按需求文档的 API 端点命名

## 分派计划

子代理 A: 核心框架
- theme.py — 完整暗色 QSS
- main.py — 入口
- widgets.py — StatCard, EmptyState, Toast
- 交接: 提供 theme 和 widgets 给 B/C 使用

子代理 B: 登录 + 站会 + 设置
- views/login_view.py
- views/home_view.py
- views/meeting_room_view.py
- views/ai_result_view.py
- views/settings_view.py

子代理 C: 待办 + 看板 + 团队 + API 客户端 + 主窗口集成
- api_client.py
- views/todo_view.py
- views/dashboard_view.py
- views/team_view.py
- app.py (主窗口 + 侧边栏 + 页面路由，集成全部 view)

## 集成验证
- `python main.py` 启动后显示登录窗口
- 点击登录进入主窗口（无验证，直接通过）
- 侧边栏 5 个导航项可切换
- 每个页面显示占位内容
- 暗色主题全局生效
- 窗口最小 960×680
