from fastapi import APIRouter, HTTPException
from typing import List, Optional
from . import database
from .models import ElderDto, ElderListDto, UpdateInfo, UpdateInfoList
from app.db_common import get_user_id_from_token

router = APIRouter()

@router.post("/push", response_model=UpdateInfoList)
async def push_elder_to_server(token: str, request: ElderListDto):
# 从app更新服务器数据，做加法，看哪些可以更新，加到返回数据
    user_id = await get_user_id_from_token(token)
    update_info_list: list[UpdateInfo] = []
    for elder_dto in request.elder_list:
        elder_model = elder_dto.model_dump()
        # get elder from user_id
        server_id = await database.get_server_id_by_user_and_elder_ids(user_id, elder_dto.elder_id) 
        if not server_id:  # user exists, but no elder
            # insert new elder record
            updated_data = await database.insert_elder(user_id, elder_model)
        else: # elder exists, check timestamp
            updated_time = await database.get_updated_time_by_server_id(server_id)
            if not updated_time:
                raise HTTPException(status_code=500, detail=f"服务器错误: 无法获取家庭成员更新时间。 server_id = {server_id}")
            if elder_dto.updated_at >= updated_time:
                updated_data = await database.update_elder(server_id, elder_model)
            else:
                updated_data = None
        if updated_data:
            update_info_list.append(UpdateInfo.from_model(updated_data)) # 把完成插入或更新的数据信息，加入返回列表

    return UpdateInfoList(info_list = update_info_list)

@router.post("/pull", response_model=ElderListDto)
async def get_elder_from_server(token: str, request: UpdateInfoList) -> dict :
# 从服务器更新app数据，做减法，先获取后端数据库全量数据，再看哪些不用更新
    elder_list_dto: list[ElderDto] = []
    info_map = build_info_map(request)
    user_id = await get_user_id_from_token(token)
    all_elders = await database.get_elders_by_user_id(user_id)
    for elder in all_elders:
        app_updated_at = info_map.get(elder['elder_id'])
        if not app_updated_at:   # not included in request list
            if not elder['is_deleted']:
                elder_list_dto.append(ElderDto.from_model(elder))
        elif app_updated_at < elder['updated_at']:
            elder_list_dto.append(ElderDto.from_model(elder))

    return ElderListDto(elder_list = elder_list_dto)

def build_info_map(info_list: UpdateInfoList) -> dict[str, str]:
    return {info.elder_id: info.updated_at for info in info_list.info_list}
