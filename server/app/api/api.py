# server/app/api/api.py
from fastapi import APIRouter
from server.app.api.endpoints import stream, behavior,books
# from app.api.endpoints import auth, reading  <-- 暂时注释掉，因为还没创建这两个文件

api_router = APIRouter()

# 1. 注册 WebSocket 实时流 (NIRS 数据)
api_router.include_router(stream.router, prefix="/stream", tags=["stream"])

# 2. 注册行为采集接口 (Behavior 数据)
# 访问地址将变成: POST /api/v1/behavior/log
api_router.include_router(behavior.router, prefix="/behavior", tags=["behavior"])

# 3. 以后可以在这里继续注册 auth (登录) 或 reading (报告)
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(books.router, prefix="/books", tags=["books"])