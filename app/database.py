import aiosqlite
import os
from .db_common import DB_PATH_USERS, DB_PATH_ELDERS, DB_PATH_DISHES, DB_PATH_ORDERS, DB_PATH_AICHATS

from .users.database import create_users_table
from .elders.database import create_elders_table
from .dishes.database import create_dishes_table
from .orders.database import create_orders_table
from .aichats.database import create_aichats_table

async def init_database():
    async with aiosqlite.connect(DB_PATH_USERS) as db:
        await create_users_table(db)
        await db.commit()

    async with aiosqlite.connect(DB_PATH_ELDERS) as db:
        await create_elders_table(db)
        await db.commit()

    async with aiosqlite.connect(DB_PATH_DISHES) as db:
        await create_dishes_table(db)
        await db.commit()

    async with aiosqlite.connect(DB_PATH_ORDERS) as db:
        await create_orders_table(db)
        await db.commit()

    async with aiosqlite.connect(DB_PATH_AICHATS) as db:
        await create_aichats_table(db)
        await db.commit()
