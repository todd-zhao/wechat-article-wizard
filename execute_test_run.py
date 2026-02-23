import asyncio
import os
import sys
import re
import httpx
from pathlib import Path
from dotenv import load_dotenv

# 环境路径
current_dir = Path(__file__).parent
root_path = current_dir.parent
sys.path.append(str(root_path))
sys.path.append(str(root_path / "backend"))
sys.path.append(str(root_path / "wechat_article_api"))
sys.path.append(str(current_dir / "src"))

# 加载环境变量
load_dotenv(current_dir / ".env")

from src.article_orchestrator import ArticleOrchestrator
from src.wechat_publisher import WeChatPublisher
from src.db_manager import DBManager
from src.dependency_checker import check_and_install_dependencies

def load_skill_file(filename):
    path = current_dir / "prompts" / filename
    if not path.exists() or os.path.getsize(path) < 10:
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_settings():
    """从环境变量加载配置（兼容旧代码）"""
    conf = {}
    # 优先从环境变量读取
    env_keys = [
        "WECHAT_APP_ID", "WECHAT_APP_SECRET",
        "CHERRY_API_BASE_URL", "CHERRY_API_KEY",
        "WRITER_API_BASE_URL", "WRITER_API_KEY",
        "WRITER_MODEL", "LAYOUT_MODEL", "IMAGE_GEN_MODEL"
    ]
    for key in env_keys:
        value = os.getenv(key)
        if value:
            conf[key] = value
    
    # 如果环境变量未设置，尝试从 config/setting.txt 读取（向后兼容）
    setting_file = current_dir / "config" / "setting.txt"
    if setting_file.exists():
        with open(setting_file, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    if k not in conf:  # 环境变量优先
                        conf[k] = v
    return conf

async def call_llm(base_url, api_key, model, system_prompt, user_prompt, max_tokens=4000):
    print(f"   [LLM] 调用模型: {model}")
    async with httpx.AsyncClient(timeout=600.0) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                "temperature": 0.7, "max_tokens": max_tokens
            }
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

async def main():
    # 0. 自检与环境准备
    check_and_install_dependencies()

    config = load_settings()
    db = DBManager()

    # 策略检查 - 如果为空，帮助用户生成账号定位
    strategy_content = load_skill_file("account_strategy.md")
    if not strategy_content:
        print("\n账号定位策略为空，正在与您对话来完成定位...")
        print("=" * 50)

        # 通过对话收集账号定位信息
        print("\n请回答以下问题，以便我帮您生成账号定位：\n")

        # 问题1：账号类型
        print("1. 您的公众号主要面向什么类型的读者？")
        print("   例如：职场人士、创业者、企业主、95后、00后等")

        # 这里我们使用LLM来帮助生成账号定位
        strategy_prompt = """你是一个资深的公众号运营顾问。请根据以下信息帮助用户生成一份完整的账号定位策略。

请先询问用户以下问题来了解情况：
1. 您的公众号主要面向什么类型的读者？（年龄、职业、兴趣等）
2. 您希望向读者传递什么核心价值？
3. 您希望读者看完文章后有什么收获？
4. 您的写作风格偏好是什么？（如：犀利、温暖、干货、故事型等）
5. 您目前有账号定位吗？

请以对话的方式向用户提问，等用户回答后再生成完整的账号定位策略。"""

        print("\n请稍候，AI正在准备问题...")
        response = await call_llm(
            config['WRITER_API_BASE_URL'], config['WRITER_API_KEY'],
            config['WRITER_MODEL'], strategy_prompt,
            "请开始与用户对话，了解账号定位需求", max_tokens=2000
        )

        # 保存响应，让用户确认
        with open(current_dir / "account_strategy_suggestion.md", "w", encoding="utf-8") as f:
            f.write(response)

        print("\n" + "=" * 50)
        print("AI已生成账号定位建议，已保存到 account_strategy_suggestion.md")
        print("=" * 50)
        print("\n请查看文件内容，确认后将其复制到 account_strategy.md 文件中，然后重新运行此脚本。")
        print("\n或者，您也可以直接告诉我您的答案，我来帮您生成完整的账号定位。")

        db.close()
        return

    # 自动获取待写计划
    pending = db.get_pending_plans()
    if not pending:
        print("数据库中没有待写的选题计划。请先添加选题计划。")
        db.close()
        return
    
    topic_id, topic, target_date = pending[0]
    print(f"[STRATEGY ALIGNMENT] 正在根据策略创作选题: {topic}")
    
    db.mark_as_writing(topic_id)
    
    # 1. 深度写作 (Claude Opus 4.5) - 注入策略语料
    writer_system_template = load_skill_file("writer_agent.md")
    # 核心修复：将策略和主题放入system prompt中，确保模型严格遵守
    writer_system = f"""{writer_system_template}

【最高优先级 - 账号定位必须严格遵守】
{strategy_content}

【本次写作主题】：{topic}

你必须100%围绕主题「{topic}」写作，禁止偏离。字数1500字以上。
"""

    writer_user = f"""主题：{topic}

请直接输出正文，不要有任何开场白。"""

    full_markdown = await call_llm(config['WRITER_API_BASE_URL'], config['WRITER_API_KEY'], config['WRITER_MODEL'], writer_system, writer_user, max_tokens=8000)

    # 保存原始markdown内容用于调试
    with open(current_dir / "debug_article.md", "w", encoding="utf-8") as f:
        f.write(f"# 主题: {topic}\n\n")
        f.write(f"# 账号定位:\n{strategy_content}\n\n")
        f.write(f"# 正文:\n{full_markdown}")

    # 1.5 生成摘要 (50-100字) - 使用全文和专业摘要人设
    print("   [LLM] 生成文章摘要 (使用 Layout Model)...")
    summary_system = load_skill_file("summary_agent.md")
    
    if not full_markdown or len(full_markdown) < 100:
        print("   [WARN] 文章内容过短，使用默认摘要")
        digest = f"深度解析：{topic}"
    else:
        # 彻底隔离：只提取 # 正文: 之后的内容发送给摘要模型
        pure_content = full_markdown
        if "# 正文:" in full_markdown:
            # 使用更鲁棒的正则切分
            parts = re.split(r'#\s*正文:', full_markdown, flags=re.IGNORECASE)
            if len(parts) > 1:
                pure_content = parts[1].strip()
        
        # 明确 Prompt 结构，只给正文，不给策略背景
        digest_prompt = f"请根据以下文章正文，生成 50-100 字的微信推送摘要。\n\n【文章标题】：{topic}\n【文章内容】：\n{pure_content}"
        
        try:
            # 切换到 LAYOUT_MODEL (Gemini) 进行摘要，它对内容识别更友好
            digest = await call_llm(
                config['CHERRY_API_BASE_URL'], 
                config['CHERRY_API_KEY'], 
                config['LAYOUT_MODEL'], 
                summary_system, 
                digest_prompt, 
                max_tokens=500
            )
            
            # 精细清理
            digest = re.sub(r'[#*`>]|\[IMAGE_PLACEHOLDER_\d+\]', '', digest)
            digest = re.sub(r'\s+', ' ', digest).strip()
            
            if len(digest) > 120:
                digest = digest[:117] + "..."
        except Exception as e:
            print(f"   [ERROR] 摘要生成失败: {e}")
            digest = f"深度解析：{topic}"

    # 保存摘要调试内容
    with open(current_dir / "debug_digest.txt", "w", encoding="utf-8") as f:
        f.write(f"主题: {topic}\n")
        f.write(f"摘要: {digest}")

    # 2. 生成图片 - 电影写实风格
    orchestrator = ArticleOrchestrator()
    # 封面：电影感、宽画幅、写实风格
    cover_prompt = f"Cinematic wide shot, {topic}, photorealistic, dramatic lighting, 2.35:1 aspect ratio, moody atmosphere, high contrast, professional photography, no text, --ar 2.35:1"
    # 插图：写实风格、叙事感、配合文章内容
    illustration_prompts = [
        f"Cinematic scene, business transformation struggle, photorealistic, dramatic light, 4:3 ratio, no text, --ar 4:3",
        f"Cinematic scene, organizational challenges, photorealistic, moody atmosphere, 4:3 ratio, no text, --ar 4:3",
        f"Cinematic scene, future opportunity, photorealistic, hopeful lighting, 4:3 ratio, no text, --ar 4:3"
    ]
    thumb_media_id, cdn_urls = await orchestrator.generate_and_upload_all_images(
        cover_prompt=cover_prompt,
        illustration_prompts=illustration_prompts
    )

    # 3. 排版 (必须设置 max_tokens=8000)
    layout_system = load_skill_file("pattern_editor.md")
    content_with_images = full_markdown
    for i, url in enumerate(cdn_urls): content_with_images = content_with_images.replace(f"[IMAGE_PLACEHOLDER_{i}]", url)

    layout_user = f"""请将以下Markdown文章转换为微信公众号HTML格式。

【关键要求】
1. 金句（> 引用格式）：必须添加装饰框，左边框4px #007AFF，背景#f8f9fa，圆角8px，左对齐
2. 段落：行高1.85，字间距1px
3. 图片：3:2比例，box-shadow阴影，圆角8px，80%宽度
4. 禁止图片放在文章开头
5. 直接输出HTML代码块，不要任何解释

文章内容：
{content_with_images}"""
    final_html = await call_llm(config['CHERRY_API_BASE_URL'], config['CHERRY_API_KEY'], config['LAYOUT_MODEL'], layout_system, layout_user, max_tokens=8000)
    if "```html" in final_html: final_html = final_html.split("```html")[1].split("```")[0].strip()

    # 4. 清理 HTML - 保留金句装饰框，去除空白装饰框
    # 去除开头的 h1/h2 标题
    final_html = re.sub(r'<h1[^>]*>.*?</h1>', '', final_html, flags=re.DOTALL | re.IGNORECASE)
    final_html = re.sub(r'<h2[^>]*>.*?</h2>', '', final_html, flags=re.DOTALL | re.IGNORECASE)
    # 去除 blockquote 前后多余的空格
    final_html = re.sub(r'>\s+', '>', final_html)
    final_html = re.sub(r'\s+<', '<', final_html)
    # 去除多余空行
    final_html = re.sub(r'\n\s*\n', '\n', final_html)
    # 去除首尾空格
    final_html = final_html.strip()
    # 只去除完全空白或只有空格的 blockquote（保留有内容的金句）
    final_html = re.sub(r'<blockquote[^>]*>\s*</blockquote>', '', final_html, flags=re.IGNORECASE)

    # 保存HTML调试内容
    with open(current_dir / "debug_article.html", "w", encoding="utf-8") as f:
        f.write(final_html)

    publisher = WeChatPublisher()
    draft_id = await publisher.create_draft(title=topic, content=final_html, digest=digest, thumb_media_id=thumb_media_id)
    
    db.mark_as_published(topic_id, draft_id)
    print(f"策略对齐创作完成！预览 ID: {draft_id}")
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
