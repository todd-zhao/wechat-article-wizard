#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
排版风格配置管理器
管理用户的排版风格偏好设置
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
STYLE_CONFIG_FILE = CONFIG_DIR / "style_config.txt"
STYLE_PRESETS_DIR = BASE_DIR / "prompts" / "style_presets"

# 内置风格定义
BUILTIN_STYLES = {
    "default": {"name": "简洁风格", "file": "pattern_editor.md", "desc": "通用风格"},
    "business": {"name": "商务风格", "file": "pattern_business.md", "desc": "专业、稳重"},
    "minimalist": {"name": "极简风格", "file": "pattern_minimalist.md", "desc": "简约风格"},
    "elegant": {"name": "优雅风格", "file": "pattern_elegant.md", "desc": "精致优雅"},
    "creative": {"name": "创意风格", "file": "pattern_creative.md", "desc": "活泼创意"}
}


class StyleConfig:
    """风格配置管理类"""
    
    def __init__(self):
        self.config = {}
        self._ensure_config_dir()
        self._load_config()
    
    def _ensure_config_dir(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        STYLE_PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self):
        if not STYLE_CONFIG_FILE.exists():
            self._create_default_config()
            return
        
        with open(STYLE_CONFIG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    try:
                        key, value = line.split("=", 1)
                        self.config[key.strip()] = value.strip()
                    except ValueError:
                        continue
    
    def _create_default_config(self):
        default_content = """# 公众号写作助手 - 排版风格配置
default_style = default
total_articles = 0
last_used_style = default
last_used_date = 2026-02-23
style_history = default
"""
        with open(STYLE_CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(default_content)
    
    def _save_config(self):
        with open(STYLE_CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write("# 公众号写作助手 - 排版风格配置\n")
            f.write(f"default_style = {self.config.get('default_style', 'default')}\n")
            f.write(f"total_articles = {self.config.get('total_articles', '0')}\n")
            f.write(f"last_used_style = {self.config.get('last_used_style', 'default')}\n")
            f.write(f"last_used_date = {self.config.get('last_used_date', datetime.now().strftime('%Y-%m-%d'))}\n")
            f.write(f"style_history = {self.config.get('style_history', 'default')}\n")
    
    def get_default_style(self) -> str:
        return self.config.get("default_style", "default")
    
    def set_default_style(self, style: str) -> bool:
        available = [s["id"] for s in self.list_available_styles()]
        if style not in available:
            return False
        
        self.config["default_style"] = style
        history = self.config.get("style_history", "default").split(",")
        if style in history:
            history.remove(style)
        history.append(style)
        self.config["style_history"] = ",".join(history[-10:])
        self._save_config()
        return True
    
    def list_available_styles(self) -> List[Dict]:
        styles = []
        for style_id, info in BUILTIN_STYLES.items():
            styles.append({"id": style_id, "name": info["name"], "desc": info["desc"], "type": "builtin", "file": info["file"]})
        
        if STYLE_PRESETS_DIR.exists():
            for file in STYLE_PRESETS_DIR.glob("*.md"):
                styles.append({"id": file.stem, "name": f"{file.stem} (自定义)", "desc": "自定义风格", "type": "custom", "file": f"style_presets/{file.name}"})
        return styles
    
    def get_style_info(self, style_id: str) -> Optional[Dict]:
        if style_id in BUILTIN_STYLES:
            info = BUILTIN_STYLES[style_id]
            return {"id": style_id, "name": info["name"], "desc": info["desc"], "type": "builtin", "file": info["file"]}
        
        custom_file = STYLE_PRESETS_DIR / f"{style_id}.md"
        if custom_file.exists():
            return {"id": style_id, "name": f"{style_id} (自定义)", "desc": "自定义风格", "type": "custom", "file": f"style_presets/{custom_file.name}"}
        return None
    
    def get_style_file_path(self, style_id: str) -> str:
        if style_id in BUILTIN_STYLES:
            return str(BASE_DIR / "prompts" / BUILTIN_STYLES[style_id]["file"])
        custom_file = STYLE_PRESETS_DIR / f"{style_id}.md"
        if custom_file.exists():
            return str(custom_file)
        return str(BASE_DIR / "prompts" / "pattern_editor.md")
    
    def record_usage(self, style_id: str):
        total = int(self.config.get("total_articles", 0))
        self.config["total_articles"] = str(total + 1)
        self.config["last_used_style"] = style_id
        self.config["last_used_date"] = datetime.now().strftime("%Y-%m-%d")
        history = self.config.get("style_history", "default").split(",")
        if style_id in history:
            history.remove(style_id)
        history.append(style_id)
        self.config["style_history"] = ",".join(history[-10:])
        self._save_config()
    
    def reset_to_default(self):
        self.config["default_style"] = "default"
        self.config["total_articles"] = "0"
        self.config["last_used_style"] = "default"
        self.config["last_used_date"] = datetime.now().strftime("%Y-%m-%d")
        self.config["style_history"] = "default"
        self._save_config()
    
    def get_usage_stats(self) -> Dict:
        return {"total_articles": int(self.config.get("total_articles", 0)), "last_used_style": self.config.get("last_used_style", "default"), "last_used_date": self.config.get("last_used_date", "unknown"), "style_history": self.config.get("style_history", "default").split(",")}


# 全局单例
_style_config_instance = None


def get_style_config() -> StyleConfig:
    global _style_config_instance
    if _style_config_instance is None:
        _style_config_instance = StyleConfig()
    return _style_config_instance


def get_default_style() -> str:
    return get_style_config().get_default_style()


def set_default_style(style: str) -> bool:
    return get_style_config().set_default_style(style)


def list_available_styles() -> List[Dict]:
    return get_style_config().list_available_styles()


def get_style_info(style_id: str) -> Optional[Dict]:
    return get_style_config().get_style_info(style_id)


def get_style_file_path(style_id: str) -> str:
    return get_style_config().get_style_file_path(style_id)


def record_style_usage(style_id: str):
    get_style_config().record_usage(style_id)
