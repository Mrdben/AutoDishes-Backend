import aiosqlite
from datetime import datetime
from typing import Optional
import json
from app.db_common import DB_PATH_AICHATS

async def create_aichats_table(db):
    """初始化数据库，创建用户表"""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS aichats (
            server_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            chat_id INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            prompt_tokens INTEGER NOT NULL,
            completion_tokens INTEGER NOT NULL,
            total_tokens INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            response_time INTEGER NOT NULL,
            user_prompt TEXT NOT NULL,
            model_response TEXT NOT NULL
        )
    """)

async def insert_aichat(user_id: int, chat_data: dict[str, any]):
    async with aiosqlite.connect(DB_PATH_AICHATS) as db:
        await db.execute(
            """
            INSERT INTO aichats
            (user_id, chat_id, model_name, 
            prompt_tokens, completion_tokens, total_tokens,
            created_at, response_time, 
            user_prompt, model_response
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
            user_id,
            chat_data['chat_id'],
            chat_data['model_name'],
            chat_data['prompt_tokens'],
            chat_data['completion_tokens'],
            chat_data['total_tokens'],
            chat_data['created_at'],
            chat_data['response_time'],
            chat_data['user_prompt'],
            chat_data['model_response'],
            )
        )
        await db.commit()

async def get_previous_replies(user_id: int, count: int) -> str: 
    async with aiosqlite.connect(DB_PATH_AICHATS) as db:
        cursor = await db.execute(
            """
            SELECT model_response FROM aichats WHERE user_id = ?
            ORDER BY server_id DESC LIMIT ?
            """, (
            user_id,
            count
            )
        )
        rows = await cursor.fetchall()
        return "\n".join(row[0] for row in rows)    
