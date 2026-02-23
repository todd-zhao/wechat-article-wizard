# ================================================
# 公众号写作助手 统一配置管理模块
# ================================================
"""
统一配置管理 - 支持多种配置来源

配置优先级（从高到低）：
1. config/setting.txt（推荐）
2. .env 文件
3. 系统环境变量

使用方法:
1. 首次使用请运行: python tools/auto_setup.py
2. 或手动创建 config/setting.txt 填入配置

安全提示:
- .env 文件已添加到 .gitignore，不会被提交到 Git
- 建议使用 config/setting.txt 管理配置
"""

import os
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv

# 项目根目录
BASE_DIR = Path(__file__).parent.parent


def load_config_file() -> Dict[str, str]:
    """
    从配置文件加载配置

    优先级：
    1. config/setting.txt
    2. .env 文件

    Returns:
        Dict[str, str]: 配置字典
    """
    config = {}

    # 1. 优先从 setting.txt 读取
    setting_path = BASE_DIR / "config" / "setting.txt"
    if setting_path.exists():
        with open(setting_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    try:
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip()
                    except ValueError:
                        continue
        if config:
            print(f"   [配置] 从 config/setting.txt 加载了 {len(config)} 项配置")
            return config

    # 2. 回退到 .env 文件
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print("   [配置] 从 .env 加载配置")

    return config


# 加载配置
_config_cache = None


def get_config_value(key: str, default: str = "") -> str:
    """
    获取配置值

    优先级：
    1. config/setting.txt
    2. .env / 环境变量
    3. 默认值

    Args:
        key: 配置键
        default: 默认值

    Returns:
        str: 配置值
    """
    global _config_cache

    # 首次调用时加载配置
    if _config_cache is None:
        _config_cache = load_config_file()

    # 1. 从配置字典获取
    if key in _config_cache and _config_cache[key]:
        return _config_cache[key]

    # 2. 从环境变量获取（.env 或系统环境变量）
    env_value = os.getenv(key)
    if env_value:
        return env_value

    # 3. 返回默认值
    return default


class Config:
    """统一配置管理类"""

    # ======== 微信公众平台配置 ========
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""

    # ======== CherryStudio API 配置 ========
    CHERRY_API_BASE_URL: str = "https://open.cherryin.ai/v1"
    CHERRY_API_KEY: str = ""

    # ======== 模型配置 ========
    WRITER_MODEL: str = "anthropic/claude-opus-4.5"
    LAYOUT_MODEL: str = "google/gemini-3-flash-preview"
    IMAGE_GEN_MODEL: str = "qwen/qwen-image(free)"

    # ======== 图片生成单独配置 ========
    # 图片生成可能使用不同的 API 地址
    IMAGE_GEN_BASE_URL: str = "https://open.cherryin.ai/v1/images/generations"

    # ======== 超时和限制配置 ========
    HTTP_TIMEOUT: int = 60
    API_MAX_TOKENS: int = 8000

    # ======== 日志配置 ========
    LOG_LEVEL: str = "INFO"

    # ======== 路径配置 ========
    BASE_DIR: Path = BASE_DIR
    DB_PATH: Path = BASE_DIR / "content_wizard.db"
    UPLOAD_DIR: Path = BASE_DIR / "images"
    CONFIG_DIR: Path = BASE_DIR / "config"

    @classmethod
    def reload(cls):
        """重新加载配置"""
        global _config_cache
        _config_cache = None
        # 重新设置类属性
        cls.WECHAT_APP_ID = get_config_value("WECHAT_APP_ID", "")
        cls.WECHAT_APP_SECRET = get_config_value("WECHAT_APP_SECRET", "")
        cls.CHERRY_API_BASE_URL = get_config_value("CHERRY_API_BASE_URL", "https://open.cherryin.ai/v1")
        cls.CHERRY_API_KEY = get_config_value("CHERRY_API_KEY", "")
        cls.WRITER_MODEL = get_config_value("WRITER_MODEL", "anthropic/claude-opus-4.5")
        cls.LAYOUT_MODEL = get_config_value("LAYOUT_MODEL", "google/gemini-3-flash-preview")
        cls.IMAGE_GEN_MODEL = get_config_value("IMAGE_GEN_MODEL", "qwen/qwen-image(free)")
        # 图片生成使用独立的 API 地址
        cls.IMAGE_GEN_BASE_URL = get_config_value("IMAGE_GEN_BASE_URL", "https://open.cherryin.ai/v1/images/generations")
        cls.HTTP_TIMEOUT = int(get_config_value("HTTP_TIMEOUT", "60"))
        cls.API_MAX_TOKENS = int(get_config_value("API_MAX_TOKENS", "8000"))
        cls.LOG_LEVEL = get_config_value("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> bool:
        """
        验证必要配置是否存在

        Returns:
            bool: 验证是否通过
        """
        # 先确保加载最新配置
        cls.reload()

        required_keys = {
            "WECHAT_APP_ID": cls.WECHAT_APP_ID,
            "WECHAT_APP_SECRET": cls.WECHAT_APP_SECRET,
            "CHERRY_API_KEY": cls.CHERRY_API_KEY,
        }

        missing = [key for key, value in required_keys.items()
                   if not value or "your_" in value.lower()]

        if missing:
            error_msg = f"缺少必要的配置项：{missing}\n"
            error_msg += f"请运行: python tools/auto_setup.py --credentials <appid> <secret> --api-key <key>"
            raise ValueError(error_msg)

        return True

    @classmethod
    def is_configured(cls) -> bool:
        """检查配置是否完成"""
        try:
            cls.reload()
            return cls.validate()
        except ValueError:
            return False

    @classmethod
    def get_masked_api_key(cls) -> str:
        """获取脱敏后的 API Key"""
        cls.reload()
        if not cls.CHERRY_API_KEY:
            return "***"
        if len(cls.CHERRY_API_KEY) <= 8:
            return "***" + cls.CHERRY_API_KEY[-2:]
        return cls.CHERRY_API_KEY[:4] + "***" + cls.CHERRY_API_KEY[-4:]


# 初始化配置
Config.reload()


# 便捷函数
def get_config() -> Config:
    """获取配置对象"""
    Config.reload()
    return Config


def validate_config() -> bool:
    """验证配置并返回结果"""
    return Config.validate()


def is_configured() -> bool:
    """检查配置是否完成"""
    return Config.is_configured()
