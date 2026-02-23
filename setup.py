"""
公众号写作助手 - 一键安装脚本
自动检测环境、安装依赖、配置参数
"""

import os
import sys
import subprocess
import asyncio

# Windows 编码设置
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def print_banner():
    print("=" * 60)
    print("   公众号写作助手 - 智能安装向导")
    print("   WeChat Article Wizard - Auto Setup")
    print("=" * 60)
    print()

def check_python():
    """检查Python版本"""
    print("[1/5] 检查Python环境...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"   [ERROR] 需要Python 3.10+, 当前版本: {version.major}.{version.minor}")
        print("   请访问 https://www.python.org/downloads/ 下载安装")
        return False
    print(f"   [OK] Python {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """安装Python依赖"""
    print("\n[2/5] 安装Python依赖...")
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")

    if not os.path.exists(req_file):
        print(f"   [ERROR] 找不到 requirements.txt")
        return False

    try:
        print("   正在安装依赖包，请稍候...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_file],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            print("   [OK] 依赖安装成功")
            return True
        else:
            print(f"   [WARN] 安装过程有警告: {result.stderr[:200]}")
            # 继续尝试，因为可能是非关键警告
            return True
    except Exception as e:
        print(f"   [ERROR] 安装失败: {e}")
        return False

def check_config():
    """检查配置文件"""
    print("\n[3/5] 检查配置文件...")
    config_dir = os.path.join(os.path.dirname(__file__), "config")

    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        print("   [INFO] 创建配置目录")

    config_file = os.path.join(config_dir, "setting.txt")
    if not os.path.exists(config_file):
        # 创建默认配置
        default_config = """# 公众号写作助手 配置文件
# 请编辑以下配置项

# ==================== 微信公众平台 ====================
# 在微信开发者平台 https://developers.weixin.qq.com/ 获取
WECHAT_APP_ID=your_app_id_here
WECHAT_APP_SECRET=your_app_secret_here

# ==================== CherryStudio API ====================
# 在 CherryStudio 设置中获取 API Key
CHERRY_API_BASE_URL=https://open.cherryin.ai/v1
CHERRY_API_KEY=your_api_key_here

# ==================== 模型配置 ====================
# 写作模型 (推荐使用 claude-haiku-4.5 或 claude-sonnet-4.5)
WRITER_MODEL=anthropic/claude-haiku-4.5

# 排版模型 (用于HTML生成和摘要)
LAYOUT_MODEL=google/gemini-3-flash-preview

# 图片生成模型
IMAGE_GEN_MODEL=qwen/qwen-image(free)
"""
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(default_config)
        print(f"   [INFO] 已创建配置文件: {config_file}")
        print("   [IMPORTANT] 请编辑配置文件，填入您的API密钥")
        return False
    else:
        # 检查配置是否完整
        with open(config_file, "r", encoding="utf-8") as f:
            content = f.read()

        required_keys = ["WECHAT_APP_ID", "WECHAT_APP_SECRET", "CHERRY_API_KEY"]
        missing = []
        for key in required_keys:
            if key not in content or "your_" in content.lower() or key not in content:
                missing.append(key)

        if missing:
            print(f"   [WARN] 缺少配置项: {', '.join(missing)}")
            return False
        print("   [OK] 配置文件完整")
        return True

def check_strategy():
    """检查账号定位"""
    print("\n[4/5] 检查账号定位...")
    strategy_file = os.path.join(os.path.dirname(__file__), "prompts", "account_strategy.md")

    prompts_dir = os.path.dirname(strategy_file)
    if not os.path.exists(prompts_dir):
        os.makedirs(prompts_dir)

    if not os.path.exists(strategy_file) or os.path.getsize(strategy_file) < 50:
        # 创建默认账号定位
        default_strategy = """# 账号定位策略

## 目标读者
- 读者画像：企业主、创业者、职场人士
- 年龄：25-45岁
- 痛点：效率提升、业绩增长、焦虑缓解

## 核心价值
- 专业实用
- 有深度有见解
- 可操作性强

## 写作风格
- 干货型（少水份，多干货）
- 犀利直接（不绕弯子）
- 冷幽默（适度调侃）
- 案例驱动（多用真实案例）

## 内容调性
- 自信但不傲慢
- 专业但不高高在上
- 有态度但不偏激
- 关注实操和效果
"""
        with open(strategy_file, "w", encoding="utf-8") as f:
            f.write(default_strategy)
        print(f"   [INFO] 已创建账号定位文件: {strategy_file}")
        print("   [TIP] 可以编辑此文件自定义您的账号风格")
        return False

    print("   [OK] 账号定位已设置")
    return True

def check_database():
    """检查数据库"""
    print("\n[5/5] 初始化数据库...")
    db_file = os.path.join(os.path.dirname(__file__), "content_wizard.db")

    # 数据库会在首次运行时自动创建
    if os.path.exists(db_file):
        print("   [OK] 数据库已存在")
    else:
        print("   [INFO] 数据库将在首次运行时自动创建")
    return True

async def test_connection():
    """测试API连接"""
    print("\n[测试] 验证API连接...")

    # 读取配置
    config_file = os.path.join(os.path.dirname(__file__), "config", "setting.txt")
    config = {}
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    config[k] = v
    except:
        print("   [SKIP] 无法读取配置，跳过测试")
        return False

    # 测试微信连接
    if "WECHAT_APP_ID" in config and "WECHAT_APP_SECRET" in config:
        if "your_" not in config.get("WECHAT_APP_ID", ""):
            print("   正在测试微信API...")
            try:
                import httpx
                url = "https://api.weixin.qq.com/cgi-bin/token"
                params = {
                    "grant_type": "client_credential",
                    "appid": config["WECHAT_APP_ID"],
                    "secret": config["WECHAT_APP_SECRET"]
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(url, params=params)
                    data = resp.json()
                    if "access_token" in data:
                        print("   [OK] 微信API连接成功")
                    else:
                        print(f"   [WARN] 微信API返回: {data.get('errmsg', '未知错误')}")
            except Exception as e:
                print(f"   [ERROR] 微信API测试失败: {e}")

    return True

def main():
    print_banner()

    # 步骤1: 检查Python
    if not check_python():
        print("\n[FAILED] Python环境检查未通过")
        input("\n按回车键退出...")
        sys.exit(1)

    # 步骤2: 安装依赖
    if not install_dependencies():
        print("\n[WARNING] 依赖安装有问题，但可以继续尝试")

    # 步骤3: 检查配置
    config_ok = check_config()

    # 步骤4: 检查账号定位
    strategy_ok = check_strategy()

    # 步骤5: 检查数据库
    check_database()

    # 总结
    print("\n" + "=" * 60)
    print("   安装检查完成")
    print("=" * 60)

    if not config_ok:
        print("\n[下一步] 请编辑 config/setting.txt 填入您的API密钥")
        print("   - WECHAT_APP_ID")
        print("   - WECHAT_APP_SECRET")
        print("   - CHERRY_API_KEY")

    if not strategy_ok:
        print("\n[下一步] 请编辑 prompts/account_strategy.md 自定义账号定位")

    if config_ok and strategy_ok:
        print("\n[完成] 所有配置就绪！")
        print("\n运行以下命令开始写作：")
        print("   python execute_test_run.py")
    else:
        print("\n[提示] 配置完成后，重新运行此脚本进行验证")
        print("   python setup.py")

    print("\n" + "=" * 60)

    # 尝试测试连接
    if config_ok:
        asyncio.run(test_connection())

    input("\n按回车键退出...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n安装已取消")
