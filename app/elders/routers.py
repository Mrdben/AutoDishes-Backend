from fastapi import APIRouter, HTTPException
from typing import List, Optional
from . import database
from .models import ElderDto, UpdateResponse, PullElderRequest, ElderListDto
from app.db_common import get_user_id_from_token

router = APIRouter()

@router.post("/push", response_model=UpdateResponse)
async def push_elder_to_server(token: str, request: ElderDto):
    user_id = await get_user_id_from_token(token)
    if user_id != request.user_id:
        raise HTTPException(status_code=409, detail="用户标识冲突")

    # get elder from user_id
    elder_data = request.model_dump()
    server_id = await database.get_server_id_by_user_and_elder_ids(user_id, request.elder_id) # no need to get whole structure
    if not server_id:  # user exists, but no elder
        # insert new elder record
        updated_data = await database.insert_elder(elder_data)
    else: # elder exists, check timestamp
        if server_id != request.server_id:
            raise HTTPException(status_code=409, detail="服务器同步错误: 家庭成员注册编号(server_id)冲突。")
        updated_time = await database.get_updated_time_by_server_id(server_id)
        if not updated_time:
            raise HTTPException(status_code=500, detail="服务器错误: 无法获取家庭成员更新时间。")
        if updated_time > request.updated_at: # timestamp conflict
            raise HTTPException(status_code=409, detail="服务器同步错误: 数据时间冲突")
        updated_data = await database.update_elder(elder_data)
    if not updated_data:
        raise HTTPException(status_code=500, detail=f"服务器错误: 服务器发生了莫名其妙的错误。")
        
    # 把新获得的时间戳返回给app
    return {"item_id" : updated_data["server_id"],
            "updated_at" : updated_data["updated_at"]}

@router.get("/pull", response_model=ElderDto)
async def get_elder_from_server(token: str, request: PullElderRequest) -> dict :
    user_id = await get_user_id_from_token(token)
    elder_data = await database.get_elder_by_server_id(request.server_id)
    if not elder_data:
        raise HTTPException(status_code=404, detail="没有找到该用户的elder数据")
    if elder_data['user_id'] != user_id:
        raise HTTPException(status_code=409, detail="用户标识冲突")
    return ElderDto.from_model(elder_data)

@router.get("/batch_pull", response_model=ElderListDto)
async def batch_pull_elder_from_server(token: str) -> ElderListDto:
    user_id = await get_user_id_from_token(token)
    elder_data = await database.pull_elders_by_user_id(user_id)
    result = []
    for elder in elder_data:
        elder = ElderDto.from_model(elder)
        result.append(elder)
    return ElderListDto(elder_list = result)

