import aiosqlite
import os
from .db_config import DB_PATH

from .users.database import create_users_table


# 全局初始化数据库（创建所有表）
async def init_database():
    async with aiosqlite.connect(DB_PATH) as db:
        # 导入并执行 auth 模块的表创建
        await create_users_table(db)

        # 未来其他模块的表在这里追加
        # from app.order.database import create_orders_table
        # await create_orders_table(db)

        await db.commit()
