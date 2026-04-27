from pydantic import BaseModel

# --- 已有的类 ---
class UserRegisterRequest(BaseModel):
    username: str
    password: str
    phonenumber: str
    
class UserRegisterResponse(BaseModel):
    message: str
    username: str
    
# --- 新增的类 ---
# 登录时 App 传来的数据
class UserLoginRequest(BaseModel):
    username: str
    password: str

# 登录成功后返回的 Token
class UserLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    
class RefreshTokenRequest(BaseModel):
    refresh_token: str
    
class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str

class GetUserByTokenResponse(BaseModel):
    id : int
    username : str
    phonenumber : str
    
class ChangePasswordRequest(BaseModel):
    old_password: str
    phonenumber: str
    new_password: str

class UpdatePhoneNumberRequest(BaseModel):
    password: str
    old_phonenumber: str
    new_phonenumber: str
    
class DeleteUserRequest(BaseModel):
    password: str
    phonenumber: str
