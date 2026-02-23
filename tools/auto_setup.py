#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动化安装和配置脚本
首次使用自动检测环境并配置
"""

import os
import sys
import subprocess
import shutil
import asyncio
import httpx

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def get_python_executable():
    """获取 Python 可执行文件路径"""
    if os.path.isdir(PROJECT_ROOT):
        for item in os.listdir(PROJECT_ROOT):
            if item.startswith("python-") and item.endswith("-embed-amd64"):
                embed_path = os.path.join(PROJECT_ROOT, item, "python.exe")
                if os.path.exists(embed_path):
                    return embed_path
    return sys.executable


def check_python():
    """检查 Python 版本"""
    print("\n[1/5] 检查 Python 环境...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"  ✗ 需要 Python 3.10+, 当前：{version.major}.{version.minor}")
        return False
    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def install_dependencies():
    """安装依赖"""
    print("\n[2/5] 安装 Python 依赖...")
    req_file = os.path.join(PROJECT_ROOT, "requirements.txt")
    if not os.path.exists(req_file):
        print(f"  ✗ 找不到 requirements.txt")
        return False
    
    try:
        python_exe = get_python_executable()
        subprocess.run([python_exe, "-m", "pip", "install", "-r", req_file], capture_output=True, timeout=300)
        print("  ✓ 依赖安装成功")
        return True
    except Exception as e:
        print(f"  ✗ 安装失败：{e}")
        return False


def ensure_directories():
    """确保目录存在"""
    print("\n[3/5] 初始化目录结构...")
    dirs = ["config", "prompts", "src", "tools", "images", "resources"]
    for d in dirs:
        path = os.path.join(PROJECT_ROOT, d)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"  ✓ 创建目录：{d}")
        else:
            print(f"  ✓ 目录已存在：{d}")
    return True


def setup_config():
    """配置初始化"""
    print("\n[4/5] 配置文件检查...")
    config_file = os.path.join(PROJECT_ROOT, "config", "setting.txt")
    
    if not os.path.exists(config_file):
        default_config = """# 公众号写作助手配置文件
# 请编辑以下内容，填入您的 API 密钥

# 微信公众平台
WECHAT_APP_ID=your_app_id_here
WECHAT_APP_SECRET=your_app_secret_here

# CherryStudio API
CHERRY_API_BASE_URL=https://open.cherryin.ai/v1
CHERRY_API_KEY=your_api_key_here

# 模型配置
WRITER_MODEL=anthropic/claude-haiku-4.5
LAYOUT_MODEL=google/gemini-3-flash-preview
IMAGE_GEN_MODEL=qwen/qwen-image(free)
"""
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(default_config)
        print(f"  ✓ 已创建配置文件")
        print(f"  ⚠ 请编辑 config/setting.txt 填入 API 密钥")
        return False
    else:
        with open(config_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        required_keys = ["WECHAT_APP_ID", "WECHAT_APP_SECRET", "CHERRY_API_KEY"]
        missing = [k for k in required_keys if k not in content or "your_" in content.lower()]
        
        if missing:
            print(f"  ⚠ 缺少配置项：{', '.join(missing)}")
            return False
        
        print(f"  ✓ 配置文件已就绪")
        return True


def setup_strategy():
    """账号定位初始化"""
    print("\n[5/5] 账号定位检查...")
    strategy_file = os.path.join(PROJECT_ROOT, "prompts", "account_strategy.md")
    
    if not os.path.exists(strategy_file) or os.path.getsize(strategy_file) < 50:
        default_strategy = """# 账号定位策略

## 目标读者
- 读者画像：企业主、创业者、职场人士
- 年龄：25-45 岁

## 核心价值
- 专业实用
- 有深度有见解
- 可操作性强

## 写作风格
- 干货型
- 犀利直接
- 案例驱动
"""
        with open(strategy_file, "w", encoding="utf-8") as f:
            f.write(default_strategy)
        print(f"  ✓ 已创建账号定位文件")
        return False
    
    print(f"  ✓ 账号定位已就绪")
    return True


async def get_public_ip():
    """获取本机公网 IPv4 地址"""
    urls = ["https://api.ipify.org?format=text", "https://ipv4.ipify.org"]
    async with httpx.AsyncClient(timeout=10.0) as client:
        for url in urls:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    ip = resp.text.strip()
                    print(f"\n  您的公网 IPv4: {ip}")
                    print(f"  ℹ 请将此 IP 添加到微信开发者平台的 IP 白名单")
                    return ip
            except:
                continue
    return None


async def test_wechat_connection(appid, secret):
    """验证微信配置"""
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {"grant_type": "client_credential", "appid": appid, "secret": secret}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, params=params)
            data = resp.json()
            if "access_token" in data:
                return True, "OK"
            return False, data.get("errmsg", "未知错误")
        except Exception as e:
            return False, str(e)


async def test_api():
    """测试 API 连接"""
    print("\n[测试] 验证 API 连接...")
    config_file = os.path.join(PROJECT_ROOT, "config", "setting.txt")
    config = {}
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    config[k] = v
    except:
        return False
    
    if "WECHAT_APP_ID" in config and "WECHAT_APP_SECRET" in config:
        if "your_" not in config.get("WECHAT_APP_ID", "").lower():
            success, msg = await test_wechat_connection(config["WECHAT_APP_ID"], config["WECHAT_APP_SECRET"])
            if success:
                print("  ✓ 微信 API 连接成功")
            else:
                print(f"  ⚠ 微信 API: {msg}")
    
    return False


def guide_style_selection():
    """引导选择排版风格"""
    print("\n" + "-" * 50)
    print("【排版风格选择】")
    print("\n请选择您喜欢的排版风格：")
    print("  [1] 简洁风格 - 通用风格")
    print("  [2] 商务风格 - 专业、稳重")
    print("  [3] 极简风格 - 简约风格")
    print("  [4] 优雅风格 - 精致优雅")
    print("  [5] 创意风格 - 活泼创意")
    print("  [s] 跳过，稍后选择")
    
    choice = input("\n请输入选项 (1-5, s): ").strip()
    
    style_map = {"1": "default", "2": "business", "3": "minimalist", "4": "elegant", "5": "creative"}
    
    if choice in style_map:
        try:
            from src.style_config import set_default_style
            set_default_style(style_map[choice])
            print(f"\n✓ 已设置默认风格")
        except:
            pass
    else:
        print("\n已跳过风格选择")
    
    print("-" * 50)


def main():
    print("=" * 60)
    print("   公众号写作助手 - 自动化配置")
    print("=" * 60)
    
    if not check_python():
        print("\n✗ Python 环境检查未通过")
        input("\n按回车键退出...")
        sys.exit(1)
    
    install_dependencies()
    ensure_directories()
    config_ok = setup_config()
    strategy_ok = setup_strategy()
    
    asyncio.run(get_public_ip())
    
    if config_ok:
        asyncio.run(test_api())
    
    # 总结
    print("\n" + "=" * 60)
    print("   配置检查完成")
    print("=" * 60)
    
    if not config_ok:
        print("\n→ 下一步：请编辑 config/setting.txt")
        print("   填入您的微信 AppID、AppSecret 和 CherryStudio API Key")
        print("\n💡 还没有 CherryStudio API Key？")
        print("   推荐注册：https://open.cherryin.ai/register?aff=gXKS")
    
    if not strategy_ok:
        print("\n→ 下一步：可以编辑 prompts/account_strategy.md")
    
    if config_ok and strategy_ok:
        print("\n✓ 所有配置就绪！")
        guide_style_selection()
        print("\n运行以下命令开始写作：")
        print("   python quick_start.py \"文章主题\"")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
