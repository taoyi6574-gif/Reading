# server/app/api/endpoints/behavior.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# 导入数据库连接和模型
from server.app.db.base import get_db
from server.app.db import models

router = APIRouter()


# --- 1. 定义数据接收格式 (Schema) ---
class EventRequest(BaseModel):
    session_id: int
    event_type: str  # 例如: "PAGE_TURN", "CLICK", "PAUSE"
    event_value: str  # 例如: "Page 5 -> Page 6", "Button: Start"
    timestamp: Optional[datetime] = None  # 允许前端传时间，不传则用服务器时间


# --- 2. 定义 API 接口 ---
@router.post("/log")
def log_behavior_event(event: EventRequest, db: Session = Depends(get_db)):
    """
    接收前端行为数据的接口
    对应文档：阅读行为数据采集模块 -> 记录翻页频率等行为指标
    """

    # 1. 检查 Session 是否存在 (可选，保证数据完整性)
    session = db.query(models.ReadingSession).filter(models.ReadingSession.id == event.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Reading Session not found")

    # 2. 写入数据库
    # 如果前端没传时间戳，就用现在的服务器时间
    event_time = event.timestamp if event.timestamp else datetime.now()

    new_event = models.BehaviorEvent(
        session_id=event.session_id,
        event_type=event.event_type,
        event_value=event.event_value,
        timestamp=event_time
    )

    try:
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        return {"status": "success", "event_id": new_event.id, "msg": "行为已记录"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/history/{session_id}")
def get_session_events(session_id: int, db: Session = Depends(get_db)):
    """
    (可选) 获取某个会话的所有行为历史，方便调试或回放
    """
    events = db.query(models.BehaviorEvent) \
        .filter(models.BehaviorEvent.session_id == session_id) \
        .order_by(models.BehaviorEvent.timestamp) \
        .all()
    return events


class SessionCreate(BaseModel):
    subject_id: int
    book_title: str


@router.post("/start_session")
def start_new_session(data: SessionCreate, db: Session = Depends(get_db)):
    """
    前端点击“开始阅读”时调用，创建一个新的 Session
    """
    # 1. 创建会话记录
    new_session = models.ReadingSession(
        subject_id=data.subject_id,  # 这里暂时由前端传，实际可改为固定值或登录用户
        book_title=data.book_title,
        start_time=datetime.now()
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return {"status": "success", "session_id": new_session.id}


@router.post("/end_session/{session_id}")
def end_current_session(session_id: int, db: Session = Depends(get_db)):
    """
    前端点击“结束阅读”时调用
    """
    session = db.query(models.ReadingSession).filter(models.ReadingSession.id == session_id).first()
    if session:
        session.end_time = datetime.now()
        db.commit()
        return {"status": "success", "msg": "阅读结束"}
    return {"status": "error", "msg": "会话不存在"}