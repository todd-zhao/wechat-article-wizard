#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动化配置测试脚本
无需交互，用于AI验证配置是否成功
"""

import os
import sys
import json
import asyncio

# Windows 控制台编码修复
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))


class ConfigTester:
    """配置测试器"""

    def __init__(self):
        self.results = {
            "success": True,
            "checks": [],
            "errors": []
        }
        self.config = {}

    def load_config(self):
        """加载配置文件"""
        config_file = os.path.join(PROJECT_ROOT, "config", "setting.txt")

        if not os.path.exists(config_file):
            self.results["success"] = False
            self.results["errors"].append("配置文件不存在: config/setting.txt")
            return False

        with open(config_file, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    try:
                        k, v = line.strip().split("=", 1)
                        self.config[k] = v
                    except:
                        pass

        # 检查必填项
        required = ["WECHAT_APP_ID", "WECHAT_APP_SECRET", "CHERRY_API_KEY"]
        missing = [k for k in required if k not in self.config or "your_" in self.config.get(k, "").lower()]

        if missing:
            self.results["success"] = False
            self.results["errors"].append(f"缺少配置项: {', '.join(missing)}")
            return False

        return True

    def check_python(self):
        """检查Python版本"""
        version = sys.version_info
        check = {
            "name": "Python环境",
            "passed": version.major >= 3 and version.minor >= 10,
            "message": f"Python {version.major}.{version.minor}.{version.micro}"
        }
        self.results["checks"].append(check)
        if not check["passed"]:
            self.results["success"] = False
        return check["passed"]

    def check_dependencies(self):
        """检查依赖包"""
        try:
            import httpx
            import aiohttp
            check = {
                "name": "Python依赖",
                "passed": True,
                "message": "核心依赖已安装"
            }
            self.results["checks"].append(check)
            return True
        except ImportError as e:
            # 尝试自动安装
            print("  尝试自动安装缺失的依赖...")
            try:
                import subprocess
                required = ["httpx", "aiohttp", "python-dotenv"]
                for pkg in required:
                    try:
                        __import__(pkg.replace("-", "_"))
                    except ImportError:
                        subprocess.run([sys.executable, "-m", "pip", "install", pkg], capture_output=True)

                # 再次检查
                import httpx
                import aiohttp
                check = {
                    "name": "Python依赖",
                    "passed": True,
                    "message": "依赖已自动安装"
                }
            except Exception as install_error:
                check = {
                    "name": "Python依赖",
                    "passed": False,
                    "message": f"缺少依赖: {str(e)}, 自动安装失败"
                }
                self.results["success"] = False

        self.results["checks"].append(check)
        return check["passed"]

    def check_database(self):
        """检查数据库"""
        try:
            from src.db_manager import DBManager
            db = DBManager()
            count = db.get_pending_count()
            db.close()

            check = {
                "name": "数据库",
                "passed": True,
                "message": f"数据库正常，待写选题: {count}"
            }
        except Exception as e:
            check = {
                "name": "Database",
                "passed": False,
                "message": f"数据库错误: {str(e)[:50]}"
            }
            self.results["success"] = False

        self.results["checks"].append(check)
        return check["passed"]

    async def check_wechat_api(self):
        """检查微信API"""
        if "WECHAT_APP_ID" not in self.config:
            check = {
                "name": "微信API",
                "passed": False,
                "message": "缺少WECHAT_APP_ID配置"
            }
            self.results["checks"].append(check)
            return False

        try:
            import httpx
            url = "https://api.weixin.qq.com/cgi-bin/token"
            params = {
                "grant_type": "client_credential",
                "appid": self.config["WECHAT_APP_ID"],
                "secret": self.config["WECHAT_APP_SECRET"]
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params)
                data = resp.json()

                if "access_token" in data:
                    check = {
                        "name": "微信API",
                        "passed": True,
                        "message": "微信API连接成功"
                    }
                else:
                    errcode = data.get("errcode", 0)
                    errmsg = data.get("errmsg", "未知错误")

                    # 常见错误码说明
                    error_msgs = {
                        40013: "AppID无效",
                        40001: "AppSecret错误",
                        40164: "IP不在白名单"
                    }

                    check = {
                        "name": "微信API",
                        "passed": False,
                        "message": f"微信API错误 [{errcode}]: {error_msgs.get(errcode, errmsg)}"
                    }
                    self.results["success"] = False

        except Exception as e:
            check = {
                "name": "微信API",
                "passed": False,
                "message": f"连接失败: {str(e)[:50]}"
            }
            self.results["success"] = False

        self.results["checks"].append(check)
        return check["passed"]

    async def check_llm_api(self):
        """检查LLM API"""
        if "CHERRY_API_KEY" not in self.config:
            check = {
                "name": "LLM API",
                "passed": False,
                "message": "缺少CHERRY_API_KEY配置"
            }
            self.results["checks"].append(check)
            return False

        try:
            import httpx

            base_url = self.config.get("CHERRY_API_BASE_URL", "https://open.cherryin.ai/v1")
            model = self.config.get("WRITER_MODEL", "anthropic/claude-haiku-4.5")

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.config['CHERRY_API_KEY']}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Hi"}],
                        "max_tokens": 10
                    }
                )

                if resp.status_code == 200:
                    check = {
                        "name": "LLM API",
                        "passed": True,
                        "message": f"LLM API连接成功 (模型: {model})"
                    }
                else:
                    data = resp.json()
                    check = {
                        "name": "LLM API",
                        "passed": False,
                        "message": f"LLM API错误: {data.get('error', {}).get('message', resp.text[:50])}"
                    }
                    self.results["success"] = False

        except Exception as e:
            check = {
                "name": "LLM API",
                "passed": False,
                "message": f"连接失败: {str(e)[:50]}"
            }
            self.results["success"] = False

        self.results["checks"].append(check)
        return check["passed"]

    async def run_all_checks(self):
        """运行所有检查"""
        print("=" * 50)
        print("  公众号写作助手 - 配置测试")
        print("=" * 50)

        # 加载配置
        print("\n[1/6] 加载配置文件...")
        if not self.load_config():
            return self.output_results()

        print("  ✓ 配置文件加载成功")

        # Python环境
        print("\n[2/6] 检查Python环境...")
        self.check_python()

        # 依赖
        print("\n[3/6] 检查Python依赖...")
        self.check_dependencies()

        # 数据库
        print("\n[4/6] 检查数据库...")
        self.check_database()

        # 微信API
        print("\n[5/6] 检查微信API...")
        await self.check_wechat_api()

        # LLM API
        print("\n[6/6] 检查LLM API...")
        await self.check_llm_api()

        return self.output_results()

    def output_results(self):
        """输出结果"""
        config_file = os.path.join(PROJECT_ROOT, "config", "setting.txt")
        
        print("\n" + "=" * 50)
        print("  测试结果")
        print("=" * 50)

        for check in self.results["checks"]:
            status = "✓" if check["passed"] else "✗"
            print(f"  {status} {check['name']}: {check['message']}")

        if self.results["errors"]:
            print("\n错误:")
            for error in self.results["errors"]:
                print(f"  - {error}")

        print("\n" + "=" * 50)

        if self.results["success"]:
            print("  ✓ 所有检查通过！")
        else:
            print("  ✗ 部分检查失败，请检查配置")
            
            # 检查是否缺少 API Key
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    content = f.read()
                if "CHERRY_API_KEY" not in content or "your_" in content.lower():
                    print("\n💡 还没有 CherryStudio API Key？")
                    print("   推荐注册：https://open.cherryin.ai/register?aff=gXKS")
                    print("   注册后在 CherryStudio 设置中生成 API Key")

        print("=" * 50)

        # 输出JSON格式结果（供AI解析）
        print("\n[JSON_OUTPUT]")
        print(json.dumps(self.results, ensure_ascii=False, indent=2))

        return 0 if self.results["success"] else 1


async def main():
    tester = ConfigTester()
    exit_code = await tester.run_all_checks()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
