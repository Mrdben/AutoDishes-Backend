import aiosqlite
import os

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

async def init_db():
    """初始化数据库，创建用户表"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        await db.commit()

async def create_user(username: str, password_hash: str):
    """创建用户"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        await db.commit()

async def get_user_by_username(username: str):
    """根据用户名查询用户"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,)
        )
        row = await cursor.fetchone()
        if row:
            return {"id": row[0], "username": row[1], "password_hash": row[2]}
        return None
