import aiosqlite
from datetime import datetime
from typing import Optional
import json
from app.db_common import DB_PATH_ELDERS


async def create_elders_table(db):
    """初始化数据库，创建用户表"""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS elders (
            server_id INTEGER PRIMARY KEY AUTOINCREMENT,
            elder_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            gender TEXT NOT NULL,
            age INTEGER NOT NULL,
            allergens TEXT DEFAULT '[]',
            diseases TEXT DEFAULT '[]',
            dietary_restriction TEXT DEFAULT '[]',
            taste_preferences TEXT DEFAULT '[]',
            is_deleted INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, elder_id)
        )
    """)

async def insert_elder(elder_data: dict[str, any]) -> dict:
    async with aiosqlite.connect(DB_PATH_ELDERS) as db:
        await db.execute(
            """
            INSERT INTO elders
            (elder_id, user_id, name, gender, age,
            allergens, diseases, dietary_restriction, taste_preferences,
            is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
            elder_data['elder_id'],
            elder_data['user_id'],
            elder_data['name'],
            elder_data['gender'],
            elder_data['age'],
            json.dumps(elder_data['allergens']),
            json.dumps(elder_data['diseases']),
            json.dumps(elder_data['dietary_restriction']),
            json.dumps(elder_data['taste_preferences']),
            1 if elder_data['is_deleted'] else 0
            )
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT server_id, updated_at FROM elders WHERE user_id = ? AND elder_id = ?",
            (elder_data['user_id'], elder_data['elder_id'])
        )
        row = await cursor.fetchone()
        if row:
            return {"server_id" : row[0],
                    "updated_at" : row[1]}
        return None

async def update_elder(elder_data: dict[str, any]) -> dict:
    async with aiosqlite.connect(DB_PATH_ELDERS) as db:
        await db.execute(
            """
            UPDATE elders
            SET name = ?, 
                gender = ?,
                age = ?,
                allergens = ?,
                diseases = ?,
                dietary_restriction = ?,
                taste_preferences = ?,
                is_deleted = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE server_id = ?
            """, (
            elder_data['name'],
            elder_data['gender'],
            elder_data['age'],
            json.dumps(elder_data['allergens']),
            json.dumps(elder_data['diseases']),
            json.dumps(elder_data['dietary_restriction']),
            json.dumps(elder_data['taste_preferences']),
            1 if elder_data['is_deleted'] else 0,
            elder_data['server_id']
            )
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT server_id, updated_at FROM elders WHERE server_id = ?",
            (elder_data['server_id'],)
        )
        row = await cursor.fetchone()
        if row:
            return {"server_id" : row[0],
                    "updated_at" : row[1]}
        return None


async def get_elder_by_server_id(server_id: int) -> Optional[dict[str, any]]:
    async with aiosqlite.connect(DB_PATH_ELDERS) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM elders WHERE server_id = ?",
            (server_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

async def get_updated_time_by_server_id(server_id: int) -> str:
    async with aiosqlite.connect(DB_PATH_ELDERS) as db:
        cursor = await db.execute(
            "SELECT updated_at FROM elders WHERE server_id = ?",
            (server_id,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]
        return None

async def get_server_id_by_user_and_elder_ids(user_id: int, elder_id: str) -> int:
    async with aiosqlite.connect(DB_PATH_ELDERS) as db:
        cursor = await db.execute(
            "SELECT server_id FROM elders WHERE user_id = ? AND elder_id = ?",
            (user_id, elder_id,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]
        return None

async def pull_elders_by_user_id(user_id: int) -> list[dict[str, any]]:
    async with aiosqlite.connect(DB_PATH_ELDERS) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM elders WHERE user_id = ?",
            (user_id,)
        )
        result = []
        rows = await cursor.fetchall()
        for row in rows:
            result.append(dict(row))
        return result
  
