from passlib.context import CryptContext
from jose import jwt, JWTError, ExpiredSignatureError  # 新增：JWT 相关
from datetime import datetime, timedelta # 新增：时间处理
import os

# --- 配置常量 ---
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key") # 密钥，生产环境要改
ALGORITHM = "HS256" # 加密算法
USER_KEY = "sub"

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """验证密码：比对明文密码和哈希值"""
    return pwd_context.verify(plain_password, hashed_password)
    
def create_token(username : str, expires_delta: timedelta):
    to_encode = {USER_KEY : username}
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
    
def get_username_by_access_token(token: str):
    username = None
    error_message = ""
    try:
        # 解码 Token，验证是否合法
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get(USER_KEY)
        if username is None:
            error_message = "Token 无效"
    except ExpiredSignatureError:
        error_message = "Token 已过期"
    except JWTError:
        error_message = "Token 无效或签名错误"
    return username, error_message

def password_hash(password: str):
    return pwd_context.hash(password)
