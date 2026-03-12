# server/app/api/endpoints/admin.py
"""
管理员端：用户管理（账号与关联关系）、阅读记录数据管理（增删改查）。
"""
import hashlib
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from server.app.db.base import get_db
from server.app.db import models

router = APIRouter()
SALT = "nirs_read_"


def _hash(password: str) -> str:
    return hashlib.sha256((SALT + password).encode("utf-8")).hexdigest()


# ---------- 被试列表（供筛选与创建阅读记录） ----------
@router.get("/subjects")
def admin_list_subjects(db: Session = Depends(get_db)):
    """列出所有被试（儿童），用于数据管理筛选与新增阅读记录。"""
    subs = db.query(models.Subject).order_by(models.Subject.id).all()
    out = [{"id": s.id, "subject_code": s.subject_code, "age": s.age, "gender": s.gender} for s in subs]
    return {"status": "success", "data": out}


# ---------- 用户管理 ----------
class UserCreate(BaseModel):
    username: str
    password: str
    role: str  # CHILD | PARENT | ADMIN
    display_name: Optional[str] = None
    subject_id: Optional[int] = None  # 仅儿童需关联被试


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    password: Optional[str] = None


@router.get("/users")
def admin_list_users(
    role: Optional[str] = Query(None, description="CHILD | PARENT | ADMIN"),
    db: Session = Depends(get_db),
):
    """列出用户，可按角色筛选。"""
    q = db.query(models.User)
    if role:
        q = q.filter(models.User.role == role)
    users = q.order_by(models.User.id).all()
    out = []
    for u in users:
        subj = db.query(models.Subject).filter(models.Subject.id == u.subject_id).first() if u.subject_id else None
        out.append({
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "display_name": u.display_name,
            "subject_id": u.subject_id,
            "subject_code": subj.subject_code if subj else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })
    return {"status": "success", "data": out}


@router.post("/users")
def admin_create_user(body: UserCreate, db: Session = Depends(get_db)):
    """创建用户（儿童/家长/管理员）。儿童可指定 subject_id，不指定则自动创建新 Subject。"""
    if db.query(models.User).filter(models.User.username == body.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    subject_id = body.subject_id
    if body.role == "CHILD" and subject_id is None:
        subj = models.Subject(subject_code="", age=0, gender=None)
        db.add(subj)
        db.flush()
        subj.subject_code = f"S{subj.id}"
        subject_id = subj.id
    user = models.User(
        username=body.username,
        password_hash=_hash(body.password),
        role=body.role,
        display_name=body.display_name or body.username,
        subject_id=subject_id if body.role == "CHILD" else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"status": "success", "data": {"id": user.id, "username": user.username, "role": user.role, "subject_id": user.subject_id}}


@router.put("/users/{user_id}")
def admin_update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db)):
    """更新用户显示名或密码。"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if body.display_name is not None:
        user.display_name = body.display_name
    if body.password is not None and body.password.strip():
        user.password_hash = _hash(body.password)
    db.commit()
    db.refresh(user)
    return {"status": "success", "data": {"id": user.id, "username": user.username}}


@router.delete("/users/{user_id}")
def admin_delete_user(user_id: int, db: Session = Depends(get_db)):
    """删除用户；会同时删除其作为家长或儿童的绑定关系。"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.query(models.ParentChildBinding).filter(
        (models.ParentChildBinding.parent_id == user_id) | (models.ParentChildBinding.child_id == user_id)
    ).delete(synchronize_session=False)
    db.delete(user)
    db.commit()
    return {"status": "success", "message": "已删除"}


# ---------- 关联关系 ----------
class BindingCreate(BaseModel):
    parent_id: int
    child_id: int


@router.get("/bindings")
def admin_list_bindings(db: Session = Depends(get_db)):
    """列出所有家长-儿童绑定。"""
    bindings = db.query(models.ParentChildBinding).order_by(models.ParentChildBinding.id).all()
    out = []
    for b in bindings:
        parent = db.query(models.User).filter(models.User.id == b.parent_id).first()
        child = db.query(models.User).filter(models.User.id == b.child_id).first()
        out.append({
            "id": b.id,
            "parent_id": b.parent_id,
            "child_id": b.child_id,
            "parent_username": parent.username if parent else None,
            "parent_name": parent.display_name if parent else None,
            "child_username": child.username if child else None,
            "child_name": child.display_name if child else None,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        })
    return {"status": "success", "data": out}


@router.post("/bindings")
def admin_create_binding(body: BindingCreate, db: Session = Depends(get_db)):
    """添加一条家长-儿童绑定。"""
    parent = db.query(models.User).filter(models.User.id == body.parent_id, models.User.role == "PARENT").first()
    child = db.query(models.User).filter(models.User.id == body.child_id, models.User.role == "CHILD").first()
    if not parent:
        raise HTTPException(status_code=400, detail="家长 ID 不存在或不是家长账号")
    if not child:
        raise HTTPException(status_code=400, detail="儿童 ID 不存在或不是儿童账号")
    if db.query(models.ParentChildBinding).filter(
        models.ParentChildBinding.parent_id == body.parent_id,
        models.ParentChildBinding.child_id == body.child_id,
    ).first():
        raise HTTPException(status_code=400, detail="该绑定已存在")
    b = models.ParentChildBinding(parent_id=body.parent_id, child_id=body.child_id)
    db.add(b)
    db.commit()
    db.refresh(b)
    return {"status": "success", "data": {"id": b.id, "parent_id": b.parent_id, "child_id": b.child_id}}


@router.delete("/bindings/{binding_id}")
def admin_delete_binding(binding_id: int, db: Session = Depends(get_db)):
    """删除一条绑定。"""
    b = db.query(models.ParentChildBinding).filter(models.ParentChildBinding.id == binding_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="绑定不存在")
    db.delete(b)
    db.commit()
    return {"status": "success", "message": "已解绑"}


# ---------- 阅读记录（数据管理） ----------
class ReadingSessionCreate(BaseModel):
    subject_id: int
    book_title: str
    book_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    avg_focus_score: Optional[float] = 0.0
    intervention_count: Optional[int] = 0


class ReadingSessionUpdate(BaseModel):
    book_title: Optional[str] = None
    book_id: Optional[str] = None
    end_time: Optional[datetime] = None
    avg_focus_score: Optional[float] = None
    intervention_count: Optional[int] = None


@router.get("/reading-sessions")
def admin_list_reading_sessions(
    subject_id: Optional[int] = Query(None, description="按被试/儿童筛选"),
    book_title: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """管理员查看所有孩子的阅读记录，支持按儿童、书名、日期筛选。"""
    q = db.query(models.ReadingSession)
    if subject_id is not None:
        q = q.filter(models.ReadingSession.subject_id == subject_id)
    if book_title:
        q = q.filter(models.ReadingSession.book_title.contains(book_title))
    if start_date:
        try:
            t = datetime.strptime(start_date, "%Y-%m-%d")
            q = q.filter(models.ReadingSession.start_time >= t)
        except ValueError:
            pass
    if end_date:
        try:
            t = datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            q = q.filter(models.ReadingSession.start_time <= t)
        except ValueError:
            pass
    total = q.count()
    sessions = q.order_by(desc(models.ReadingSession.start_time)).offset(offset).limit(limit).all()
    out = []
    for s in sessions:
        subj = db.query(models.Subject).filter(models.Subject.id == s.subject_id).first()
        user = db.query(models.User).filter(models.User.subject_id == s.subject_id, models.User.role == "CHILD").first()
        out.append({
            "id": s.id,
            "subject_id": s.subject_id,
            "subject_code": subj.subject_code if subj else None,
            "child_display_name": user.display_name if user else None,
            "child_username": user.username if user else None,
            "book_title": s.book_title,
            "book_id": s.book_id,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "avg_focus_score": s.avg_focus_score,
            "intervention_count": s.intervention_count,
        })
    return {"status": "success", "data": out, "total": total}


@router.get("/reading-sessions/{session_id}")
def admin_get_reading_session(session_id: int, db: Session = Depends(get_db)):
    """单条阅读记录详情。"""
    s = db.query(models.ReadingSession).filter(models.ReadingSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="阅读记录不存在")
    subj = db.query(models.Subject).filter(models.Subject.id == s.subject_id).first()
    user = db.query(models.User).filter(models.User.subject_id == s.subject_id, models.User.role == "CHILD").first()
    return {
        "status": "success",
        "data": {
            "id": s.id,
            "subject_id": s.subject_id,
            "subject_code": subj.subject_code if subj else None,
            "child_display_name": user.display_name if user else None,
            "child_username": user.username if user else None,
            "book_title": s.book_title,
            "book_id": s.book_id,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "avg_focus_score": s.avg_focus_score,
            "intervention_count": s.intervention_count,
        },
    }


@router.post("/reading-sessions")
def admin_create_reading_session(body: ReadingSessionCreate, db: Session = Depends(get_db)):
    """新增一条阅读记录。"""
    subj = db.query(models.Subject).filter(models.Subject.id == body.subject_id).first()
    if not subj:
        raise HTTPException(status_code=400, detail="被试不存在")
    book_id = body.book_id or f"{body.book_title}.txt"
    s = models.ReadingSession(
        subject_id=body.subject_id,
        book_title=body.book_title,
        book_id=book_id,
        start_time=body.start_time or datetime.now(),
        end_time=body.end_time,
        avg_focus_score=body.avg_focus_score or 0.0,
        intervention_count=body.intervention_count or 0,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"status": "success", "data": {"id": s.id, "subject_id": s.subject_id, "book_title": s.book_title}}


@router.put("/reading-sessions/{session_id}")
def admin_update_reading_session(session_id: int, body: ReadingSessionUpdate, db: Session = Depends(get_db)):
    """更新阅读记录。"""
    s = db.query(models.ReadingSession).filter(models.ReadingSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="阅读记录不存在")
    if body.book_title is not None:
        s.book_title = body.book_title
    if body.book_id is not None:
        s.book_id = body.book_id
    if body.end_time is not None:
        s.end_time = body.end_time
    if body.avg_focus_score is not None:
        s.avg_focus_score = body.avg_focus_score
    if body.intervention_count is not None:
        s.intervention_count = body.intervention_count
    db.commit()
    db.refresh(s)
    return {"status": "success", "data": {"id": s.id}}


@router.delete("/reading-sessions/{session_id}")
def admin_delete_reading_session(session_id: int, db: Session = Depends(get_db)):
    """删除阅读记录及其关联的行为事件、NIRS 数据、评估日志。"""
    s = db.query(models.ReadingSession).filter(models.ReadingSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="阅读记录不存在")
    db.query(models.BehaviorEvent).filter(models.BehaviorEvent.session_id == session_id).delete(synchronize_session=False)
    db.query(models.NirsRawData).filter(models.NirsRawData.session_id == session_id).delete(synchronize_session=False)
    db.query(models.EvaluationLog).filter(models.EvaluationLog.session_id == session_id).delete(synchronize_session=False)
    db.delete(s)
    db.commit()
    return {"status": "success", "message": "已删除"}
