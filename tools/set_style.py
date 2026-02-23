#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
排版风格设置工具

使用方式：
    python tools/set_style.py business    # 设置默认风格
    python tools/set_style.py --current   # 查看当前风格
    python tools/set_style.py --list      # 列出所有风格
    python tools/set_style.py --reset     # 重置为默认
    python tools/set_style.py             # 交互式设置
"""

import os
import sys
import argparse

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description="排版风格设置工具")
    parser.add_argument("style", nargs="?", help="要设置的风格名称")
    parser.add_argument("--current", "-c", action="store_true", help="查看当前默认风格")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有可用风格")
    parser.add_argument("--reset", action="store_true", help="重置为系统默认")
    
    args = parser.parse_args()
    
    from src.style_config import StyleConfig
    config = StyleConfig()
    
    if args.list:
        print("可用风格:")
        for style in config.list_available_styles():
            mark = " ⭐默认" if style["id"] == config.get_default_style() else ""
            print(f"  [{style['id']:12}] {style['name']}{mark} - {style['desc']}")
        return
    
    if args.current:
        default_style = config.get_default_style()
        style_info = config.get_style_info(default_style)
        stats = config.get_usage_stats()
        print(f"当前默认风格：{default_style} ({style_info['name'] if style_info else '未知'})")
        print(f"总文章数：{stats['total_articles']}")
        print(f"上次使用：{stats['last_used_date']}")
        return
    
    if args.reset:
        config.reset_to_default()
        print("已重置为系统默认风格")
        return
    
    if args.style:
        style_info = config.get_style_info(args.style)
        if style_info:
            config.set_default_style(args.style)
            print(f"已设置默认风格为：{style_info['name']} ({args.style})")
        else:
            print(f"无效的风格 ID: {args.style}")
            sys.exit(1)
        return
    
    # 交互式设置
    print("请选择排版风格:")
    for i, style in enumerate(config.list_available_styles(), 1):
        mark = " ⭐默认" if style["id"] == config.get_default_style() else ""
        print(f"  [{i}] {style['name']}{mark} - {style['desc']}")
    
    choice = input("\n请输入选项 (q 退出): ").strip()
    styles = config.list_available_styles()
    if choice.isdigit() and 1 <= int(choice) <= len(styles):
        style = styles[int(choice) - 1]
        config.set_default_style(style["id"])
        print(f"已设置默认风格为：{style['name']}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已取消")
