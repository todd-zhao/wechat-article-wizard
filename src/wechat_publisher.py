import asyncio
import sys
import os
import httpx
from pathlib import Path
from .config import Config


class WeChatPublisher:
    """微信发布器 - 创建草稿"""

    def __init__(self):
        # 确保加载最新配置
        Config.reload()

        self.config = Config
        self.settings = {
            "WECHAT_APP_ID": Config.WECHAT_APP_ID,
            "WECHAT_APP_SECRET": Config.WECHAT_APP_SECRET,
            "CHERRY_API_KEY": Config.CHERRY_API_KEY,
            "CHERRY_API_BASE_URL": Config.CHERRY_API_BASE_URL,
            "WRITER_MODEL": Config.WRITER_MODEL,
            "LAYOUT_MODEL": Config.LAYOUT_MODEL,
            "IMAGE_GEN_MODEL": Config.IMAGE_GEN_MODEL,
        }
        self._token = None
        self._token_expires = 0

    async def _get_access_token(self) -> str:
        """获取微信access_token

        优先使用 httpx，失败则使用 aiohttp 作为备用
        """
        import time
        if self._token and time.time() < self._token_expires:
            return self._token

        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.settings.get("WECHAT_APP_ID"),
            "secret": self.settings.get("WECHAT_APP_SECRET")
        }

        # 方法1: 尝试使用 httpx
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, params=params)
                data = resp.json()
                if "access_token" in data:
                    self._token = data["access_token"]
                    self._token_expires = time.time() + data["expires_in"] - 300
                    return self._token
        except Exception as e:
            print(f"  [INFO] httpx 获取token失败，尝试 aiohttp: {e}")

        # 方法2: 使用 aiohttp 作为备用
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    data = await resp.json()
                    if "access_token" in data:
                        self._token = data["access_token"]
                        self._token_expires = time.time() + data["expires_in"] - 300
                        return self._token
        except Exception as e:
            raise Exception(f"获取token失败 (httpx和aiohttp都失败): {e}")

        raise Exception(f"获取token失败: {data}")

    async def create_draft(self, title: str, content: str, digest: str, thumb_media_id: str = None) -> str:
        """
        创建微信草稿

        Args:
            title: 文章标题
            content: HTML内容
            digest: 摘要
            thumb_media_id: 封面图media_id

        Returns:
            草稿ID
        """
        token = await self._get_access_token()

        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"

        # 构造文章内容
        # 注意：如果没有封面图，不要包含 thumb_media_id 字段
        article = {
            "title": title,
            "author": "AI Writer",
            "content": content,
            "digest": digest[:120] if digest else "",
            "content_source_url": "",
        }
        # 只有在有有效 media_id 时才添加
        if thumb_media_id and len(thumb_media_id) > 0:
            article["thumb_media_id"] = thumb_media_id

        articles = [article]

        # 方法1: 尝试使用 httpx
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json={"articles": articles})
                data = resp.json()
                print(f"   [DEBUG] 创建草稿响应: {data}")
                if "media_id" in data:
                    return data["media_id"]
                elif "errcode" in data:
                    errcode = data.get("errcode")
                    errmsg = data.get("errmsg", "未知错误")
                    # 常见错误处理
                    if errcode == -1:
                        raise Exception(f"创建草稿失败: 微信服务繁忙 ({errcode})")
                    elif errcode == 615:
                        raise Exception(f"创建草稿失败: 日期格式错误 ({errcode})")
                    elif errcode == 40007:
                        raise Exception(f"创建草稿失败: thumb_media_id无效或已过期 ({errcode})")
                    else:
                        raise Exception(f"创建草稿失败: {errmsg} (错误码: {errcode})")
        except Exception as e:
            if "创建草稿失败" in str(e):
                raise
            print(f"  [INFO] httpx 创建草稿失败，尝试 aiohttp: {e}")

        # 方法2: 使用 aiohttp 作为备用
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"articles": articles}, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    data = await resp.json()
                    if "media_id" in data:
                        return data["media_id"]
                    elif "errcode" in data:
                        errcode = data.get("errcode")
                        errmsg = data.get("errmsg", "未知错误")
                        raise Exception(f"创建草稿失败: {errmsg} (错误码: {errcode})")
        except Exception as e:
            if "创建草稿失败" in str(e):
                raise
            raise Exception(f"创建草稿失败 (httpx和aiohttp都失败): {e}")

        raise Exception(f"创建草稿失败: {data}")
