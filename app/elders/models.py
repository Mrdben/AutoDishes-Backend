from pydantic import BaseModel
from enum import Enum
from typing import List
import json

class ElderDto(BaseModel):
    elder_id: str
    name: str
    gender: str
    age: int
    allergens: List[str] = []
    diseases: List[str] = []
    dietary_restriction: List[str] = []
    taste_preferences: List[str] = []
    is_deleted: bool = False
    updated_at: str
    created_at: str

    @staticmethod
    def from_model(model: dict):
        elder = ElderDto(
            elder_id = model['elder_id'],
            name = model['name'],
            gender = model['gender'],
            age = model['age'],
            allergens = json.loads(model['allergens']),
            diseases = json.loads(model['diseases']),
            dietary_restriction = json.loads(model['dietary_restriction']),
            taste_preferences = json.loads(model['taste_preferences']),
            is_deleted = bool(model['is_deleted']),
            updated_at = model['updated_at'],
            created_at = model['created_at']
        )
        return elder

class ElderListDto(BaseModel):
    elder_list: list[ElderDto]

class UpdateInfo(BaseModel):
    elder_id: str
    updated_at: str

    @staticmethod
    def from_model(model: dict):
        info = UpdateInfo(
            elder_id = model['elder_id'],
            updated_at = model['updated_at']
        )
        return info

class UpdateInfoList(BaseModel):
    info_list: list[UpdateInfo]
