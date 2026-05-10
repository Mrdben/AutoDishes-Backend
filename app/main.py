import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .users.routers import router as users_router
from .elders.routers import router as elders_router

from .database import init_database
from dotenv import load_dotenv

load_dotenv()  # 无参数，自动从启动目录查找 .env，100%生效

# --------------- 创建 FastAPI 实例 ---------------
app = FastAPI(title="Android App Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------- 启动时初始化数据库 ---------------
@app.on_event("startup")
async def startup_event():
    await init_database()

# --------------- 挂载 auth 模块路由 ---------------
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(elders_router, prefix="/elders", tags=["elders"])

# --------------- 根接口（测试用）---------------
@app.get("/")
def home():
    return {"message": "Backend API is running"}

