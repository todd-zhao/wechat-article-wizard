import sqlite3
import os
from pathlib import Path
from datetime import datetime
import sys

# 相对路径
current_dir = Path(__file__).parent.parent
db_path = current_dir / "content_wizard.db"

# 确保数据库存在
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
        print(f"[INFO] 已创建数据库: {db_path}")

# 先确保数据库存在
ensure_db_exists()

# 从命令行参数获取主题
if len(sys.argv) > 1:
    topic = sys.argv[1]
else:
    topic = "测试选题"

reason = "测试选题"
summary = "测试摘要"
target_date = datetime.now().strftime('%Y-%m-%d')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('''
INSERT OR REPLACE INTO article_plans (topic, reason, summary, target_date, status)
VALUES (?, ?, ?, ?, 'planned')
''', (topic, reason, summary, target_date))
conn.commit()
conn.close()
print(f"成功将选题同步至数据库：{topic}")
