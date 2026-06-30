# 模块开发规格 — AI 纪要 + 数据看板 + 数据筛选

## 目标
在现有桌面骨架基础上，填充三个模块的实际业务逻辑，产出可演示的功能。

## 当前状态
- 桌面框架：已完成（8 个占位页面，侧边栏导航，暗色主题）
- 后端：不存在，用本地 Python 模块替代（后续可迁移至 Java）
- API 客户端：桩实现，返回固定占位数据

## 本次开发：三个模块

### 模块 A：AI 纪要引擎 (`services/ai_engine.py`)
- 三步 Prompt 流水线（Step1 发言人识别 / Step2 逐人结构化 / Step3 汇总+Action Item）
- LLM 调用客户端（OpenAI 兼容 API，支持豆包/通义/OpenAI）
- 容错：超时重试、非 JSON 正则提取、降级处理
- 所有函数独立、小巧

### 模块 B：数据看板引擎 (`services/dashboard_engine.py`)
- 聚合计算函数（出勤率/完成率/阻碍分布/排行）
- 筛选逻辑（Sprint/阻碍类型/时间段/成员/跨团队）
- 内置 mock 数据生成器（用于无后端时演示）
- 所有函数独立、小巧

### 模块 C：桌面视图集成（更新现有 views）
- `views/ai_result_view.py` — 接入 AI 引擎，展示真实三步结果
- `views/dashboard_view.py` — 接入看板引擎，展示真实聚合数据
- 看板页面增加筛选控件（工具栏下拉 + 活跃标签）
- 所有函数独立、小巧

## 接口约定

模块 A (ai_engine.py) 对外暴露：
- `AIConfig(provider, model, api_key)` — 配置数据类
- `parse_chat_log(text) -> list[dict]` — Step1 发言人识别
- `structure_speech(speaker, text) -> dict` — Step2 逐人结构化
- `summarize_meeting(structured_list) -> dict` — Step3 汇总+ActionItem
- `run_pipeline(speeches, config) -> dict` — 一键三步
- `call_llm(config, messages) -> str` — 通用 LLM 调用

模块 B (dashboard_engine.py) 对外暴露：
- `compute_summary(meetings, action_items) -> dict` — 4 关键数字
- `compute_attendance_trend(meetings) -> list` — 出勤趋势
- `compute_completion_trend(meetings, action_items) -> list` — 完成趋势
- `compute_blocker_distribution(meetings) -> list` — 阻碍分布
- `compute_ranking(action_items) -> list` — 成员排行
- `apply_filters(data, filters) -> data` — 筛选
- `generate_mock_data() -> dict` — mock 数据

模块 C (视图更新)：
- `AIResultView` — `activate()` 时调用 `run_pipeline()`
- `DashboardView` — `activate()` 时调用 `compute_*()` 系列函数
- 筛选器 UI（QComboBox + QChipLabel 工具栏）
