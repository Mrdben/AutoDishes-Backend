import os
import secrets
from fastapi import APIRouter, HTTPException, Depends, status
from datetime import timedelta # 新增：时间处理

from . import database
from .aliyun_sms_verify import Aliyun_SMS_Verify
from .models import UserRegisterRequest, UserRegisterResponse
from .models import UserLoginRequest, UserLoginResponse
from .models import RefreshTokenRequest, RefreshTokenResponse
from .models import GetUserByTokenResponse, DeleteUserRequest
from .models import ChangePasswordRequest, UpdatePhoneNumberRequest
from .models import ResetPasswordRequest, UpdateFamilyNameRequest
from .models import ValidationSMSRequest, ValidationSMSResponse
from app.encryption import verify_password, create_token, get_username_by_access_token, password_hash

ACCESS_TOKEN_EXPIRE_MINUTES = 15 # Token 过期时间 (分钟)

# 初始化 FastAPI
router = APIRouter()

# --- 工具函数 ---
async def authenticate_user_by_password(username: str, password: str):
    # 这里直接调用我们在 database.py 里写好的函数
    # 注意：如果你的 database.py 里函数名叫 get_user，请改为 get_user
    user = await database.get_user_by_username_or_phone_number(username)

    if not user:
        return False
    if not verify_password(password, user["password_hash"]):
        return False
    return user

async def get_user_by_access_token(token: str):
    username, refresh, error_message = get_username_by_access_token(token)
    if (not username) or (not refresh):
        raise HTTPException(status_code=401, detail=error_message)
        
    refresh_username = await database.get_username_by_refresh_token(refresh)
    if (not refresh_username) or (refresh_username != username):
        raise HTTPException(status_code=401, detail="刷新令牌无效或已过期")

    # 从数据库查用户信息
    return await database.get_user_by_username_or_phone_number(username)

async def authenticate_user_by_password_token_phonenumber(token: str, password: str, phone_number: str):
    user = await get_user_by_access_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    # 3. 验证旧密码
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="密码错误")

    if phone_number != user["phone_number"]:
        raise HTTPException(status_code=400, detail="手机号错误")

    return user

# --- 接口 ---
@router.post("/register", response_model=UserRegisterResponse)
async def register(request: UserRegisterRequest) -> dict:
    existing_user = await database.get_user_by_username_or_phone_number(request.username)
    if existing_user:
        raise HTTPException(status_code=400, detail=f"用户名:{request.username} 已存在")

    await phone_number_verify(request.phone_number)

    sms_code_verify(request.phone_number, request.validation_code)

    phash = password_hash(request.password)
    await database.create_user(request.username, phash, request.phone_number, request.family_name)

    return {"message": "注册成功！", "username": request.username}

@router.post("/login", response_model=UserLoginResponse)
async def login_for_access_token(user_login: UserLoginRequest) -> dict:
    # 1. 验证用户
    user = await authenticate_user_by_password(user_login.username, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. 生成 Refresh Token (有效期长，比如 7 天)
    # 注意：Refresh Token 我们生成一个随机字符串，而不是 JWT，这样更安全
    refresh_token = secrets.token_urlsafe(32)

    # 3. 将 Refresh Token 存入数据库 (绑定到该用户)
    await database.write_refresh_token_to_user(user["username"], refresh_token)
    
    # 4. 生成 Access Token (有效期短，比如 15 分钟，方便测试你可以设短点)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_token(user["username"], refresh_token, expires_delta=access_token_expires)
    
    # 5. 返回两个 Token
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_access_token(request: RefreshTokenRequest) -> dict:
    # 1. 验证前端传来的 refresh_token 是否为空
    if not request.refresh_token:
        raise HTTPException(status_code=401, detail="缺少刷新令牌")

    username = await database.get_username_by_refresh_token(request.refresh_token)

    if not username:
        raise HTTPException(status_code=401, detail="刷新令牌无效或已过期")

    # 3. 如果有效，生成新的 Access Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_token(username, request.refresh_token, expires_delta=access_token_expires)

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=GetUserByTokenResponse)
async def get_current_user(token: str) -> dict:
    user = await get_user_by_access_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    return {"id": user["id"],
            "username": user["username"],
            "phone_number": user["phone_number"],
            "family_name": user["family_name"],
            "created_at": user["created_at"]}

# 修改密码接口
@router.post("/change-password")
async def change_password(token: str, request: ChangePasswordRequest):
    # 1. 验证 Token
    user = await authenticate_user_by_password_token_phonenumber(token, request.old_password, request.phone_number)
    sms_code_verify(request.phone_number, request.validation_code)
    # 4. 更新新密码
    new_hash = password_hash(request.new_password)
    await database.update_user_password(user["username"], new_hash)

    return {"message": "密码修改成功！"}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    user = await database.get_user_by_username_or_phone_number(request.username)

    if not user:
        raise HTTPException(status_code=401, detail="该用户不存在。")

    if user["phone_number"] != request.phone_number:
        raise HTTPException(status_code=400, detail="用户信息不符。")

    sms_code_verify(request.phone_number, request.validation_code)
    new_hash = password_hash(request.new_password)
    await database.update_user_password(request.username, new_hash)

    return {"message": "重置密码成功！"}

# 更新手机号
@router.post("/update-phone-number")
async def update_phone_number(token: str, request: UpdatePhoneNumberRequest):
    # 1. 验证 Token
    user = await authenticate_user_by_password_token_phonenumber(token, request.password, request.old_phone_number)

    # 2, 检查新号码是否已经被注册
    await phone_number_verify(request.new_phone_number)
    sms_code_verify(request.new_phone_number, request.validation_code)

    # 4. 更新手机号
    await database.update_user_phone_number(user["username"], request.new_phone_number)

    return {"message": "更新手机号成功！"}

@router.post("/update-family-name")
async def update_family_name(token: str, request: UpdateFamilyNameRequest):
    user = await get_user_by_access_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="该用户不存在。")
    await database.update_user_family_name(user["username"], request.family_name)
    return {"message","更改家庭名称成功！"}

# 注销账号接口
@router.post("/delete-account")
async def delete_account(token: str, request: DeleteUserRequest):
    # 1. 验证 Token, password, phonenumber
    user = await authenticate_user_by_password_token_phonenumber(token, request.password, request.phone_number)
    sms_code_verify(request.phone_number, request.validation_code)

    # 2. 删除用户
    await database.delete_user(user["username"])

    return {"message": "账号已注销"}

# 获取短信验证码
@router.post("/code-request", response_model=ValidationSMSResponse)
async def sms_code_request(request: ValidationSMSRequest) -> dict:
    if request.scene in {"register","phone"}:
        await phone_number_verify(request.phone_number)
    return Aliyun_SMS_Verify.send_request(request.phone_number, request.scene)

def sms_code_verify(phone_number: str, verify_code: str):
    result = Aliyun_SMS_Verify.verfiy_request(phone_number, verify_code)
    if not result["success"]:
        raise HTTPException(status_code=result["code"], detail=result["message"])

async def phone_number_verify(phone_number: str):
    existing_user = await database.get_username_by_phone_number(phone_number)
    if existing_user:
        raise HTTPException(status_code=400, detail=f"手机号:{phone_number} 已被注册")

