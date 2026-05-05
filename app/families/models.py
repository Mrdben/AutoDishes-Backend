from pydantic import BaseModel, Field
from typing import List

class FamilyDto(BaseModel):
    family_id: int
    user_id: int
    family_name: str
    elder_ids: List[str] = []

    is_deleted: bool = False
    updated_at: str
    created_at: str

class UpdateResponse(BaseModel) :
    item_id: int
    updated_at: str
