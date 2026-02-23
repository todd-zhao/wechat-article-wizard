import subprocess
import sys
from pathlib import Path

# 使用 importlib.metadata 替代 pkg_resources (Python 3.8+)
try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    # Python < 3.8 回退方案
    from importlib_metadata import version, PackageNotFoundError


def check_and_install_dependencies():
    """
    检查并安装项目依赖
    兼容 Python 3.8+ (包括 3.12, 3.13, 3.14)
    """
    requirements_file = Path(__file__).parent.parent / "requirements.txt"
    if not requirements_file.exists():
        print("   [SELF-CHECK] Warning: requirements.txt not found. Skipping dependency check.")
        return

    print("   [SELF-CHECK] 正在检查环境依赖...")

    with open(requirements_file, "r", encoding="utf-8") as f:
        requirements = [
            line.strip().split(">=")[0].split("==")[0].split("<=")[0]
            for line in f
            if line.strip() and not line.startswith("#")
        ]

    missing = []
    for package in requirements:
        try:
            # 尝试获取版本，如果不存在则抛出异常
            version(package)
        except PackageNotFoundError:
            missing.append(package)

    if missing:
        print(f"   [SELF-CHECK] 发现缺少依赖项: {', '.join(missing)}")
        print("   [SELF-CHECK] 正在尝试自动安装...")

        try:
            # 直接传递缺少的包给 pip install
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            print("   [SELF-CHECK] 依赖项安装成功！")
        except subprocess.CalledProcessError:
            print(f"   [SELF-CHECK] 错误: 自动安装失败。请手动运行 'pip install -r requirements.txt'")
    else:
        print("   [SELF-CHECK] 所有依赖项已就绪。")


if __name__ == "__main__":
    check_and_install_dependencies()
