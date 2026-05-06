from fastapi import APIRouter, HTTPException
from typing import List, Optional

from . import database
from .models import FamilyDto, UpdateResponse
from app.db_common import get_user_id_from_token

router = APIRouter()

@router.post("/push", response_model=UpdateResponse)
async def push_family_to_server(token: str, request: FamilyDto):
    user_id = await get_user_id_from_token(token)
    if user_id != request.user_id:
        raise HTTPException(status_code=409, detail="用户标识冲突")
    
    # get family from user_id
    family_data = request.model_dump() 
    updated_time = await database.get_update_time_by_user_id(user_id) # no need to get whole structure
    if not updated_time:  # user exists, but no family
        # insert new family record
        updated_data = await database.insert_family(family_data)
    else: # family exists, check timestamp
        if updated_time > request.updated_at: # timestamp conflict
            raise HTTPException(status_code=409, detail="服务器同步错误: 数据时间冲突")
        updated_data = await database.update_family(family_data)
    if not updated_data:
        raise HTTPException(status_code=500, detail="服务器错误: 服务器发生了莫名其妙的错误。")        
    # 把新获得的时间戳返回给app
    return {"item_id" : updated_data["family_id"],
            "updated_at" : updated_data["updated_at"]}

@router.get("/pull", response_model=FamilyDto)
async def get_family_from_server(token: str) -> dict :
    user_id = await get_user_id_from_token(token)
    family_data = await database.get_family_by_user_id(user_id)
    if not family_data:
        raise HTTPException(status_code=404, detail="没有找到该用户的family数据")

    return family_data
