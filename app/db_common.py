import os
import aiosqlite
from .encryption import get_username_by_access_token
from fastapi import HTTPException

DB_PATH_USERS = os.path.join(os.path.dirname(__file__), "users.db")
DB_PATH_ELDERS = os.path.join(os.path.dirname(__file__), "elders.db")
DB_PATH_DISHES = os.path.join(os.path.dirname(__file__), "dishes.db")
DB_PATH_ORDERS = os.path.join(os.path.dirname(__file__), "orders.db")
DB_PATH_AICHATS = os.path.join(os.path.dirname(__file__), "aichats.db")

async def get_user_id_from_token(token):
    # 1, get username from token
    username, refresh, error_message = get_username_by_access_token(token)
    if (not username) or (not refresh):
        raise HTTPException(status_code=401, detail=error_message)
        
    refresh_username = await get_username_by_refresh_token(refresh)
    if (not refresh_username) or (refresh_username != username):
        raise HTTPException(status_code=401, detail="刷新令牌无效或已过期")

# 2, check user info
    user_id = await get_user_id_by_username(username)
    if not user_id:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user_id

async def get_user_id_by_username(username: str):
    async with aiosqlite.connect(DB_PATH_USERS) as db:
        cursor = await db.execute(
            "SELECT id FROM users WHERE username = ? AND is_deleted = 0",
            (username,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]
        return None

async def get_username_by_refresh_token(refresh_token: str):
    async with aiosqlite.connect(DB_PATH_USERS) as db:
        cursor = await db.execute(
            "SELECT username FROM users WHERE refresh_token = ? AND is_deleted = 0",
            (refresh_token,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]
        return None

