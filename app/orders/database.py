import aiosqlite
from datetime import datetime
from typing import Optional
import json
from app.db_common import DB_PATH_ORDERS


async def create_orders_table(db):
    """初始化数据库，创建用户表"""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            server_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            meal_type TEXT NOT NULL,
            meal_time TEXT NOT NULL,
            elder_ids TEXT NOT NULL,
            dish_ids TEXT NOT NULL,
            is_deleted INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, order_id)
        )
    """)

async def insert_order(user_id: int, order_data: dict[str, any]) -> dict:
    async with aiosqlite.connect(DB_PATH_ORDERS) as db:
        await db.execute(
            """
            INSERT INTO orders
            (order_id, user_id, meal_type, meal_time,
            elder_ids, dish_ids,
            is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
            order_data['order_id'],
            user_id,
            order_data['meal_type'],
            order_data['meal_time'],
            json.dumps(order_data['elder_ids']),
            json.dumps(order_data['dish_ids']),
            1 if order_data['is_deleted'] else 0
            )
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT updated_at FROM orders WHERE user_id = ? AND order_id = ?",
            (user_id, order_data['order_id'])
        )
        row = await cursor.fetchone()
        if row:
            return {"order_id" : order_data['order_id'],
                    "updated_at" : row[0]}
        return None

async def update_order(server_id: int, order_data: dict[str, any]) -> dict:
    async with aiosqlite.connect(DB_PATH_ORDERS) as db:
        await db.execute(
            """
            UPDATE orders
            SET meal_type = ?,
                meal_time = ?,
                elder_ids = ?,
                dish_ids = ?,
                is_deleted = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE server_id = ?
            """, (
            order_data['meal_type'],
            order_data['meal_time'],
            json.dumps(order_data['elder_ids']),
            json.dumps(order_data['dish_ids']),
            1 if order_data['is_deleted'] else 0,
            server_id
            )
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT updated_at FROM orders WHERE server_id = ?",
            (server_id,)
        )
        row = await cursor.fetchone()
        if row:
            return {"order_id" : order_data['order_id'],
                    "updated_at" : row[0]}
        return None

async def get_updated_time_by_server_id(server_id: int) -> str:
    async with aiosqlite.connect(DB_PATH_ORDERS) as db:
        cursor = await db.execute(
            "SELECT updated_at FROM orders WHERE server_id = ?",
            (server_id,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]
        return None

async def get_server_id_by_user_and_order_ids(user_id: int, order_id: str) -> int:
    async with aiosqlite.connect(DB_PATH_ORDERS) as db:
        cursor = await db.execute(
            "SELECT server_id FROM orders WHERE user_id = ? AND order_id = ?",
            (user_id, order_id,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]
        return None

async def get_orders_by_user_id(user_id: int) -> list[dict[str, any]]:
    async with aiosqlite.connect(DB_PATH_ORDERS) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM orders WHERE user_id = ?",
            (user_id,)
        )
        result = []
        rows = await cursor.fetchall()
        for row in rows:
            result.append(dict(row))
        return result

