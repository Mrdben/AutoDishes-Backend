from fastapi import APIRouter, HTTPException
from typing import List, Optional

from . import database
from .models import FamilyDto, UpdatedTime
from app.encryption import get_username_by_access_token
from app.db_common import get_user_id_from_token

router = APIRouter()

@router.post("/push", response_model=UpdatedTime)
async def push_family_to_server(token: str, request: FamilyDto):
    user_id = await get_user_id_from_token(token)
    family_data = request.model_dump()
    # get family from user_id
    updated_time = await database.get_update_time_by_id(user_id) # no need to get whole structure
    if not updated_time:  # user exists, but no family
        # insert new family record
        new_updated_time = await database.insert_family(user_id, family_data)
    else: # family exists, check timestamp
        if updated_time > request.updated_at: # timestamp conflict
            raise HTTPException(status_code=409, detail=f"服务器同步错误: 数据时间冲突")
        new_updated_time = await database.update_family(user_id, family_data)
        
    # 把新获得的时间戳返回给app
    return {"updated_at" : new_updated_time}

@router.get("/pull", response_model=FamilyDto)
async def get_family_from_server(token: str) -> dict :
    user_id = await get_user_id_from_token(token)
    family_data = await database.get_family_by_id(user_id)
    if not family:
        raise HTTPException(status_code=404, detail="没有找到该用户的family数据")

    return family_data
