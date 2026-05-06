import aiosqlite
import os
from .db_common import DB_PATH_USERS, DB_PATH_FAMILIES, DB_PATH_ELDERS

from .users.database import create_users_table
from .families.database import create_families_table
from .elders.database import create_elders_table

async def init_database():
    async with aiosqlite.connect(DB_PATH_USERS) as db:
        await create_users_table(db)
        await db.commit()

    async with aiosqlite.connect(DB_PATH_FAMILIES) as db:
        await create_families_table(db)
        await db.commit()

    async with aiosqlite.connect(DB_PATH_ELDERS) as db:
        await create_elders_table(db)
        await db.commit()
