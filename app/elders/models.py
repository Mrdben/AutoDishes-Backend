from pydantic import BaseModel
from enum import Enum
from typing import List
import json

class ElderDto(BaseModel):
    server_id: int
    elder_id: str
    user_id: int
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
            server_id = model['server_id'],
            elder_id = model['elder_id'],
            user_id = model['user_id'],
            name = model['name'],
            gender = model['gender'],
            age = model['age'],
            allergens = json.loads(model['allergens']),
            diseases = json.loads(model['diseases']),
            dietary_restriction = json.loads(model['dietary_restriction']),
            taste_preferences = json.loads(model['taste_preferences']),
            is_deleted = bool(model['is_deleted']),
            updated_at = model['updated_at'],
            created_at = model['updated_at']
        )
        return elder

class PullElderRequest(BaseModel):
    server_id: int
    
class UpdateResponse(BaseModel) :
    item_id: int
    updated_at: str

class ElderListDto(BaseModel):
    elder_list: list[ElderDto]
