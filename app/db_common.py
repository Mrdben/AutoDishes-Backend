import os
import aiosqlite
from .encryption import get_username_by_access_token
from fastapi import HTTPException

DB_PATH_USERS = os.path.join(os.path.dirname(__file__), "users.db")
DB_PATH_ELDERS = os.path.join(os.path.dirname(__file__), "elders.db")
DB_PATH_DISHES = os.path.join(os.path.dirname(__file__), "dishes.db")
DB_PATH_ORDERS = os.path.join(os.path.dirname(__file__), "orders.db")

def get_user_id_from_token(token):
    # 1, get username from token
    username, error_message = get_username_by_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail=error_message)
    # 2, check user info
    user_id = get_user_id_by_username(username)
    if not user_id:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user_id

async def get_user_id_by_username(username: str):
    async with aiosqlite.connect(DB_PATH_USERS) as db:
        cursor = await db.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]
        return None
