import os
import secrets
from fastapi import APIRouter, HTTPException, Depends, status

from passlib.context import CryptContext
from jose import jwt, JWTError  # 新增：JWT 相关
from datetime import datetime, timedelta # 新增：时间处理

from . import database
from .models import UserRegisterRequest, UserRegisterResponse
from .models import UserLoginRequest, UserLoginResponse
from .models import RefreshTokenRequest, RefreshTokenResponse
from .models import GetUserByTokenResponse, DeleteUserRequest
from .models import ChangePasswordRequest, UpdatePhoneNumberRequest
from .models import ResetPasswordRequest
from pydantic import BaseModel

# --- 配置常量 ---
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key") # 密钥，生产环境要改
ALGORITHM = "HS256" # 加密算法
ACCESS_TOKEN_EXPIRE_MINUTES = 15 # Token 过期时间 (分钟)

# 初始化 FastAPI
router = APIRouter()

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- 工具函数 ---
def verify_password(plain_password, hashed_password):
    """验证密码：比对明文密码和哈希值"""
    return pwd_context.verify(plain_password, hashed_password)

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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
    try:
        # 解码 Token，验证是否合法
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token 无效")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 已过期或无效")

    # 从数据库查用户信息
    return await database.get_user_by_username_or_phone_number(username)

async def authenticate_user_by_password_token_phonenumber(token: str, password: str, phone_number: str):
    user = await get_user_by_access_token(token)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

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

    existing_user = await database.get_username_by_phone_number(request.phone_number)
    if existing_user:
        raise HTTPException(status_code=400, detail=f"手机号:{request.phone_number} 已被注册")

    password_hash = pwd_context.hash(request.password)
    await database.create_user(request.username, password_hash, request.phone_number)

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

    # 2. 生成 Access Token (有效期短，比如 15 分钟，方便测试你可以设短点)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_token(data={"sub": user["username"]}, expires_delta=access_token_expires)

    # 3. 生成 Refresh Token (有效期长，比如 7 天)
    # 注意：Refresh Token 我们生成一个随机字符串，而不是 JWT，这样更安全
    refresh_token = secrets.token_urlsafe(32)

    # 4. 将 Refresh Token 存入数据库 (绑定到该用户)
    await database.write_refresh_token_to_user(user["username"], refresh_token)

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
    new_access_token = create_token(data={"sub": username}, expires_delta=access_token_expires)

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
            "created_at": user["created_at"]}

# 修改密码接口
@router.post("/change-password")
async def change_password(token: str, request: ChangePasswordRequest):
    # 1. 验证 Token
    user = await authenticate_user_by_password_token_phonenumber(token, request.old_password, request.phone_number)

    # 4. 更新新密码
    new_hash = pwd_context.hash(request.new_password)
    await database.update_user_password(user["username"], new_hash)

    return {"message": "密码修改成功！"}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    user = await database.get_user_by_username_or_phone_number(request.username)

    if not user:
        raise HTTPException(status_code=404, detail="该用户不存在。")

    if user["phone_number"] != request.phone_number:
        raise HTTPException(status_code=400, detail="用户信息不符。")

    new_hash = pwd_context.hash(request.new_password)
    await database.update_user_password(request.username, new_hash)

    return {"message": "重置密码成功！"}

# 更新手机号
@router.post("/update-phone-number")
async def update_phone_number(token: str, request: UpdatePhoneNumberRequest):
    # 1. 验证 Token
    user = await authenticate_user_by_password_token_phonenumber(token, request.password, request.old_phone_number)

    # 2, 检查新号码是否已经被注册
    existing_user = await database.get_username_by_phone_number(request.new_phone_number)
    if existing_user:
        raise HTTPException(status_code=400, detail=f"手机号:{request.new_phone_number} 已被注册")

    # 4. 更新手机号
    await database.update_user_phone_number(user["username"], request.new_phone_number)

    return {"message": "更新手机号成功！"}
    
# 注销账号接口
@router.post("/delete-account")
async def delete_account(token: str, request: DeleteUserRequest):
    # 1. 验证 Token, password, phonenumber
    user = await authenticate_user_by_password_token_phonenumber(token, request.password, request.phone_number)

    # 2. 删除用户
    await database.delete_user(user["username"])

    return {"message": "账号已注销"}

