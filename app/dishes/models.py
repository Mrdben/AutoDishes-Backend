from pydantic import BaseModel
from enum import Enum
from typing import List
import json

class DishDto(BaseModel):
    dish_id: str
    name: str
    taste: str
    dish_type: str
    cuisine: str
    ingredients: str
    recipe: str
    favorite_level: int
    comments: str
    is_deleted: bool = False
    updated_at: str
    created_at: str

    @staticmethod
    def from_model(model: dict):
        dish = DishDto(
            dish_id = model['dish_id'],
            name = model['name'],
            taste = model['taste'],
            dish_type = model['dish_type'],
            cuisine = model['cuisine'],
            ingredients = model['ingredients'],
            recipe = model['recipe'],
            favorite_level = model['favorite_level'],
            comments = model['comments'],
            is_deleted = bool(model['is_deleted']),
            updated_at = model['updated_at'],
            created_at = model['created_at']
        )
        return dish

class DishListDto(BaseModel):
    dish_list: list[DishDto]

class UpdateInfo(BaseModel):
    dish_id: str
    updated_at: str

    @staticmethod
    def from_model(model: dict):
        info = UpdateInfo(
            dish_id = model['dish_id'],
            updated_at = model['updated_at']
        )
        return info

class UpdateInfoList(BaseModel):
    info_list: list[UpdateInfo]

