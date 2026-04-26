from pydantic import BaseModel

# --- 已有的类 ---
class UserRegister(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

# --- 新增的类 ---
# 登录时 App 传来的数据
class UserLogin(BaseModel):
    username: str
    password: str

# 登录成功后返回的 Token
class Token(BaseModel):
    access_token: str
    token_type: str
