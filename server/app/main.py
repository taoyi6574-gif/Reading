# server/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api import api_router
from server.app.db.base import engine
from server.app.db import models

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 配置跨域 (CORS)，允许前端 Vue 访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册所有路由
app.include_router(api_router, prefix=settings.API_V1_STR)


def _seed_password(password: str) -> str:
    import hashlib
    return hashlib.sha256(("nirs_read_" + password).encode("utf-8")).hexdigest()


@app.on_event("startup")
def on_startup():
    """启动时创建表结构、补齐缺失列、默认被试、示例用户与家长-儿童绑定"""
    from sqlalchemy import text
    from server.app.db.base import SessionLocal

    models.Base.metadata.create_all(bind=engine)

    # 若 reading_sessions 已存在但缺少 book_id 列，则添加（兼容旧库）
    try:
        with engine.begin() as conn:
            r = conn.execute(text("""
                SELECT COUNT(1) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'reading_sessions' AND COLUMN_NAME = 'book_id'
            """))
            if r.scalar() == 0:
                conn.execute(text("""
                    ALTER TABLE reading_sessions
                    ADD COLUMN book_id VARCHAR(120) NULL COMMENT '书籍ID，与书架列表 id 一致' AFTER book_title
                """))
                conn.execute(text("CREATE INDEX ix_reading_sessions_book_id ON reading_sessions (book_id)"))
    except Exception:
        pass

    db = SessionLocal()
    try:
        if db.query(models.Subject).first() is None:
            subject = models.Subject(subject_code="S001", age=6, gender="男")
            db.add(subject)
            db.commit()

        # 示例用户：儿童、家长、管理员（密码均为 123456）
        pw = _seed_password("123456")
        subject_one = db.query(models.Subject).filter(models.Subject.id == 1).first()
        if subject_one and not db.query(models.User).filter(models.User.username == "child").first():
            u_child = models.User(
                username="child",
                password_hash=pw,
                role="CHILD",
                subject_id=1,
                display_name="小明",
            )
            db.add(u_child)
        if not db.query(models.User).filter(models.User.username == "parent").first():
            db.add(models.User(username="parent", password_hash=pw, role="PARENT", display_name="家长"))
        if not db.query(models.User).filter(models.User.username == "admin").first():
            db.add(models.User(username="admin", password_hash=pw, role="ADMIN", display_name="管理员"))
        db.commit()

        # 示例绑定：家长 parent 已绑定儿童 child
        parent_user = db.query(models.User).filter(models.User.username == "parent", models.User.role == "PARENT").first()
        child_user = db.query(models.User).filter(models.User.username == "child", models.User.role == "CHILD").first()
        if parent_user and child_user and not db.query(models.ParentChildBinding).filter(
            models.ParentChildBinding.parent_id == parent_user.id,
            models.ParentChildBinding.child_id == child_user.id,
        ).first():
            db.add(models.ParentChildBinding(parent_id=parent_user.id, child_id=child_user.id))
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "NIRS System Backend is Running"}