import httpx
import asyncio
import sys
import re

# 解决 Windows 命令行中文乱码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def is_ipv4(ip: str) -> bool:
    """检查是否为有效的IPv4地址"""
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    parts = ip.split('.')
    return all(0 <= int(part) <= 255 for part in parts)

async def fetch_ip():
    print("正在查询您的公网 IP 地址，请稍候...")
    # 使用专门的IPv4查询服务
    urls = [
        "https://api.ipify.org?format=text",  # 强制返回IPv4
        "https://ipv4.ipify.org",
        "https://ifconfig.me/ip",
        "https://ident.me",
        "https://icanhazip.com"
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:
        for url in urls:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    ip = response.text.strip()
                    # 检查是否为IPv4地址
                    if is_ipv4(ip):
                        print("\n" + "="*40)
                        print(f"[OK] 您的公网 IPv4 地址是: {ip}")
                        print("="*40)
                        print("\n提示：请复制上面的数字，填入微信公众号后台的「IP白名单」中。")
                        return
                    else:
                        print(f"   [跳过] {url} 返回的是IPv6地址: {ip}")
                        continue
            except Exception as e:
                print(f"   [跳过] {url} 查询失败: {e}")
                continue

    print("\n[ERROR] 无法获取IPv4地址。")
    print("可能原因：您的网络环境只支持IPv6")
    print("\n请尝试以下方案：")
    print("1. 手动访问 https://ipw.cn 或 https://ip138.com 查询IPv4地址")
    print("2. 或联系您的网络管理员获取白名单IP")

if __name__ == "__main__":
    try:
        asyncio.run(fetch_ip())
    except KeyboardInterrupt:
        print("\n查询已取消。")
