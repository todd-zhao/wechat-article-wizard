#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速状态检查工具
让 Agent 快速静默检查项目状态

使用方式：
    # 快速检查（静默模式）
    python tools/quick_check.py --silent
    
    # 详细检查
    python tools/quick_check.py --verbose
    
    # JSON 输出（供程序解析）
    python tools/quick_check.py --json
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def main():
    import argparse
    parser = argparse.ArgumentParser(description="快速状态检查工具")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出模式")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--silent", "-s", action="store_true", help="完全静默（仅返回退出码）")
    
    args = parser.parse_args()
    
    from src.status_checker import StatusChecker
    
    silent = args.silent or (args.json and not args.verbose)
    checker = StatusChecker(silent=silent)
    result = checker.check_all(skip_api=True)
    
    if args.json:
        print(checker.get_status_json())
    elif not args.silent:
        print("\n" + "=" * 50)
        print("  状态摘要")
        print("=" * 50)
        print(f"  Python 环境：{'✓' if result.python_ok else '✗'}")
        print(f"  配置文件：{'✓' if result.config_ok else '✗'}")
        print(f"  账号定位：{'✓' if result.strategy_ok else '✗'}")
        print(f"  数据库：{'✓' if result.database_ok else '✗'}")
        print(f"  选题计划：{'✓' if result.has_plans else '✗'}")
        print("=" * 50)
        
        if result.is_ready:
            print("  ✓ 所有检查通过，可以开始工作")
        else:
            print(f"  ✗ 部分检查未通过，缺失{len(result.missing_items)}项:")
            for item in result.missing_items:
                print(f"    - {item}")
            print("\n💡 修复提示:")
            if not result.config_ok:
                print("   运行：python tools/auto_setup.py --credentials <appid> <secret> --api-key <key>")
            if not result.strategy_ok:
                print("   编辑：prompts/account_strategy.md")
        print("=" * 50)
    
    sys.exit(0 if result.is_ready else 1)


if __name__ == "__main__":
    main()
