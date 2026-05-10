from pydantic import BaseModel

# --- 已有的类 ---
class UserRegisterRequest(BaseModel):
    username: str
    password: str
    phone_number: str
    family_name: str
    
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
    phone_number : str
    created_at : str
    family_name: str
    
class ChangePasswordRequest(BaseModel):
    old_password: str
    phone_number: str
    new_password: str

class ResetPasswordRequest(BaseModel):
    username: str
    phone_number: str
    new_password: str

class UpdatePhoneNumberRequest(BaseModel):
    password: str
    old_phone_number: str
    new_phone_number: str

class UpdateFamilyNameRequest(BaseModel):
    family_name: str

class DeleteUserRequest(BaseModel):
    password: str
    phone_number: str
