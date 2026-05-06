import aiosqlite
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
            is_deleted INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

async def insert_family( family_data: dict[str, any]) -> dict:
    async with aiosqlite.connect(DB_PATH_FAMILIES) as db:
        await db.execute(
            """
            INSERT INTO families 
            (user_id, family_name, is_deleted)
            VALUES (?, ?, ?)
            """, (
            family_data['user_id'],
            family_data['family_name'],
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
    async with aiosqlite.connect(DB_PATH_FAMILIES) as db:
        await db.execute(
            """
            UPDATE families 
            SET family_name = ?, 
                is_deleted = ?, 
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """, (
            family_data['family_name'],
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
        

async def get_family_by_user_id(user_id: int) -> Optional[dict[str, any]]:
    async with aiosqlite.connect(DB_PATH_FAMILIES) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM families WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

async def get_update_time_by_user_id(user_id: int) -> str:
    async with aiosqlite.connect(DB_PATH_FAMILIES) as db:
        cursor = await db.execute(
            "SELECT updated_at FROM families WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]
        return None
