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
                password_hash TEXT NOT NULL,
                phone_number TEXT UNIQUE NOT NULL,
                refresh_token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def create_user(username: str, password_hash: str, phone_number: str):
    """创建用户"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (username, password_hash, phone_number) VALUES (?, ?, ?)",
            (username, password_hash, phone_number,)
        )
        await db.commit()

async def get_user_by_username_or_phone_number(username: str):
    """根据用户名查询用户"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, username, password_hash, phone_number, created_at FROM users WHERE username = ? OR phone_number = ?",
            (username, username,)
        )
        row = await cursor.fetchone()
        if row:
            return {"id": row[0], 
                    "username": row[1], 
                    "password_hash": row[2], 
                    "phone_number": row[3],
                    "created_at": row[4]}
        return None

async def get_username_by_phone_number(phone_number: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT username FROM users WHERE phone_number = ? ",
            (phone_number,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]
        return None

async def write_refresh_token_to_user(username: str, refresh_token: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET refresh_token = ? WHERE username = ?",
            (refresh_token, username,)
        )
        await db.commit()
    
async def get_username_by_refresh_token(refresh_token: str):
    """根据用户名查询用户"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT username FROM users WHERE refresh_token = ?",
            (refresh_token,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]
        return None
        
async def update_user_password(username: str, new_password_hash: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (new_password_hash, username,)
        )
        await db.execute(
            "UPDATE users SET refresh_token = NULL WHERE username = ?",
            (username,)
        )
        await db.commit()

async def update_user_phone_number(username: str, new_phone_number: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET phone_number = ? WHERE username = ?",
            (new_phone_number, username,)
        )
        await db.execute(
            "UPDATE users SET refresh_token = NULL WHERE username = ?",
            (username,)
        )
        await db.commit()
        
async def delete_user(username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users WHERE username = ?", (username,))
        await db.commit()

