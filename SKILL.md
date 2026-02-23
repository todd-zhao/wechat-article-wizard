---
name: wechat-article-wizard
description: 公众号文章自动化写作工具。支持选题规划、AI 写作、图片生成、HTML 排版、微信草稿发布全流程。
---

# WeChat Article Wizard (公众号写作助手)

## ⚠️ 重要提示 - Agent 必须遵守

**Agent 使用此 Skill 时必须严格遵守以下规则：**

### 🔴 绝对禁止

1. **禁止自己调用 API** - Agent 不能自己写代码调用任何 API 生成内容
2. **禁止重写脚本** - 不允许修改、删除或重写项目中的任何脚本
3. **禁止跳过脚本** - 必须使用项目提供的脚本来完成写作和发布

### ✅ 正确流程

```
用户请求创作文章
    ↓
1. 运行 quick_start.py 脚本（会自动调用配置的模型生成内容）
    ↓
2. 脚本会自动：
   - 调用配置的 WRITER_MODEL 生成文章
   - 调用配置的 IMAGE_GEN_MODEL 生成配图
   - 调用配置的 LAYOUT_MODEL 排版
   - 调用微信 API 推送到公众号草稿
    ↓
3. 返回结果给用户
```

### ⚙️ 配置

- **配置文件**: `config/setting.txt` 或 `.env`
- **模型配置**: WRITER_MODEL, LAYOUT_MODEL, IMAGE_GEN_MODEL
- **账号定位**: `prompts/account_strategy.md`

### ⚠️ 前置要求

**已预置 Python 环境（推荐）**
- 项目已包含 Python 3.12 便携版（`python-3.12.0rc3-embed-amd64/`）
- 解压后可直接运行，无需安装

**或使用系统 Python**
- 需要 Python 3.10+
- 下载地址：https://www.python.org/downloads/

---

## 🚀 正确的使用方式

### Agent 必须执行的完整流程：

```bash
# 1. 检查配置
python tools/auto_setup.py

# 2. 如果未配置，先配置（用户需要提供凭证）
python tools/auto_setup.py --credentials "用户凭证 1" "用户凭证 2" --api-key "用户的 api key"

# 3. 测试配置
python check_config.py

# 4. 开始写作（必须使用脚本！）
python quick_start.py "用户要求的文章主题"
```

**关键点**：
- **必须运行 `python quick_start.py`** 来生成文章
- **不要自己调用 API** - 脚本会自动调用配置的模型
- **不要自己排版** - 脚本会自动完成排版
- **不要自己推送** - 脚本会自动推送到微信草稿

---

## 配置说明

### 1. 配置文件（Agent 引导用户设置）

当用户首次使用时，Agent 必须引导用户完成以下设置：

#### 第一步：获取凭证
让用户提供：
- 微信 AppID 和 AppSecret（在 https://developers.weixin.qq.com/ 获取）
- CherryStudio API Key

**💡 还没有 CherryStudio API Key？**

推荐用户通过以下链接注册：
- 注册链接：**https://open.cherryin.ai/register?aff=gXKS**
- 注册后在 CherryStudio 设置中生成 API Key

#### 第二步：运行配置命令
```bash
python tools/auto_setup.py --credentials "用户凭证 1" "用户凭证 2" --api-key "用户的 api key"
```

### 2. 账号定位（Agent 引导用户设置）

首次使用时，Agent 必须引导用户设置 `prompts/account_strategy.md`：

让用户回答以下问题：
1. 目标读者是谁？
2. 核心价值是什么？
3. 希望以什么形象示人？
4. 写作风格偏好？
5. 主要写哪些内容？

然后将用户回答填充到 `prompts/account_strategy.md`

---

## 🔍 快速状态检查（Agent 专用）

Agent 可以通过以下方式快速检查项目状态：

### 方式 1：命令行检查

```bash
# 静默检查（仅返回退出码：0=通过，1=失败）
python tools/quick_check.py --silent

# 详细检查（显示所有检查项）
python tools/quick_check.py --verbose

# JSON 输出（供程序解析）
python tools/quick_check.py --json
```

### 方式 2：Python API

```python
from src.status_checker import StatusChecker

checker = StatusChecker(silent=True)
result = checker.check_all(skip_api=True)

if result.is_ready:
    # 所有检查通过，开始工作
    ...
else:
    # 输出缺失项
    for item in result.missing_items:
        print(f"缺失：{item}")
```

### 检查项目

| 检查项 | 说明 | 缺失时修复命令 |
|--------|------|---------------|
| Python 环境 | Python 3.10+ | 使用预置 Python 或安装 |
| 配置文件 | config/setting.txt | `python tools/auto_setup.py` |
| 账号定位 | prompts/account_strategy.md | 编辑文件填充内容 |
| 数据库 | content_wizard.db | 首次运行时自动创建 |
| 选题计划 | 待写的选题 | `python tools/add_new_topic.py "主题"` |

### JSON 输出示例

```json
{
  "is_ready": true,
  "python_ok": true,
  "config_ok": true,
  "strategy_ok": true,
  "database_ok": true,
  "has_plans": true,
  "missing_items": [],
  "warnings": []
}
```

---

## 📋 完整工作流程（Agent 必须遵循）

当用户请求创作公众号文章时，Agent **必须** 执行以下完整流程：

```
用户请求："帮我写一篇关于 XXX 的文章"
    ↓
【第一步】检查配置
    运行：python tools/auto_setup.py
    ↓
【第二步】如果未配置，引导用户配置
    运行：python tools/auto_setup.py --credentials <凭证 1> <凭证 2> --api-key <key>
    ↓
【第三步】测试配置
    运行：python check_config.py
    ↓
【第四步】开始写作（必须使用脚本！）
    运行：python quick_start.py "用户的主题"
    ↓
【脚本会自动完成以下全部工作】
    1. 调用 WRITER_MODEL 生成文章内容
    2. 调用 IMAGE_GEN_MODEL 生成封面和插图
    3. 上传图片到微信素材库
    4. 调用 LAYOUT_MODEL 进行 HTML 排版
    5. 自动推送到微信公众号草稿
    ↓
【返回结果给用户】
    - 微信草稿 ID
    - 文章预览链接
```

### ⚠️ 关键警告

**禁止 Agent 自行完成以下工作：**
- ❌ 自己调用 API 生成文章
- ❌ 自己调用 API 生成图片
- ❌ 自己排版 HTML
- ❌ 自己调用微信 API 推送

**必须使用脚本：**
- ✅ 运行 `python quick_start.py` 让脚本完成所有工作

---

## 🎨 排版风格管理

### 核心功能

**风格持久化**：一次选择，长期受益。设置默认风格后，之后写作自动使用，无需每次指定。

**智能读取**：`quick_start.py` 自动读取配置文件，命令行参数可临时覆盖。

**自定义风格**：支持创建和加载自定义风格模板。

### 预置排版风格

项目已预置 **5 种高级排版风格**：

| 风格 | 参数 | 主色调 | 适用场景 |
|------|------|--------|----------|
| 简洁（默认） | `default` | 蓝色 (#007AFF) | 通用内容 |
| 商务 | `business` | 深蓝 (#1E3A8A) | 企业、财经、职场 |
| 极简 | `minimalist` | 黑白灰 + 蓝 | 文艺、生活、成长 |
| 优雅 | `elegant` | 玫瑰金 (#B76E79) | 美妆、时尚、情感 |
| 创意 | `creative` | 渐变 (#6366F1→#EC4899) | 科技、互联网、年轻 |

### 使用方式

#### 1. 设置默认风格（长期有效）

```bash
# 设置商务风格为默认
python tools/set_style.py business

# 交互式设置（可预览效果）
python tools/set_style.py

# 查看当前风格
python tools/set_style.py --current

# 列出所有可用风格
python tools/set_style.py --list

# 重置为系统默认
python tools/set_style.py --reset
```

#### 2. 写作时自动使用默认风格

```bash
# 自动使用配置文件中的默认风格
python quick_start.py "AI 发展"

# 输出显示：排版风格：business (配置文件)
```

#### 3. 临时覆盖风格（仅本次有效）

```bash
# 默认是商务风格，但这次临时用极简风格
python quick_start.py "春日随笔" --style minimalist
```

### 配置文件

**位置：** `config/style_config.txt`

**内容示例：**
```ini
# 公众号写作助手 - 排版风格配置
default_style = business
total_articles = 127
last_used_style = business
last_used_date = 2026-02-23
```

---

## 使用方式

### 方式一：Claude Code Skill

```bash
/wechat-article-wizard
```

### 方式二：命令行

```bash
# 测试配置
python check_config.py

# 开始写作
python quick_start.py "文章主题"

# 使用特定风格
python quick_start.py "文章主题" --style business
```

## 功能列表

| 功能 | 说明 |
|------|------|
| 一键配置 | 自动获取 IP、验证配置 |
| 快速写作 | 输入主题，一键生成 |
| 选题管理 | 规划选题计划 |
| AI 写作 | 基于账号定位的深度内容 |
| 图片生成 | 电影写实风格配图 |
| HTML 排版 | 微信公众号优化格式 |
| 微信发布 | 自动创建草稿 |
| 风格管理 | 5 种预置风格 + 自定义 |

## 项目结构

```
wechat-article-wizard-skill/
├── SKILL.md                   # Skill 定义
├── README.md                  # 使用说明
├── setup.py                   # 安装脚本
├── quick_start.py             # 快速写作
├── execute_test_run.py        # 主程序
├── check_config.py            # 配置检查
├── requirements.txt           # Python 依赖
│
├── config/
│   ├── setting.txt            # API 配置
│   └── style_config.txt       # 风格配置
│
├── prompts/
│   ├── writer_agent.md        # 写作风格
│   ├── pattern_editor.md      # 排版样式（默认）
│   ├── pattern_business.md    # 商务风格
│   ├── pattern_minimalist.md  # 极简风格
│   ├── pattern_elegant.md     # 优雅风格
│   ├── pattern_creative.md    # 创意风格
│   ├── vision_editor.md       # 图片生成
│   ├── summary_agent.md       # 摘要生成
│   └── account_strategy.md    # 账号定位
│
├── src/
│   ├── config.py              # 配置管理
│   ├── style_config.py        # 风格配置管理
│   ├── db_manager.py          # 数据库
│   ├── article_orchestrator.py# 图片生成
│   ├── wechat_publisher.py    # 微信发布
│   └── dependency_checker.py  # 依赖检查
│
└── tools/
    ├── auto_setup.py          # 一键配置
    ├── set_style.py           # 风格设置
    └── list_plans.py          # 查看选题
```

---

**版本**: 2.5.1
**更新**: 2026-02-23

## 更新日志

### v2.5.1 (2026-02-23)
- 恢复状态检查功能（Agent 专用）
- 新增：`src/status_checker.py` - 简化版状态检查器
- 新增：`tools/quick_check.py` - 命令行快速检查工具
- 优化：状态检查支持 JSON 输出

### v2.5.0 (2026-02-23)
- 恢复强制脚本工作流
- 清理 Agent 自动写作模块
- 保留风格管理功能
- 恢复模板文件到初始状态

### v2.4.x
- 排版风格管理功能
- 5 种预置排版风格
- 自定义风格支持
