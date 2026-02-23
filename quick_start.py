#!/usr/bin/env python
"""
公众号写作助手 - 快速启动
输入主题，一键生成文章
"""

import os
import sys
import asyncio
import re

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, "src"))

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def load_settings():
    from src.config import Config
    Config.reload()
    return {
        "CHERRY_API_KEY": Config.CHERRY_API_KEY,
        "CHERRY_API_BASE_URL": Config.CHERRY_API_BASE_URL,
        "WRITER_MODEL": Config.WRITER_MODEL,
        "LAYOUT_MODEL": Config.LAYOUT_MODEL,
        "IMAGE_GEN_MODEL": Config.IMAGE_GEN_MODEL,
        "WECHAT_APP_ID": Config.WECHAT_APP_ID,
        "WECHAT_APP_SECRET": Config.WECHAT_APP_SECRET,
    }


def load_prompt_file(filename):
    path = os.path.join(current_dir, "prompts", filename)
    if os.path.exists(path) and os.path.getsize(path) > 10:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def load_style_template(style: str = "default") -> str:
    """加载排版风格模板"""
    try:
        from src.style_config import get_style_file_path
        style_path = get_style_file_path(style)
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception:
        pass
    
    style_map = {
        "default": "pattern_editor.md",
        "business": "pattern_business.md",
        "minimalist": "pattern_minimalist.md",
        "elegant": "pattern_elegant.md",
        "creative": "pattern_creative.md"
    }
    return load_prompt_file(style_map.get(style, "pattern_editor.md"))


def save_to_resources(topic: str, html_content: str, image_urls: list = None) -> str:
    import shutil
    from pathlib import Path
    
    resources_dir = os.path.join(current_dir, "resources")
    os.makedirs(resources_dir, exist_ok=True)
    
    safe_topic = re.sub(r'[<>:"/\\|?*]', '_', topic)[:50]
    article_dir = os.path.join(resources_dir, safe_topic)
    os.makedirs(article_dir, exist_ok=True)
    
    html_path = os.path.join(article_dir, "article.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"   已保存文章：article.html")
    
    if image_urls:
        images_dir = os.path.join(article_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        import httpx
        from urllib.parse import urlparse
        try:
            with httpx.Client(timeout=30.0) as client:
                for idx, url in enumerate(image_urls):
                    try:
                        resp = client.get(url)
                        if resp.status_code == 200:
                            parsed = urlparse(url)
                            ext = os.path.splitext(parsed.path)[1].lstrip('.')[:4] or 'png'
                            img_path = os.path.join(images_dir, f"image_{idx}.{ext}")
                            with open(img_path, 'wb') as img_f:
                                img_f.write(resp.content)
                            print(f"   已保存图片：images/image_{idx}.{ext}")
                    except Exception as e:
                        print(f"   [WARN] 保存图片 {idx} 失败：{e}")
        except Exception as e:
            print(f"   [WARN] 下载图片失败：{e}")
    
    meta_path = os.path.join(article_dir, "meta.txt")
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"主题：{topic}\n")
        from datetime import datetime
        f.write(f"生成时间：{datetime.now()}\n")
        f.write(f"图片数量：{len(image_urls) if image_urls else 0}\n")
    
    return article_dir


async def call_llm(base_url, api_key, model, system_prompt, user_prompt, max_tokens=4000):
    import httpx
    async with httpx.AsyncClient(timeout=600.0) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": max_tokens
            }
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def generate_article(topic, no_publish=False, article_content=None, style: str = "default"):
    """生成文章
    
    Args:
        topic: 文章主题
        no_publish: 是否跳过微信发布
        article_content: 外部传入的文章内容（可选）
        style: 排版风格
    """
    print(f"\n开始生成文章：{topic}")
    print("-" * 50)
    
    config = load_settings()
    
    required = ["CHERRY_API_KEY", "WRITER_MODEL"]
    for key in required:
        if key not in config:
            print(f"[ERROR] 缺少配置：{key}")
            return
    
    writer_prompt = load_prompt_file("writer_agent.md")
    strategy = load_prompt_file("account_strategy.md")
    
    # 判断是否使用外部传入的文章内容
    if article_content:
        print("[1/4] 使用外部传入的文章内容...")
        article = article_content
        print(f"   完成！文章长度：{len(article)} 字")
    else:
        system = f"""{writer_prompt}

【最高优先级 - 账号定位必须严格遵守】
{strategy}

【本次写作主题】：{topic}

你必须 100% 围绕主题「{topic}」写作，禁止偏离。字数 1500 字以上。
"""
        user = f"主题：{topic}\n\n请直接输出正文，不要有任何开场白。"
        
        print("[1/4] 正在写作...")
        try:
            article = await call_llm(
                config.get("CHERRY_API_BASE_URL", "https://open.cherryin.ai/v1"),
                config["CHERRY_API_KEY"],
                config["WRITER_MODEL"],
                system,
                user,
                max_tokens=8000
            )
            print(f"   完成！文章长度：{len(article)} 字")
        except Exception as e:
            print(f"   [ERROR] 写作失败：{e}")
            return
    
    # 生成摘要
    print("[2/4] 生成摘要...")
    summary_system = load_prompt_file("summary_agent.md")
    
    if not article or len(article) < 100:
        print("   [WARN] 文章内容过短，使用默认摘要")
        digest = f"深度解析：{topic}"
    else:
        pure_content = re.sub(r'\[IMAGE_PLACEHOLDER_\d+\]', '', article)
        digest_prompt = f"请根据以下文章正文，生成 50-100 字的微信推送摘要。\n\n【文章标题】：{topic}\n【文章内容】：\n{pure_content}"
        
        try:
            digest = await call_llm(
                config.get("CHERRY_API_BASE_URL", "https://open.cherryin.ai/v1"),
                config["CHERRY_API_KEY"],
                config.get("LAYOUT_MODEL", "google/gemini-3-flash-preview"),
                summary_system if summary_system else "你是一个专业的微信编辑，擅长从长文中提取核心要点，生成 50-100 字的推送摘要。",
                digest_prompt,
                max_tokens=500
            )
            digest = re.sub(r'[#*`>]|\[IMAGE_PLACEHOLDER_\d+\]', '', digest)
            digest = re.sub(r'\s+', ' ', digest).strip()
            if len(digest) > 120:
                digest = digest[:117] + "..."
        except Exception as e:
            print(f"   [ERROR] 摘要生成失败：{e}")
            digest = f"深度解析：{topic}"
    
    with open(os.path.join(current_dir, "debug_digest.txt"), "w", encoding="utf-8") as f:
        f.write(f"主题：{topic}\n摘要：{digest}")
    
    # 生成图片
    print("[3/4] 生成配图...")
    try:
        from src.article_orchestrator import ArticleOrchestrator
        orchestrator = ArticleOrchestrator()
        
        cover_prompt = f"Cinematic wide shot, {topic}, photorealistic, dramatic lighting, 2.35:1, moody atmosphere, no text, --ar 2.35:1"
        illustration_prompts = [
            f"Cinematic scene, {topic}, photorealistic, dramatic light, 4:3, no text, --ar 4:3",
            f"Cinematic scene, business context, photorealistic, moody, 4:3, no text, --ar 4:3",
            f"Cinematic scene, future opportunity, photorealistic, hopeful, 4:3, no text, --ar 4:3"
        ]
        
        thumb_media_id, cdn_urls = await orchestrator.generate_and_upload_all_images(
            cover_prompt=cover_prompt,
            illustration_prompts=illustration_prompts
        )
        print("   完成！图片已上传微信素材库")
        
        for i, url in enumerate(cdn_urls):
            article = article.replace(f"[IMAGE_PLACEHOLDER_{i}]", url)
    except Exception as e:
        print(f"   [WARN] 图片生成失败：{e}")
        thumb_media_id = None
        cdn_urls = []
    
    # 排版
    print("[4/4] HTML 排版...")
    try:
        layout_prompt = load_style_template(style)
        content_with_images = article
        
        layout_user = f"""请将以下 Markdown 文章转换为微信公众号 HTML 格式。

【关键要求】
1. 金句（> 引用格式）：必须添加装饰框
2. 段落：行高适中，字间距舒适
3. 图片：圆角阴影，居中显示
4. 禁止图片放在文章开头
5. 直接输出 HTML 代码块

文章内容：
{content_with_images}"""
        
        html_content = await call_llm(
            config.get("CHERRY_API_BASE_URL", "https://open.cherryin.ai/v1"),
            config["CHERRY_API_KEY"],
            config.get("LAYOUT_MODEL", "google/gemini-3-flash-preview"),
            layout_prompt,
            layout_user,
            max_tokens=8000
        )
        
        if "```html" in html_content:
            html_content = html_content.split("```html")[1].split("```")[0].strip()
        
        html_content = re.sub(r'<h1[^>]*>.*?</h1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<h2[^>]*>.*?</h2>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<blockquote[^>]*>\s*</blockquote>', '', html_content, flags=re.IGNORECASE)
        print("   完成！")
    except Exception as e:
        print(f"   [WARN] 排版失败：{e}")
        html_content = f"<h1>{topic}</h1><p>{article}</p>"
    
    # 保存文章和图片
    resource_dir = save_to_resources(topic, html_content, cdn_urls)
    print(f"\n[INFO] 文章已保存到：{resource_dir}")
    
    # 记录风格使用
    try:
        from src.style_config import record_style_usage
        record_style_usage(style)
    except Exception:
        pass
    
    if no_publish:
        print("\n[INFO] 已跳过微信发布")
        return
    
    # 发布到微信
    print("\n正在创建微信草稿...")
    try:
        from src.wechat_publisher import WeChatPublisher
        publisher = WeChatPublisher()
        draft_id = await publisher.create_draft(
            title=topic,
            content=html_content,
            digest=digest,
            thumb_media_id=thumb_media_id
        )
        print(f"\n[SUCCESS] 文章生成完成！")
        print(f"   微信草稿 ID: {draft_id}")
        print(f"   登录 https://mp.weixin.qq.com/ 查看草稿")
    except Exception as e:
        print(f"   [ERROR] 发布失败：{e}")


def load_article_from_file(filepath: str) -> str:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在：{filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="公众号写作助手 - 快速写作")
    parser.add_argument("topic", nargs="?", help="文章主题")
    parser.add_argument("--no-publish", action="store_true", help="仅生成文章，不发布到微信")
    parser.add_argument("--content", "-c", help="直接传入文章内容（Markdown 格式）")
    parser.add_argument("--from-file", "-f", help="从文件读取文章内容")
    parser.add_argument("--style", "-s", help="排版风格（默认：从配置文件读取）")
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("   公众号写作助手 - 快速写作")
    print("=" * 50)
    
    config = load_settings()
    if not config.get("CHERRY_API_KEY"):
        print("\n[ERROR] 请先配置 API Key")
        print("\n💡 还没有 API Key？")
        print("   推荐注册：https://open.cherryin.ai/register?aff=gXKS")
        print("   注册后在 CherryStudio 设置中生成 API Key")
        print("\n运行：python tools/auto_setup.py --credentials <appid> <secret> --api-key <key>")
        sys.exit(1)
    
    if not config.get("WECHAT_APP_ID"):
        print("\n[ERROR] 请先配置微信 AppID")
        sys.exit(1)
    
    topic = args.topic
    if not topic:
        topic = input("\n请输入文章主题：").strip()
    
    if not topic:
        print("[ERROR] 主题不能为空")
        sys.exit(1)
    
    # 确定排版风格
    style = args.style
    style_source = "命令行参数"
    
    if not style:
        try:
            from src.style_config import get_default_style
            style = get_default_style()
            style_source = "配置文件"
        except Exception:
            style = "default"
            style_source = "系统默认"
    
    article_content = None
    if args.content:
        print(f"\n使用传入的文章内容...")
        article_content = args.content
    elif args.from_file:
        print(f"\n从文件加载文章：{args.from_file}")
        try:
            article_content = load_article_from_file(args.from_file)
            print(f"   已加载 {len(article_content)} 字")
        except Exception as e:
            print(f"   [ERROR] 读取文件失败：{e}")
            sys.exit(1)
    
    print(f"\n主题：{topic}")
    if article_content:
        print("模式：使用外部传入的文章内容")
    print(f"排版风格：{style} ({style_source})")
    print("开始写作流程...\n")
    
    asyncio.run(generate_article(topic, no_publish=args.no_publish, article_content=article_content, style=style))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消")
