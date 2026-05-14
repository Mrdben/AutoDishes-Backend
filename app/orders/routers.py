from fastapi import APIRouter, HTTPException
from typing import List, Optional
from . import database
from .models import OrderDto, OrderListDto, UpdateInfo, UpdateInfoList
from app.db_common import get_user_id_from_token

router = APIRouter()

@router.post("/push", response_model=UpdateInfoList)
async def push_order_to_server(token: str, request: OrderListDto):
# 从app更新服务器数据，做加法，看哪些可以更新，加到返回数据
    user_id = await get_user_id_from_token(token)
    update_info_list: list[UpdateInfo] = []
    for order_dto in request.order_list:
        order_model = order_dto.model_dump()
        # get order from user_id
        server_id = await database.get_server_id_by_user_and_order_ids(user_id, order_dto.order_id)
        if not server_id:  # user exists, but no order
            # insert new order record
            updated_data = await database.insert_order(user_id, order_model)
        else: # order exists, check timestamp
            updated_time = await database.get_updated_time_by_server_id(server_id)
            if not updated_time:
                raise HTTPException(status_code=500, detail=f"服务器错误: 无法获取家庭成员更新时间。 server_id = {server_id}")
            if order_dto.updated_at >= updated_time:
                updated_data = await database.update_order(server_id, order_model)
            else:
                updated_data = None
        if updated_data:
            update_info_list.append(UpdateInfo.from_model(updated_data)) # 把完成插入或更新的数据信息，加入返回列表

    return UpdateInfoList(info_list = update_info_list)

@router.post("/pull", response_model=OrderListDto)
async def get_order_from_server(token: str, request: UpdateInfoList) -> dict :
# 从服务器更新app数据，做减法，先获取后端数据库全量数据，再看哪些不用更新
    order_list_dto: list[OrderDto] = []
    info_map = build_info_map(request)
    user_id = await get_user_id_from_token(token)
    all_orders = await database.get_orders_by_user_id(user_id)
    for order in all_orders:
        app_updated_at = info_map.get(order['order_id'])
        if not app_updated_at:   # not included in request list
            if not order['is_deleted']:
                order_list_dto.append(OrderDto.from_model(order))
        elif app_updated_at < order['updated_at']:
            order_list_dto.append(OrderDto.from_model(order))

    return OrderListDto(order_list = order_list_dto)

def build_info_map(info_list: UpdateInfoList) -> dict[str, str]:
    return {info.order_id: info.updated_at for info in info_list.info_list}

