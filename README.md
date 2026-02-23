# WeChat Article Wizard - 公众号写作助手

简体中文 | [English](./README_EN.md)

## 概述

公众号写作助手是一个自动化公众号文章写作工具，支持选题规划、AI写作、图片生成、HTML排版、微信草稿发布全流程。

## 功能特点

- **选题管理** - 规划未来选题，跟踪写作状态
- **AI写作** - 基于账号定位的深度内容生成
- **图片生成** - 电影写实风格配图
- **自动排版** - 微信公众号优化HTML
- **一键发布** - 自动创建微信草稿

## 快速开始

### 1. 双击运行

```
双击 run.bat
```

### 2. 首次配置

按照提示输入：
- 微信公众号 AppID 和 AppSecret
- CherryStudio API Key

### 3. 设置账号定位

编辑 `prompts/account_strategy.md`，定义你的账号风格。

### 4. 开始写作

输入文章主题，自动完成：
1. AI深度写作
2. 电影风格配图
3. HTML精致排版
4. 微信草稿发布

## 使用方法

### Windows 用户

```bash
# 方式1: 双击 run.bat 选择菜单操作

# 方式2: 命令行运行
python execute_test_run.py           # 按选题列表写作
python quick_start.py                # 快速输入主题写作
python setup.py                      # 配置向导
python tools/config_wizard.py        # API配置
python tools/list_plans.py           # 查看选题
python tools/add_new_topic.py        # 添加选题
```

### 配置文件

编辑 `config/setting.txt`：

```ini
# 微信
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret

# CherryStudio API
CHERRY_API_BASE_URL=https://open.cherryin.ai/v1
CHERRY_API_KEY=your_api_key

# 模型
WRITER_MODEL=anthropic/claude-haiku-4.5
LAYOUT_MODEL=google/gemini-3-flash-preview
IMAGE_GEN_MODEL=qwen/qwen-image(free)
```

## 项目结构

```
wechat-article-wizard-skill/
├── run.bat                 # 双击运行入口
├── setup.py                # 一键安装配置
├── quick_start.py          # 快速写作
├── execute_test_run.py     # 主程序（按选题写作）
├── requirements.txt        # Python依赖
├── config/
│   └── setting.txt         # API配置
├── prompts/
│   ├── writer_agent.md     # 写作风格
│   ├── vision_editor.md    # 图片生成
│   ├── pattern_editor.md   # 排版样式
│   └── account_strategy.md # 账号定位
├── src/
│   ├── db_manager.py       # 数据库
│   ├── article_orchestrator.py  # 图片生成
│   ├── wechat_publisher.py # 微信发布
│   ├── task_scheduler.py   # 计划任务
│   └── dependency_checker.py # 依赖检查
├── tools/
│   ├── list_plans.py       # 查看选题
│   ├── add_new_topic.py    # 添加选题
│   └── config_wizard.py    # 配置向导
└── content_wizard.db       # 数据库文件
```

## 依赖

- Python 3.10+
- httpx / aiohttp
- python-dotenv
- fastapi (可选)

安装依赖：
```bash
pip install -r requirements.txt
```

## 常见问题

### 如何获取 AppID？

1. 登录 https://developers.weixin.qq.com/
2. 我的业务 → 选择公众号 → 基础信息 → 开发密钥
3. 查看 AppID 和 AppSecret

### API 连接失败？

1. 检查网络
2. 确认 API Key 正确
3. 检查 IP 白名单设置
4. 运行 `python tools/config_wizard.py` 测试

### 文章偏离主题？

系统已内置强制聚焦机制，确保内容围绕主题。

## 技术支持

- 详细文档：查看项目根目录 README.md
- 配置指南：查看 WECHAT_SETUP_GUIDE.md
- 问题反馈：创建 Issue

## License

MIT License
