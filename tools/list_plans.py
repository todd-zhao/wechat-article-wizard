import sqlite3
import os
from pathlib import Path

# 环境路径
current_dir = Path(__file__).parent.parent
db_path = current_dir / "content_wizard.db"

def ensure_db_exists():
    """确保数据库和表存在"""
    if not db_path.exists():
        # 创建数据库和表
        conn = sqlite3.connect(str(db_path))
        conn.execute('''
        CREATE TABLE IF NOT EXISTS article_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL UNIQUE,
            reason TEXT,
            summary TEXT,
            target_date TEXT,
            status TEXT DEFAULT 'planned',
            media_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()
        conn.close()
        return True
    return False

def list_plans():
    # 确保数据库存在
    db_created = ensure_db_exists()
    if db_created:
        print("[INFO] 已创建数据库")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, topic, target_date, status FROM article_plans ORDER BY target_date ASC")
    plans = cursor.fetchall()

    if not plans:
        print("\n[INFO] 暂无选题计划")
        print("使用 python tools/add_new_topic.py \"选题名称\" 添加选题")
        conn.close()
        return

    print("\n[选题计划] 公众号选题一览:")
    print("-" * 80)
    print(f"{'ID':<3} | {'日期':<12} | {'状态':<10} | {'选题'}")
    print("-" * 80)
    for p in plans:
        # 为了美观处理下中文字符对齐 (简易处理)
        print(f"{p[0]:<3} | {p[2]:<12} | {p[3]:<10} | {p[1]}")
    print("-" * 80)
    conn.close()

if __name__ == "__main__":
    list_plans()
