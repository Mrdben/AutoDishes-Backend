import os
from dotenv import load_dotenv
import aiosqlite
import secrets
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm # 新增：用于后续验证 Token

from passlib.context import CryptContext
from jose import jwt, JWTError  # 新增：JWT 相关
from datetime import datetime, timedelta # 新增：时间处理

from app.models import UserRegister, UserResponse, UserLogin, Token
from app.database import init_db, create_user, get_user_by_username, DB_PATH

from pydantic import BaseModel

load_dotenv()
# --- 配置常量 ---
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key") # 密钥，生产环境要改
ALGORITHM = "HS256" # 加密算法
ACCESS_TOKEN_EXPIRE_MINUTES = 15 # Token 过期时间 (分钟)

# 初始化 FastAPI
app = FastAPI(title="My App Backend")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 启动时初始化数据库
@app.on_event("startup")
async def startup_event():
    await init_db()

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

# --- 接口 ---

@app.get("/")
def read_root():
    return {"message": "后端服务运行中！"}

@app.post("/register")
async def register(user: UserRegister) -> dict:
    existing_user = await get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    password_hash = pwd_context.hash(user.password)
    await create_user(user.username, password_hash)
    
    return {"message": "注册成功！", "username": user.username}

async def get_user(username: str):
    import aiosqlite
    from app.database import DB_PATH # 导入数据库路径
    
    # 这个函数本身就是 async 的，所以可以直接使用 await
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        )
        row = await cursor.fetchone()
        return row

async def authenticate_user(username: str, password: str):
    # 这里直接调用我们在 database.py 里写好的函数
    # 注意：如果你的 database.py 里函数名叫 get_user，请改为 get_user
    user = await get_user(username) 
    
    if not user:
        return False
    if not verify_password(password, user["password_hash"]):
        return False
    return user

@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # 1. 验证用户
    user = await authenticate_user(form_data.username, form_data.password)
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
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET refresh_token = ? WHERE username = ?",
            (refresh_token, user["username"])
        )
        await db.commit()

    # 5. 返回两个 Token
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@app.post("/refresh")
async def refresh_access_token(request: RefreshTokenRequest):
    # 1. 验证前端传来的 refresh_token 是否为空
    if not request.refresh_token:
        raise HTTPException(status_code=401, detail="缺少刷新令牌")

    # 2. 去数据库查这个 refresh_token 是否存在且有效
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT username FROM users WHERE refresh_token = ?", 
            (request.refresh_token,)
        )
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="刷新令牌无效或已过期")

    username = row["username"]

    # 3. 如果有效，生成新的 Access Token
    access_token_expires = timedelta(minutes=15)
    new_access_token = create_token(data={"sub": username}, expires_delta=access_token_expires)

    # 4. (可选) 这里可以选择是否更新 Refresh Token
    # 为了安全，通常每次刷新后，我们会给一个新的 Refresh Token (轮换机制)
    # 这里为了简单，我们先只刷新 Access Token，Refresh Token 不变。

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }

@app.get("/users/me")
async def get_current_user(token: str):
    """
    获取当前登录用户信息
    需要携带有效的 access_token
    """
    try:
        # 解码 Token，验证是否合法
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token 无效")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 已过期或无效")
    
    # 从数据库查用户信息
    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"id": user["id"], "username": user["username"]}

# 新增：修改密码的请求模型
class ChangePassword(BaseModel):
    old_password: str
    new_password: str

# 新增：更新用户密码的数据库函数
async def update_user_password(username: str, new_password_hash: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (new_password_hash, username)
        )
        await db.commit()

# 新增：删除用户的数据库函数
async def delete_user(username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users WHERE username = ?", (username,))
        await db.commit()

# 修改密码接口
@app.post("/users/me/change-password")
async def change_password(token: str, password_data: ChangePassword):
    # 1. 验证 Token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token 无效")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 已过期或无效")

    # 2. 查询用户
    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 3. 验证旧密码
    if not verify_password(password_data.old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="旧密码错误")

    # 4. 更新新密码
    new_hash = pwd_context.hash(password_data.new_password)
    await update_user_password(username, new_hash)

    return {"message": "密码修改成功！"}

# 注销账号接口
@app.delete("/users/me")
async def delete_account(token: str):
    # 1. 验证 Token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token 无效")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 已过期或无效")

    # 2. 删除用户
    await delete_user(username)

    return {"message": "账号已注销"}
