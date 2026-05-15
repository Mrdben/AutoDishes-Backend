from pydantic import BaseModel
from enum import Enum
from typing import List
import json

class OrderDto(BaseModel):
    order_id: str
    meal_type: str
    meal_time: str
    elder_ids: list[str]
    dish_ids: list[str]
    is_deleted: bool = False
    updated_at: str
    created_at: str

    @staticmethod
    def from_model(model: dict):
        order = OrderDto(
            order_id = model['order_id'],
            meal_type = model['meal_type'],
            meal_time = model['meal_time'],
            elder_ids = json.loads(model['elder_ids']),
            dish_ids = json.loads(model['dish_ids']),
            is_deleted = bool(model['is_deleted']),
            updated_at = model['updated_at'],
            created_at = model['created_at']
        )
        return order

class OrderListDto(BaseModel):
    order_list: list[OrderDto]

class UpdateInfo(BaseModel):
    order_id: str
    updated_at: str

    @staticmethod
    def from_model(model: dict):
        info = UpdateInfo(
            order_id = model['order_id'],
            updated_at = model['updated_at']
        )
        return info

class UpdateInfoList(BaseModel):
    info_list: list[UpdateInfo]

