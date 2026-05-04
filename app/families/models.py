from pydantic import BaseModel, Field
from typing import List, Optional

class FamilyDto(BaseModel):
    family_id: int
    family_name: str
    elder_ids: List[str] = []

    server_id: Optional[str] = None
    is_deleted: bool = False
    updated_at: str
    created_at: str

class UpdatedTime(BaseModel) :
    updated_at: str
