# Ithaca

Ithaca 是一个基于 LLM Agents 的 Meta Ads 营销自动化平台，能够自动创建、执行和评估营销计划。

## 项目结构

### 核心目录

#### `/ithaca/` - 主要代码目录

**主要文件：**

- `main.py` - 系统主入口，提供命令行接口启动调度器
- `scheduler.py` - 核心调度器，支持后台运行和前台运行模式
- `scheduler_cli.py` - 调度器命令行控制工具
- `settings.py` - 全局配置文件，包含 API 密钥和系统设置
- `utils.py` - 通用工具函数，如缓存目录管理
- `logger.py` - 全局日志系统

#### `/ithaca/agents/` - AI 智能体模块

**核心文件：**

- `agent_types.py` - 定义营销计划数据模型和类型
- `holisticagent.py` - 全能营销智能体，负责端到端营销计划创建和执行
- `evalagent.py` - 评估智能体，负责营销计划效果评估和优化

**子智能体 (`/subagents/`)：**

- `plan_agent.py` - 计划制定智能体
- `research_agent.py` - 市场调研智能体
- `execute_agent.py` - 执行智能体
- `evaluate_agent.py` - 评估智能体

#### `/ithaca/tools/` - 工具集成模块

**核心工具：**

- `webtools.py` - 网页内容抓取和分析工具
- `random.py` - 随机数生成工具

**Meta API 集成 (`/meta_api/`)：**

- `meta_ads_api.py` - Meta Ads API 核心接口
- `utils.py` - API 工具辅助函数和错误处理
- `meta_ads_*.py` - 各种 Meta Ads 功能模块：
  - 广告账户管理 (`meta_ads_adaccount.py`)
  - 广告系列管理 (`meta_ads_campaign.py`)
  - 广告组管理 (`meta_ads_adset.py`)
  - 广告管理 (`meta_ads_ad.py`)
  - 创意管理 (`meta_ads_creative.py`)
  - 图片管理 (`meta_ads_ad_image.py`)
  - 受众定位 (`meta_ads_targeting.py`)
  - 数据洞察 (`meta_ads_insights.py`)
  - 预算管理 (`meta_ads_budget.py`)
  - 页面管理 (`meta_ads_page.py`)
  - 受众估算 (`meta_ads_audience_estimate.py`)

#### `/ithaca/db/` - 数据库模块

- `ithacadb.py` - 数据库操作接口，支持 SQLite
- `history.py` - 营销历史数据模型

#### `/ithaca/llms/` - 大语言模型集成

- `base.py` - LLM 基础抽象类
- `gemini.py` - Google Gemini 模型集成

#### `/ithaca/oauth/` - OAuth 认证模块

- `auth.py` - Meta API OAuth 认证管理
- `callback_server.py` - OAuth 回调服务器

#### `/ithaca/workflow/` - 工作流模块

- `base.py` - 工作流基础抽象类
- `holistic_workflow.py` - 全能营销工作流实现

## 功能特性

### 🤖 智能营销计划生成

- 基于产品信息自动生成 3-5 个营销计划
- 支持历史数据分析和优化建议
- 集成 Meta Ads API 实现自动化广告投放

### 📊 营销效果评估

- 自动收集广告投放数据
- 智能评估营销计划效果（1-10 分评分）
- 提供优化建议和改进方案

### ⏰ 自动化调度系统

- 支持后台守护进程运行
- 可配置执行间隔（默认 1 小时）
- 命令行控制：启动、暂停、恢复、停止

### 🔐 安全认证

- Meta API OAuth 2.0 认证
- 访问令牌自动管理和刷新
- 安全的本地缓存机制

### 💾 数据持久化

- SQLite 数据库存储营销历史
- 支持复杂查询和数据分析
- 自动备份和恢复机制

## 快速开始

### 1. 启动营销调度器

```bash
# 前台运行
python -m ithaca.main start --product-name "智能手表" --product-url "https://example.com" --budget 10000

# 后台运行
python -m ithaca.main start --product-name "智能手表" --product-url "https://example.com" --budget 10000 --daemon
```

### 2. 控制调度器

```bash
# 查看状态
python -m ithaca.scheduler_cli status

# 暂停调度器
python -m ithaca.scheduler_cli pause

# 恢复调度器
python -m ithaca.scheduler_cli resume

# 停止调度器
python -m ithaca.scheduler_cli stop
```

### 3. 配置参数

主要配置项在 `settings.py` 中：

- `META_APP_ID` - Meta 应用 ID
- `META_APP_SECRET` - Meta 应用密钥
- `GEMINI_API_KEY` - Google Gemini API 密钥

## 系统架构

```
用户输入 → 调度器 → 全能工作流 → AI 智能体 → Meta API → 效果评估 → 数据存储
```

1. **调度器层**：管理任务执行时间和状态
2. **工作流层**：协调各个智能体的执行顺序
3. **智能体层**：负责具体的营销任务（研究、计划、执行、评估）
4. **工具层**：提供 API 集成和辅助功能
5. **数据层**：持久化存储和历史数据管理

## 技术栈

- **AI 框架**: LangChain + Google Gemini
- **API 集成**: Meta Graph API
- **数据库**: SQLite + SQLModel
- **认证**: OAuth 2.0
- **调度**: 自研调度器
- **日志**: Python logging

## 开发说明

系统采用模块化设计，各模块职责清晰：

- 智能体负责 AI 决策
- 工具模块负责外部集成
- 数据库模块负责数据持久化
- 调度器负责任务管理
- 工作流负责流程编排

每个模块都有清晰的接口定义，便于扩展和维护。
