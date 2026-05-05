import aiosqlite
import json
from datetime import datetime
from typing import Optional 
from app.db_common import DB_PATH_FAMILIES

async def create_families_table(db):
    """初始化数据库，创建用户表"""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS families (
            family_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            family_name TEXT NOT NULL,
            elder_ids TEXT NOT NULL DEFAULT '[]',
            is_deleted INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

async def insert_family( family_data: dict[str, any]) -> dict:
    elder_ids_json = json.dumps(family_data.get('elder_ids', []))
    async with aiosqlite.connect(DB_PATH_FAMILIES) as db:
        await db.execute(
            """
            INSERT INTO families 
            (user_id, family_name, elder_ids, is_deleted)
            VALUES (?, ?, ?, ?)
            """, (
            family_data['user_id'],
            family_data['family_name'],
            elder_ids_json,
            1 if family_data.get('is_deleted') else 0)
        )
        cursor = await db.execute(
            "SELECT family_id, updated_at FROM families WHERE user_id = ?",
            (family_data['user_id'],)
        )
        row = await cursor.fetchone()
        await db.commit()
        if row:
            return {"family_id" : row[0],
                    "updated_at" : row[1]}
        return None

async def update_family(family_data: dict[str, any]) -> dict:
    elder_ids_json = json.dumps(family_data.get('elder_ids', []))
    async with aiosqlite.connect(DB_PATH_FAMILIES) as db:
        await db.execute(
            """
            UPDATE families 
            SET family_name = ?, 
                elder_ids = ?, 
                is_deleted = ?, 
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """, (
            family_data['family_name'],
            elder_ids_json,
            1 if family_data.get('is_deleted') else 0,
            family_data['user_id'])
            )
        cursor = await db.execute(
            "SELECT family_id, updated_at FROM families WHERE user_id = ?",
            (family_data['user_id'],)
        )
        row = await cursor.fetchone()
        await db.commit()
        if row:
            return {"family_id" : row[0],
                    "updated_at" : row[1]}
        return None
        

async def get_family_by_user_id(user_id: str) -> Optional[dict[str, any]]:
    async with aiosqlite.connect(DB_PATH_FAMILIES) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM families WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            try:
                data['elder_ids'] = json.loads(data['elder_ids'])
            except json.JSONDecodeError:
                data['elder_ids'] = []
            return data
        return None

async def get_update_time_by_user_id(user_id: str) -> str:
    async with aiosqlite.connect(DB_PATH_FAMILIES) as db:
        cursor = await db.execute(
            "SELECT updated_at FROM families WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]
        return None
