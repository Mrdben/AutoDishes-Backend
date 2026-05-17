import os
import datetime
import time
from openai import OpenAI
from .aimagic import magic_words1, magic_words2

ALIYUN_QWEN_BASE_URL = os.getenv("ALIYUN_QWEN_BASE_URL")
ALIYUN_QWEN_API_KEY = os.getenv("ALIYUN_QWEN_API_KEY")
ALIYUN_QWEN_MODEL = os.getenv("ALIYUN_QWEN_MODEL")

def aliyun_qwen_api(elder_count: int, meal_type: str, elder_info: str, order_hist: str):
    system_prompt = make_system_prompt()
    user_prompt = make_user_prompt(elder_count, meal_type, elder_info, order_hist)
    return aliyun_qwen_api_call(system_prompt, user_prompt)

def aliyun_qwen_api_call(system_prompt, user_prompt):
    # 初始化客户端
    client = OpenAI(
        # 从环境变量中读取 API Key（推荐）
        api_key = ALIYUN_QWEN_API_KEY,
        # 阿里云百炼的 OpenAI 兼容接口地址
        base_url = ALIYUN_QWEN_BASE_URL,
    )
    # 发起对话请求.
    start_time = time.perf_counter()
    completion = client.chat.completions.create(
        model = ALIYUN_QWEN_MODEL,  # 指定调用的模型，这里以 qwen-plus 为例
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        temperature = 0.1,
        response_format = {"type": "json_object"}
    )
    end_time = time.perf_counter()
    comp_dict = format_converter(completion)
    comp_dict['user_prompt'] = user_prompt
    comp_dict['response_time'] = int((end_time - start_time) * 1000)
    return comp_dict

def format_converter(completion) -> dict:
    dt_object = datetime.datetime.fromtimestamp(completion.created)
    return {
        'chat_id': completion.id,
        'model_name': completion.model,
        'prompt_tokens': completion.usage.prompt_tokens,
        'completion_tokens': completion.usage.completion_tokens,
        'total_tokens': completion.usage.total_tokens,
        'created_at': dt_object.strftime('%Y-%m-%d %H:%M:%S'),
        'model_response': completion.choices[0].message.content
    }

def make_user_prompt(elder_count: int, meal_type: str, elder_info: str, order_hist: str):
    user_prompt = f"""
    请为以下{elder_count}位用餐者推荐合适份量的[{meal_type}]，包括主食。
    {magic_words2}
    【用餐者信息】
    {elder_info}
    【饮食历史】
    {order_hist}
    """
    return user_prompt

def make_system_prompt():
    system_prompt = magic_words1 + \
    """
    【输出格式要求】
    你必须严格且仅输出一个合法的 JSON 对象，不要包含任何 ```json代码块标记或额外的解释性文字。
    JSON 必须是一个数组，包含以下结构的菜品对象：
    [{
        "name": "字符串，必填，推荐的菜品名称",
        "taste": "字符串，必填，菜品的口味描述",
        "dish_type": "字符串，必填，菜品的类型",
        "cuisine": "字符串，必填，菜品的菜系",
        "ingredients": "字符串，必填，包含所有主要原料",
        "recipe": "字符串，必填，包含可操作的烹饪步骤，每两个步骤之间加入换行符"，
        "comments": "字符串，必填，推荐理由"
    }]
    【字段取值约束】
    - type 必须严格在以下选项中选择：[冷荤, 冷素, 热荤, 热素, 汤, 主食, 零食]
    - cuisine 必须严格在以下选项中选择：[鲁菜, 川菜, 粤菜, 湘菜, 徽菜, 京菜, 沪菜, 东北菜, 家常菜]
    【输出示例】
    [{
        "name": "清蒸鲈鱼",
        "taste": "咸鲜清淡",
        "type": "热荤",
        "cuisine": "粤菜",
        "ingredients": "鲈鱼、葱姜、蒸鱼豉油",
        "recipe": "1.鲈鱼处理干净打花刀；\n2.葱姜铺底水开上锅蒸8分钟；\n3.淋上蒸鱼豉油即可",
        "comments": "清蒸鱼有营养，易消化，鲈鱼刺少，用餐者没有对鱼类过敏史。"
    }]
    """
    return system_prompt
