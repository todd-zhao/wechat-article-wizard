import os
import time
import httpx
import asyncio
import sys
from pathlib import Path
from dotenv import set_key

# 解决 Windows 命令行中文乱码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def save_to_env(config: dict):
    """安全保存配置到 .env 文件"""
    env_path = Path(__file__).parent.parent / ".env"
    
    # 如果 .env 不存在，先复制模板
    env_example_path = Path(__file__).parent.parent / ".env.example"
    if not env_path.exists() and env_example_path.exists():
        import shutil
        shutil.copy(env_example_path, env_path)
    
    # 逐项写入配置
    for key, value in config.items():
        set_key(str(env_path), key, value)
    
    print(f"✓ 配置已保存到：{env_path}")
    print("⚠ 安全提示：.env 文件包含敏感信息，请勿分享给他人或提交到 Git")

async def get_public_ip():
    urls = ["https://api.ipify.org", "https://ifconfig.me/ip"]
    async with httpx.AsyncClient(timeout=5.0) as client:
        for url in urls:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.text.strip()
            except: continue
    return "未知"

async def test_wechat_connection(appid, secret):
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {"grant_type": "client_credential", "appid": appid, "secret": secret}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, params=params)
            data = resp.json()
            if "access_token" in data:
                return True, "[OK] 握手成功！您的 AppID 和 Secret 配置正确。"
            errcode = data.get("errcode")
            if errcode == 40164:
                my_ip = await get_public_ip()
                return False, f"[ERROR] IP不在白名单内！\n   原因：微信拒绝了当前电脑的访问。\n   解决：请将您的IP [{my_ip}] 复制到公众号后台的「IP白名单」中。"
            elif errcode == 40013:
                return False, "[ERROR] AppID 无效！请检查是否输入多余空格或填错。"
            elif errcode == 40001:
                return False, "[ERROR] AppSecret 错误！请确保这是最新的密钥。"
            else:
                return False, f"[ERROR] 微信返回错误: {data.get('errmsg')} (代码: {errcode})"
        except Exception as e:
            return False, f"[ERROR] 网络连接失败: {str(e)}"

async def run_wizard():
    clear_screen()
    print("============================================================")
    print("   公众号写作助手 - 智能配置向导")
    print("============================================================")
    print("\n我们将帮您完成设置。如果不清楚如何获取，请看: WECHAT_SETUP_GUIDE.md")
    print("-" * 60)

    config = {}
    while True:
        print("\n[第一部分：微信公众号]")
        appid = input("请输入 AppID: ").strip()
        secret = input("请输入 AppSecret: ").strip()
        print("正在验证连接，请稍候...")
        success, message = await test_wechat_connection(appid, secret)
        print("\n" + "-"*40)
        print(message)
        print("-"*40)
        if success:
            config['WECHAT_APP_ID'] = appid
            config['WECHAT_APP_SECRET'] = secret
            break
        else:
            choice = input("\n验证失败，是否重新输入？(y/n, 输入 n 跳过并保存): ").lower()
            if choice != 'y':
                config['WECHAT_APP_ID'] = appid
                config['WECHAT_APP_SECRET'] = secret
                break

    print("\n[第二部分：AI 创作大脑]")
    config['CHERRY_API_KEY'] = input("请输入 Cherry Studio 的 API Key: ").strip()
    config['CHERRY_API_BASE_URL'] = "https://open.cherryin.ai/v1"
    config['WRITER_MODEL'] = "anthropic/claude-haiku-4.5"
    config['IMAGE_GEN_MODEL'] = "qwen/qwen-image(free)"
    config['MINIMAX_API_URL'] = "https://api.minimax.io/v1/image_generation"
    config['MINIMAX_API_KEY'] = ""

    print("\n正在保存设置...")
    save_to_env(config)
    
    print("\n[DONE] 配置已保存！您可以开始创作了。")
    print("============================================================")

if __name__ == "__main__":
    try:
        asyncio.run(run_wizard())
    except KeyboardInterrupt:
        print("\n\n配置已取消。")
