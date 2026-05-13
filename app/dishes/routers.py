from fastapi import APIRouter, HTTPException
from typing import List, Optional
from . import database
from .models import DishDto, DishListDto, UpdateInfo, UpdateInfoList
from app.db_common import get_user_id_from_token

router = APIRouter()

@router.post("/push", response_model=UpdateInfoList)
async def push_dish_to_server(token: str, request: DishListDto):
# 从app更新服务器数据，做加法，看哪些可以更新，加到返回数据
    user_id = await get_user_id_from_token(token)
    update_info_list: list[UpdateInfo] = []
    for dish_dto in request.dish_list:
        dish_model = dish_dto.model_dump()
        # get dish from user_id
        server_id = await database.get_server_id_by_user_and_dish_ids(user_id, dish_dto.dish_id)
        if not server_id:  # user exists, but no dish
            # insert new dish record
            updated_data = await database.insert_dish(user_id, dish_model)
        else: # dish exists, check timestamp
            updated_time = await database.get_updated_time_by_server_id(server_id)
            if not updated_time:
                raise HTTPException(status_code=500, detail=f"服务器错误: 无法获取家庭成员更新时间。 server_id = {server_id}")
            if dish_dto.updated_at >= updated_time:
                updated_data = await database.update_dish(server_id, dish_model)
            else:
                updated_data = None
        if updated_data:
            update_info_list.append(UpdateInfo.from_model(updated_data)) # 把完成插入或更新的数据信息，加入返回列表

    return UpdateInfoList(info_list = update_info_list)

@router.post("/pull", response_model=DishListDto)
async def get_dish_from_server(token: str, request: UpdateInfoList) -> dict :
# 从服务器更新app数据，做减法，先获取后端数据库全量数据，再看哪些不用更新
    dish_list_dto: list[DishDto] = []
    info_map = build_info_map(request)
    user_id = await get_user_id_from_token(token)
    all_dishes = await database.get_dishes_by_user_id(user_id)
    for dish in all_dishes:
        app_updated_at = info_map.get(dish['dish_id'])
        if not app_updated_at:   # not included in request list
            if not dish['is_deleted']:
                dish_list_dto.append(DishDto.from_model(dish))
        elif app_updated_at < dish['updated_at']:
            dish_list_dto.append(DishDto.from_model(dish))

    return DishListDto(dish_list = dish_list_dto)

def build_info_map(info_list: UpdateInfoList) -> dict[str, str]:
    return {info.dish_id: info.updated_at for info in info_list.info_list}

