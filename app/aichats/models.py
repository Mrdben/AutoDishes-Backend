from pydantic import BaseModel

class AiChefRequest(BaseModel):
    elder_count: int
    meal_type: str
    elder_info: str
    order_hist: str
    selected_dishes: str
    user_prompt: str
    refresh_count: int
