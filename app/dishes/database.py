import aiosqlite
from datetime import datetime
from typing import Optional
import json
from app.db_common import DB_PATH_DISHES


async def create_dishes_table(db):
    """初始化数据库，创建用户表"""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS dishes (
            server_id INTEGER PRIMARY KEY AUTOINCREMENT,
            dish_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            taste TEXT NOT NULL,
            dish_type TEXT NOT NULL,
            cuisine TEXT NOT NULL,
            ingredients TEXT NOT NULL,
            recipe TEXT NOT NULL,
            favorite_level INTEGER NOT NULL,
            is_deleted INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, dish_id)
        )
    """)

async def insert_dish(user_id: int, dish_data: dict[str, any]) -> dict:
    async with aiosqlite.connect(DB_PATH_DISHES) as db:
        await db.execute(
            """
            INSERT INTO dishes
            (dish_id, user_id, name, taste, dish_type, 
            cuisine, ingredients, recipe, favorite_level,
            is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
            dish_data['dish_id'],
            user_id,
            dish_data['name'],
            dish_data['taste'],
            dish_data['dish_type'],
            dish_data['cuisine'],
            dish_data['ingredients'],
            dish_data['recipe'],
            dish_data['favorite_level'],
            1 if dish_data['is_deleted'] else 0
            )
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT updated_at FROM dishes WHERE user_id = ? AND dish_id = ?",
            (user_id, dish_data['dish_id'])
        )
        row = await cursor.fetchone()
        if row:
            return {"dish_id" : dish_data['dish_id'],
                    "updated_at" : row[0]}
        return None

async def update_dish(server_id: int, dish_data: dict[str, any]) -> dict:
    async with aiosqlite.connect(DB_PATH_DISHES) as db:
        await db.execute(
            """
            UPDATE dishes
            SET name = ?,
                taste = ?,
                dish_type = ?,
                cuisine = ?,
                ingredients = ?,
                recipe = ?,
                favorite_level = ?,
                is_deleted = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE server_id = ?
            """, (
            dish_data['name'],
            dish_data['taste'],
            dish_data['dish_type'],
            dish_data['cuisine'],
            dish_data['ingredients'],
            dish_data['recipe'],
            dish_data['favorite_level'],
            1 if dish_data['is_deleted'] else 0,
            server_id
            )
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT updated_at FROM dishes WHERE server_id = ?",
            (server_id,)
        )
        row = await cursor.fetchone()
        if row:
            return {"dish_id" : dish_data['dish_id'],
                    "updated_at" : row[0]}
        return None

async def get_updated_time_by_server_id(server_id: int) -> str:
    async with aiosqlite.connect(DB_PATH_DISHES) as db:
        cursor = await db.execute(
            "SELECT updated_at FROM dishes WHERE server_id = ?",
            (server_id,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]
        return None

async def get_server_id_by_user_and_dish_ids(user_id: int, dish_id: str) -> int:
    async with aiosqlite.connect(DB_PATH_DISHES) as db:
        cursor = await db.execute(
            "SELECT server_id FROM dishes WHERE user_id = ? AND dish_id = ?",
            (user_id, dish_id,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]
        return None

async def get_dishes_by_user_id(user_id: int) -> list[dict[str, any]]:
    async with aiosqlite.connect(DB_PATH_DISHES) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM dishes WHERE user_id = ?",
            (user_id,)
        )
        result = []
        rows = await cursor.fetchall()
        for row in rows:
            result.append(dict(row))
        return result

