import asyncio
import os
import httpx
from typing import List, Tuple, Dict
from .config import Config


class ArticleOrchestrator:
    """图片生成和上传协调器"""

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
            # 图片生成使用独立的 API 地址
            "IMAGE_GEN_BASE_URL": Config.IMAGE_GEN_BASE_URL,
        }
        self.upload_dir = os.path.join(os.path.dirname(__file__), "..", "images")
        os.makedirs(self.upload_dir, exist_ok=True)

        # 缓存access_token
        self._token = None
        self._token_expires = 0

    async def _get_access_token(self) -> str:
        """获取微信access_token"""
        import time
        if self._token and time.time() < self._token_expires:
            return self._token

        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.settings.get("WECHAT_APP_ID"),
            "secret": self.settings.get("WECHAT_APP_SECRET")
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
            if "access_token" in data:
                self._token = data["access_token"]
                self._token_expires = time.time() + data["expires_in"] - 300
                return self._token
            else:
                raise Exception(f"获取token失败: {data}")

    async def _upload_image_to_wechat(self, image_path: str, image_type: str = "image", is_permanent: bool = False, is_article_image: bool = False) -> dict:
        """上传图片到微信素材库

        Args:
            image_path: 图片本地路径
            image_type: 素材类型 (image/thumb)
            is_permanent: 是否上传为永久素材
            is_article_image: 是否上传为图文消息图片（使用uploadimg接口）

        优先使用 httpx，失败则使用 aiohttp 作为备用
        """
        token = await self._get_access_token()

        # 选择上传接口
        if is_article_image:
            # 图文消息图片接口 - 返回可直接使用的URL，不占用素材数量限制
            url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
        elif is_permanent:
            # 永久素材
            url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type={image_type}"
        else:
            # 临时素材
            url = f"https://api.weixin.qq.com/cgi-bin/media/upload?access_token={token}&type={image_type}"

        # 根据图片类型设置content_type
        content_type = 'image/png' if image_path.endswith('.png') else 'image/jpeg'

        # 方法1: 尝试使用 httpx
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(image_path, 'rb') as f:
                    files = {'media': (os.path.basename(image_path), f, content_type)}
                    resp = await client.post(url, files=files)
                    result = resp.json()
                    print(f"   [DEBUG] {'图文' if is_article_image else ('永久' if is_permanent else '临时')}图片上传结果: {result}")
                    return result
        except Exception as e:
            print(f"   [INFO] httpx 上传失败，尝试 aiohttp: {e}")

        # 方法2: 使用 aiohttp 作为备用
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                with open(image_path, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('media', f, filename=os.path.basename(image_path), content_type=content_type)
                    async with session.post(url, data=data, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                        result = await resp.json()
                        print(f"   [DEBUG] aiohttp {'图文' if is_article_image else ('永久' if is_permanent else '临时')}图片上传结果: {result}")
                        return result
        except Exception as e:
            raise Exception(f"图片上传失败 (httpx和aiohttp都失败): {e}")

    async def generate_and_upload_all_images(self,
                                            cover_prompt: str,
                                            illustration_prompts: List[str]) -> Tuple[str, List[str]]:
        """
        1. Generate cover and illustrations via LLM API
        2. Download them locally
        3. Upload cover to WeChat (media_id)
        4. Upload illustrations to WeChat (CDN URL)
        Returns: (thumb_media_id, [content_image_urls])
        """
        print("[图片] 正在生成封面...")

        # 调用图片生成API
        cover_url = await self._generate_image(cover_prompt)

        # 下载封面
        cover_path = os.path.join(self.upload_dir, "cover.png")
        await self._download_image(cover_url, cover_path)

        # 上传封面到微信 - 使用永久 thumb 素材获取 media_id
        print("[图片] 上传封面到微信（永久素材）...")
        cover_result = await self._upload_image_to_wechat(cover_path, "thumb", is_permanent=True)

        # 检查上传结果 - thumb 永久素材会返回 media_id
        if "media_id" in cover_result:
            thumb_media_id = cover_result["media_id"]
            print(f"   封面上传成功，media_id: {thumb_media_id[:20]}...")
        elif "errcode" in cover_result:
            errcode = cover_result.get('errcode')
            errmsg = cover_result.get('errmsg', '未知错误')
            print(f"   [WARN] 永久素材上传失败，尝试临时素材: {errmsg}")
            # 备用：尝试使用临时素材
            temp_result = await self._upload_image_to_wechat(cover_path, "thumb", is_permanent=False)
            if "media_id" in temp_result:
                thumb_media_id = temp_result["media_id"]
                print(f"   [INFO] 临时封面上传成功，media_id: {thumb_media_id[:20]}...")
            else:
                print(f"   [WARN] 临时素材也失败: {temp_result}")
                thumb_media_id = None
        else:
            print(f"   [WARN] 封面上传返回异常: {cover_result}")
            thumb_media_id = None

        # 生成并上传插图
        cdn_urls = []
        for i, prompt in enumerate(illustration_prompts):
            print(f"[图片] 正在生成插图 {i+1}/{len(illustration_prompts)}...")

            # 生成图片
            img_url = await self._generate_image(prompt)

            # 下载
            img_path = os.path.join(self.upload_dir, f"illustration_{i}.png")
            await self._download_image(img_url, img_path)

            # 上传到微信 - 插图使用图文消息图片接口（返回可直接使用的URL）
            print(f"[图片] 上传插图 {i+1} 到微信（图文图片）...")
            result = await self._upload_image_to_wechat(img_path, "image", is_article_image=True)

            # 获取CDN URL - 图文图片接口会返回 url 字段
            if "url" in result:
                cdn_url = result["url"]
                print(f"   插图 {i+1} 上传成功，URL: {cdn_url[:50]}...")
            elif "errcode" in result:
                errcode = result.get('errcode')
                errmsg = result.get('errmsg', '未知错误')
                print(f"   [WARN] 图文图片上传失败: {errmsg}")
                # 备用：使用原始生成的图片URL
                cdn_url = img_url
                print(f"   [WARN] 使用原始图片URL")
            else:
                cdn_url = img_url
                print(f"   [WARN] 插图 {i+1} 返回异常，使用原始URL")

            cdn_urls.append(cdn_url)

        return thumb_media_id, cdn_urls

    async def _generate_image(self, prompt: str) -> str:
        """调用LLM API生成图片

        优先使用 httpx，失败则使用 aiohttp 作为备用
        """
        api_key = self.settings.get("CHERRY_API_KEY")
        # 使用图片生成专用 API 地址
        base_url = self.settings.get("IMAGE_GEN_BASE_URL", "https://open.cherryin.ai/v1/images/generations")
        model = self.settings.get("IMAGE_GEN_MODEL", "qwen/qwen-image(free)")

        # 直接使用 base_url（已经是完整URL）
        api_urls = [base_url]

        last_error = None
        for url in api_urls:
            # 方法1: 尝试使用 httpx
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    resp = await client.post(
                        url,
                        headers={"Authorization": f"Bearer {api_key}"},
                        json={
                            "model": model,
                            "prompt": prompt,
                            "n": 1,
                            "size": "1024x1024"
                        }
                    )
                    print(f"  [DEBUG] httpx 响应状态: {resp.status_code}")
                    data = resp.json()
                    print(f"  [DEBUG] httpx 响应: {data}")
                    # 兼容不同返回格式
                    if "data" in data and len(data["data"]) > 0:
                        return data["data"][0].get("url", "") or data["data"][0].get("b64_json", "")
                    elif "url" in data:
                        return data["url"]
                    elif "image_url" in data:
                        return data["image_url"]
                    elif "error" in data:
                        last_error = data["error"]
                        print(f"  [INFO] API返回错误: {data['error']}")
            except Exception as e:
                last_error = e
                print(f"  [INFO] {url} 失败: {e}")
                continue

            # 方法2: 使用 aiohttp 作为备用
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        headers={"Authorization": f"Bearer {api_key}"},
                        json={
                            "model": model,
                            "prompt": prompt,
                            "n": 1,
                            "size": "1024x1024"
                        },
                        timeout=aiohttp.ClientTimeout(total=120)
                    ) as resp:
                        data = await resp.json()
                        print(f"  [DEBUG] aiohttp 响应: {data}")
                        if "data" in data and len(data["data"]) > 0:
                            return data["data"][0].get("url", "") or data["data"][0].get("b64_json", "")
                        elif "url" in data:
                            return data["url"]
            except Exception as e:
                last_error = e
                continue

        raise Exception(f"图片生成失败: {last_error}")

    async def _download_image(self, url: str, path: str):
        """下载图片到本地

        优先使用 httpx，失败则使用 aiohttp 作为备用
        """
        # 方法1: 尝试使用 httpx
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                with open(path, 'wb') as f:
                    f.write(resp.content)
                return
        except Exception as e:
            print(f"  [INFO] httpx 下载失败，尝试 aiohttp: {e}")

        # 方法2: 使用 aiohttp 作为备用
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    data = await resp.read()
                    with open(path, 'wb') as f:
                        f.write(data)
        except Exception as e:
            raise Exception(f"图片下载失败: {e}")
