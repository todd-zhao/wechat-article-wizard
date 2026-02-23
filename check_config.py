#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置验证工具 - 检查环境变量配置是否完整
"""

import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "src"))

from config import Config


def print_config_status():
    """打印配置状态"""
    print("=" * 60)
    print("   公众号写作助手 - 配置检查工具")
    print("=" * 60)
    
    print("\n🔑 配置项检查:")
    
    config_items = [
        ("WECHAT_APP_ID", Config.WECHAT_APP_ID, "微信公众号 AppID"),
        ("WECHAT_APP_SECRET", Config.WECHAT_APP_SECRET, "微信公众号 AppSecret"),
        ("CHERRY_API_KEY", Config.CHERRY_API_KEY, "CherryStudio API Key"),
    ]
    
    all_configured = True
    missing_items = []
    
    for key, value, description in config_items:
        if not value or value == "your_app_id_here" or value == "your_app_secret_here" or value == "your_api_key_here":
            print(f"  ✗ {key}: 未配置 ({description})")
            missing_items.append(key)
            all_configured = False
        else:
            masked = "***" + value[-4:] if len(value) > 4 else "***"
            print(f"  ✓ {key}: {masked}")
    
    print("\n⚙️  其他配置:")
    print(f"  • HTTP_TIMEOUT: {Config.HTTP_TIMEOUT}秒")
    print(f"  • API_MAX_TOKENS: {Config.API_MAX_TOKENS}")
    
    print("\n" + "=" * 60)
    if all_configured:
        print("✅ 配置检查通过！")
        print("\n→ 您现在可以运行程序了:")
        print("  python quick_start.py \"文章主题\"")
    else:
        print("❌ 配置不完整！缺少以下配置项:")
        for item in missing_items:
            print(f"   - {item}")
        print("\n💡 还没有 CherryStudio API Key？")
        print("   推荐注册：https://open.cherryin.ai/register?aff=gXKS")
        print("\n→ 快速配置命令:")
        print("  python tools/auto_setup.py --credentials <appid> <secret> --api-key <key>")
    print("=" * 60)
    
    return all_configured


if __name__ == "__main__":
    try:
        success = print_config_status()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 检查过程出错：{e}")
        sys.exit(1)
