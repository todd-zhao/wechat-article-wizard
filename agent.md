# Agent 使用指南

## ⚠️ 重要警告

**你必须严格按照以下规则执行，否则会导致项目失败！**

---

## 🔴 绝对禁止的行为

1. **禁止自行编写代码调用任何 API**
   - ❌ 不允许使用 httpx、aiohttp 等自行调用 API
   - ❌ 不允许使用 openai 库等调用模型
   - ❌ 不允许自己拼接请求参数

2. **禁止修改任何文件**
   - ❌ 不允许修改 .py 脚本
   - ❌ 不允许修改配置文件
   - ❌ 不允许修改提示词文件

3. **禁止跳过现有脚本**
   - ❌ 不允许自己实现功能
   - ❌ 不允许"简化"脚本逻辑

---

## ✅ 必须遵守的规则

### 1. 配置文件读取

从以下位置读取配置（优先级从高到低）：
```
1. config/setting.txt
2. .env 文件
```

### 2. 必须使用的脚本

所有功能必须通过以下脚本完成：

| 功能 | 必须使用的脚本 |
|------|---------------|
| 检查配置 | `python tools/auto_setup.py --check` |
| 配置账号 | `python tools/auto_setup.py --credentials <凭证1> <凭证2> --api-key <key>` |
| 测试配置 | `python test_config.py` |
| 写作文章 | `python quick_start.py "文章主题"` |

### 3. 正确的调用流程

```
用户请求创作公众号文章
    ↓
【第一步】检查配置状态
    命令: python tools/auto_setup.py --check
    ↓
【第二步】如果未配置，引导用户提供凭证
    - 微信 AppID 和 AppSecret
    - CherryStudio API Key
    ↓
【第三步】配置账号
    命令: python tools/auto_setup.py --credentials "凭证1" "凭证2" --api-key "key"
    ↓
【第四步】测试配置（可选）
    命令: python test_config.py
    ↓
【第五步】开始写作（必须使用脚本！）
    命令: python quick_start.py "用户的主题"
    ↓
【脚本会自动完成】
    ✓ 调用配置的模型生成文章
    ✓ 调用图片生成API生成配图
    ✓ 自动排版HTML
    ✓ 自动推送到微信草稿
    ↓
返回结果给用户
```

---

## 📋 常见任务示例

### 任务1：用户首次使用

```
用户：帮我设置一下
你的回复：
好的！让我先检查配置状态...
（运行 python tools/auto_setup.py --check）

请提供以下信息：
1. 微信 AppID 和 AppSecret（在 https://developers.weixin.qq.com/ 获取）
2. CherryStudio API Key

用户提供凭证后：
运行: python tools/auto_setup.py --credentials "凭证1" "凭证2" --api-key "key"
```

### 任务2：用户请求写文章

```
用户：帮我写一篇关于AI发展的文章
你的回复：
好的！我来为您创作文章。
（运行 python quick_start.py "AI发展"）

注意：如果配置未完成，先引导用户配置。
```

### 任务3：检查配置状态

```
运行: python tools/auto_setup.py --check
根据输出结果告知用户配置状态。
```

---

## ⚠️ 错误示例

### 错误1：自行调用 API

```python
# ❌ 错误做法
import httpx
response = await httpx.AsyncClient().post(url, json={...})
```

### 错误2：自己拼接 HTML

```python
# ❌ 错误做法
html = "<html>..." + content + "</html>"
```

### 错误3：修改脚本

```python
# ❌ 错误做法
# 修改 quick_start.py 的逻辑
```

---

## ✅ 正确做法

```python
# ✅ 正确做法
import subprocess
result = subprocess.run(
    ["python", "quick_start.py", "文章主题"],
    capture_output=True,
    text=True
)
print(result.stdout)
```

---

## 📞 总结

**记住：你的角色是"运行脚本"，不是"实现功能"！**

1. 用户提出需求
2. 你运行相应的脚本
3. 返回脚本的输出结果
4. 如果出错，根据错误信息引导用户解决

**不要尝试自己实现任何功能！**
