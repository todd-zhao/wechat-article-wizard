# 快速开始指南

## 第一次使用

### 1. 安装依赖

```bash
pip install python-dotenv
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入您的真实配置
# - WECHAT_APP_ID: 微信公众号 AppID
# - WECHAT_APP_SECRET: 微信公众号 AppSecret
# - CHERRY_API_KEY: CherryStudio API Key
```

### 3. 运行程序

```bash
python execute_test_run.py
```

## 安全提示

- ⚠️ **切勿** 将 `.env` 文件提交到 Git
- ✅ 已添加到 `.gitignore`，自动保护敏感信息
- 🔒 生产环境建议在系统环境变量中配置
