import sqlite3
import os
import shutil
from datetime import datetime
from pathlib import Path

# 项目根目录（src的父目录）
current_dir = Path(__file__).parent.parent
db_path = current_dir / "content_wizard.db"
db_template = current_dir / "content_wizard.db.empty"


def ensure_db_exists():
    """确保数据库文件存在，如果不存在则从模板创建"""
    if not db_path.exists():
        # 确保目录存在
        db_path.parent.mkdir(parents=True, exist_ok=True)

        if db_template.exists():
            # 从模板复制
            shutil.copy(db_template, db_path)
        else:
            # 创建空数据库
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


class DBManager:
    def __init__(self):
        # 确保数据库存在
        ensure_db_exists()

        self.conn = sqlite3.connect(str(db_path))
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        self.cursor.execute('''
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
        self.conn.commit()

    def save_plans(self, plans_json):
        import json
        plans = json.loads(plans_json)
        for p in plans:
            self.cursor.execute('''
            INSERT OR REPLACE INTO article_plans (topic, reason, summary, target_date, status)
            VALUES (?, ?, ?, ?, ?)
            ''', (p['topic'], p['reason'], p['summary'], p['target_date'], p['status']))
        self.conn.commit()

    def update_plan(self, plan_id, field, new_value):
        query = f"UPDATE article_plans SET {field} = ? WHERE id = ?"
        self.cursor.execute(query, (new_value, plan_id))
        self.conn.commit()

    def delete_plan(self, plan_id):
        self.cursor.execute("DELETE FROM article_plans WHERE id = ?", (plan_id,))
        self.conn.commit()

    def get_pending_plans(self):
        self.cursor.execute("SELECT id, topic, target_date FROM article_plans WHERE status = 'planned' ORDER BY target_date ASC")
        return self.cursor.fetchall()

    def get_all_plans_raw(self):
        self.cursor.execute("SELECT * FROM article_plans")
        return self.cursor.fetchall()

    def mark_as_writing(self, topic_id):
        self.cursor.execute("UPDATE article_plans SET status = 'writing' WHERE id = ?", (topic_id,))
        self.conn.commit()

    def mark_as_published(self, topic_id, media_id):
        self.cursor.execute("UPDATE article_plans SET status = 'published', media_id = ? WHERE id = ?", (media_id, topic_id))
        self.conn.commit()

    def get_pending_count(self):
        """获取待写的选题数量"""
        self.cursor.execute("SELECT COUNT(*) FROM article_plans WHERE status = 'planned'")
        return self.cursor.fetchone()[0]

    def close(self):
        self.conn.close()
