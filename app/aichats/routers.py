import json
from fastapi import APIRouter, HTTPException
from typing import List, Set
from . import database
from .models import AiChefRequest
from .aliyun_qwen_api import aliyun_qwen_api
from app.dishes.models import DishDto, DishListDto, DishType, CuisineType
from app.db_common import get_user_id_from_token

router = APIRouter()
api_required_keys = {'chat_id','model_name','prompt_tokens','completion_tokens','total_tokens','created_at','response_time','user_prompt','model_response'}
dish_required_keys = {"name","taste","dish_type","cuisine","ingredients","recipe","comments"}

@router.post("/chat", response_model=DishListDto)
async def LLM_ai_chat(token: str, request: AiChefRequest):
# 从app更新服务器数据，做加法，看哪些可以更新，加到返回数据
    user_id = await get_user_id_from_token(token)
    try:
        previous_replies = "" if not request.refresh_count else await database.get_previous_replies(user_id, request.refresh_count)
        completion = aliyun_qwen_api(request.elder_count, 
                                     request.meal_type, 
                                     request.elder_info, 
                                     request.order_hist,
                                     request.selected_dishes,
                                     request.user_prompt,
                                     previous_replies)
        missing_keys = check_dict_keys(api_required_keys, completion)
        if missing_keys:
            raise Exception(f"模型返回的数据结构不完整，缺少必要的键: {missing_keys}")
        await database.insert_aichat(user_id, completion)
        model_dish_list = safe_converter(completion['model_response'])
        return DishListDto(dish_list = model_dish_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: 模型调用出错。 {e}")

    return

def check_dict_keys(required_keys: set[str], completion: dict[str, any]) -> set[str]:
    actual_keys = completion.keys()
    return required_keys - actual_keys

def safe_converter(suggest: str) -> list[DishDto] :
    try:
        sug_list = json.loads(suggest)
    except json.JSONDecodeError as e:
        raise Exception(f"服务器错误: JSON 解析模型返回的数据时失败了: {e}")

    if not isinstance(sug_list, list):
        raise Exception("服务器错误: 模型返回的数据结构不是列表")

    dish_list = []
    collect_missing_keys: set[str] = set()

    for sug in sug_list:
        # 确保 sug 是字典类型，防止传入非字典元素导致报错
        if not isinstance(sug, dict):
            continue
        missing_keys = check_dict_keys(dish_required_keys, sug)
        if missing_keys:
            collect_missing_keys |= missing_keys
            continue
        sug['dish_type'] = DishType(sug['dish_type']).name
        sug['cuisine'] = CuisineType(sug['cuisine']).name
        sug['dish_id'] = ""
        sug['favorite_level'] = 0
        sug['is_deleted'] = False
        sug['updated_at'] = ""
        sug['created_at'] = ""
        dish_list.append(DishDto.from_model(sug))
    if not dish_list:
        raise Exception(f"模型返回的菜品数据结构不完整，缺少必要的键: {collect_missing_keys}")
    return dish_list

