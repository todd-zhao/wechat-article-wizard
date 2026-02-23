#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目状态检查器
提供快速、静默的状态检查，返回结构化结果

使用方式：
    from src.status_checker import StatusChecker
    
    checker = StatusChecker(silent=True)
    result = checker.check_all(skip_api=True)
    
    if result.is_ready:
        # 所有检查通过，开始工作
        ...
    else:
        # 输出缺失项
        print(result.missing_items)
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

BASE_DIR = Path(__file__).parent.parent


class CheckStatus(Enum):
    OK = "ok"
    MISSING = "missing"
    ERROR = "error"


@dataclass
class StatusResult:
    is_ready: bool = True
    python_ok: bool = True
    config_ok: bool = True
    strategy_ok: bool = True
    database_ok: bool = True
    has_plans: bool = False
    
    missing_items: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.missing_items is None:
            object.__setattr__(self, 'missing_items', [])
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])
    
    def to_dict(self) -> dict:
        return {
            "is_ready": self.is_ready,
            "python_ok": self.python_ok,
            "config_ok": self.config_ok,
            "strategy_ok": self.strategy_ok,
            "database_ok": self.database_ok,
            "has_plans": self.has_plans,
            "missing_items": self.missing_items,
            "warnings": self.warnings
        }


class StatusChecker:
    """状态检查器 - 供 Agent 快速检查项目状态"""
    
    def __init__(self, silent: bool = True):
        self.silent = silent
        self.result = StatusResult()
    
    def _log(self, message: str):
        if not self.silent:
            print(message)
    
    def check_python(self):
        version = sys.version_info
        if version.major >= 3 and version.minor >= 10:
            self._log(f"  ✓ Python {version.major}.{version.minor}")
            return True
        self.result.is_ready = False
        self.result.python_ok = False
        self.result.missing_items.append(f"Python 版本过低 (需要 3.10+)")
        return False
    
    def check_config(self):
        config_file = BASE_DIR / "config" / "setting.txt"
        
        if not config_file.exists():
            self.result.is_ready = False
            self.result.config_ok = False
            self.result.missing_items.append("配置文件不存在：config/setting.txt")
            self._log("  ✗ 配置文件不存在")
            return False
        
        with open(config_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        required_keys = ["WECHAT_APP_ID", "WECHAT_APP_SECRET", "CHERRY_API_KEY"]
        missing_keys = [k for k in required_keys if k not in content or "your_" in content.lower()]
        
        if missing_keys:
            self.result.is_ready = False
            self.result.config_ok = False
            self.result.missing_items.append(f"配置不完整：{', '.join(missing_keys)}")
            self._log(f"  ✗ 缺少配置：{', '.join(missing_keys)}")
            return False
        
        self._log("  ✓ 配置文件完整")
        return True
    
    def check_strategy(self):
        strategy_file = BASE_DIR / "prompts" / "account_strategy.md"
        
        if not strategy_file.exists():
            self.result.strategy_ok = False
            self.result.missing_items.append("账号定位文件不存在")
            self._log("  ✗ 账号定位不存在")
            return False
        
        if strategy_file.stat().st_size < 50:
            self.result.strategy_ok = False
            self.result.missing_items.append("账号定位内容为空")
            self._log("  ✗ 账号定位内容为空")
            return False
        
        self._log("  ✓ 账号定位已设置")
        return True
    
    def check_database(self):
        db_file = BASE_DIR / "content_wizard.db"
        
        if not db_file.exists():
            self._log("  ℹ 数据库不存在（首次运行时自动创建）")
            return True
        
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM article_plans WHERE status = 'planned'")
            count = cursor.fetchone()[0]
            conn.close()
            
            self.result.database_ok = True
            self.result.has_plans = (count > 0)
            self._log(f"  ✓ 数据库正常 ({count} 个待写选题)")
            return True
        except Exception as e:
            self.result.database_ok = False
            self.result.missing_items.append(f"数据库错误：{str(e)}")
            self._log(f"  ✗ 数据库错误")
            return False
    
    def check_all(self, skip_api: bool = True) -> StatusResult:
        """执行所有检查"""
        self._log("=" * 50)
        self._log("  项目状态检查")
        self._log("=" * 50)
        
        self._log("\n[1/4] Python 环境...")
        self.check_python()
        
        self._log("\n[2/4] 配置文件...")
        self.check_config()
        
        self._log("\n[3/4] 账号定位...")
        self.check_strategy()
        
        self._log("\n[4/4] 数据库...")
        self.check_database()
        
        self._log("\n" + "=" * 50)
        if self.result.is_ready:
            self._log("  ✓ 所有检查通过，可以开始工作")
        else:
            self._log(f"  ✗ 部分检查未通过，缺失{len(self.result.missing_items)}项")
        self._log("=" * 50)
        
        return self.result
    
    def quick_check(self) -> bool:
        """快速检查（静默模式，仅检查关键项）"""
        old_silent = self.silent
        self.silent = True
        self.check_all(skip_api=True)
        self.silent = old_silent
        return self.result.is_ready
    
    def get_status_json(self) -> str:
        """获取 JSON 格式的状态报告"""
        return json.dumps(self.result.to_dict(), ensure_ascii=False, indent=2)


def check_status(silent: bool = True, skip_api: bool = True) -> StatusResult:
    """便捷函数：执行状态检查"""
    checker = StatusChecker(silent=silent)
    return checker.check_all(skip_api=skip_api)


if __name__ == "__main__":
    checker = StatusChecker(silent=False)
    result = checker.check_all(skip_api=False)
    print("\n[JSON_OUTPUT]")
    print(checker.get_status_json())
    sys.exit(0 if result.is_ready else 1)
