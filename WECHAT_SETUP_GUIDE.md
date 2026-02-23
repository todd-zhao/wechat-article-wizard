# 🔑 微信公众号配置指南

本文档说明如何获取公众号开发所需的凭证信息。

---

## 重要提示

**获取凭证的网址是「微信开发者平台」，不是公众平台！**

| 平台 | 网址 | 用途 |
|------|------|------|
| 微信开发者平台 | https://developers.weixin.qq.com/ | 获取 AppID 和 AppSecret |
| 微信公众号后台 | https://mp.weixin.qq.com/ | 内容发布和管理 |

---

## 获取步骤

### 1. 打开微信开发者平台

访问 https://developers.weixin.qq.com/

### 2. 扫码登录

使用微信公众号管理员微信扫码登录

### 3. 进入凭证页面

点击「我的业务」→ 选择您的公众号 → 「基础信息」→「开发密钥」

### 4. 获取 AppID

在页面上可以看到 AppID（应用标识），格式为 `wx` 开头的字母数字组合

### 5. 获取 AppSecret

点击 AppSecret 的「查看」或「重置」按钮

**重要**：
- AppSecret 只显示一次，请立即保存
- 如果忘记只能重置，重置后旧的会失效

---

## 配置 IP 白名单

### 作用

开启IP白名单后，只有白名单内的IP地址才能调用公众号API。

### 设置步骤

1. 同样在「开发密钥」页面
2. 找到「IP白名单」选项
3. 点击「添加」
4. 输入您的公网IP

### 查询本机IP

运行以下命令：

```bash
python tools/get_my_ip.py
```

---

## 常见错误

### 错误码 40164 - IP不在白名单

解决：将本机IP添加到白名单

### 错误码 40013 - AppID无效

解决：检查AppID是否填写正确

### 错误码 40001 - AppSecret错误

解决：AppSecret可能已重置，需要使用最新的

---

## 配置示例

获取凭证后，编辑 `config/setting.txt`：

```ini
WECHAT_APP_ID=wx开头的标识
WECHAT_APP_SECRET=一串字母数字
CHERRY_API_KEY=您的API密钥
```
