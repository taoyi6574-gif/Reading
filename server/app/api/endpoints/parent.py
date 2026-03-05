# server/app/api/endpoints/parent.py
"""
家长端：关联/解绑儿童账号，获取已绑定儿童列表。
"""
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from server.app.db.base import get_db
from server.app.db import models

router = APIRouter()

SALT = "nirs_read_"


def _hash(password: str) -> str:
    return hashlib.sha256((SALT + password).encode("utf-8")).hexdigest()


def _verify(plain: str, hashed: str) -> bool:
    return _hash(plain) == hashed


class BindRequest(BaseModel):
    parent_username: str
    child_username: str
    child_password: str


class UnbindRequest(BaseModel):
    parent_username: str
    child_id: int


@router.get("/bound-children")
def list_bound_children(
    parent_username: str = Query(..., description="当前登录的家长账号"),
    db: Session = Depends(get_db),
):
    """获取该家长已绑定的儿童列表，用于家长端首页展示与切换。"""
    parent = db.query(models.User).filter(
        models.User.username == parent_username,
        models.User.role == "PARENT",
    ).first()
    if not parent:
        return {"status": "error", "message": "家长账号不存在", "data": []}
    bindings = db.query(models.ParentChildBinding).filter(
        models.ParentChildBinding.parent_id == parent.id
    ).all()
    children = []
    for b in bindings:
        child = db.query(models.User).filter(models.User.id == b.child_id).first()
        if child:
            subj = db.query(models.Subject).filter(models.Subject.id == child.subject_id).first() if child.subject_id else None
            children.append({
                "id": str(child.id),
                "account": child.username,
                "name": child.display_name or child.username,
                "subject_id": child.subject_id,
            })
    return {"status": "success", "data": children}


@router.post("/bind")
def bind_child(req: BindRequest, db: Session = Depends(get_db)):
    """
    家长输入儿童账号与密码，校验通过后建立绑定关系。
    若该儿童已在绑定列表中则返回成功（幂等）。
    """
    parent = db.query(models.User).filter(
        models.User.username == req.parent_username,
        models.User.role == "PARENT",
    ).first()
    if not parent:
        raise HTTPException(status_code=400, detail="家长账号不存在")
    child = db.query(models.User).filter(
        models.User.username == req.child_username,
        models.User.role == "CHILD",
    ).first()
    if not child:
        raise HTTPException(status_code=400, detail="儿童账号不存在")
    if not _verify(req.child_password, child.password_hash):
        raise HTTPException(status_code=400, detail="儿童密码错误")
    existing = db.query(models.ParentChildBinding).filter(
        models.ParentChildBinding.parent_id == parent.id,
        models.ParentChildBinding.child_id == child.id,
    ).first()
    if existing:
        return {"status": "success", "message": "已绑定过该儿童", "child_id": child.id}
    binding = models.ParentChildBinding(parent_id=parent.id, child_id=child.id)
    db.add(binding)
    db.commit()
    return {
        "status": "success",
        "message": "关联成功",
        "child_id": child.id,
        "child_account": child.username,
        "child_name": child.display_name or child.username,
    }


@router.post("/unbind")
def unbind_child(req: UnbindRequest, db: Session = Depends(get_db)):
    """解除家长与指定儿童的绑定关系（删除关联记录）。"""
    parent = db.query(models.User).filter(
        models.User.username == req.parent_username,
        models.User.role == "PARENT",
    ).first()
    if not parent:
        raise HTTPException(status_code=400, detail="家长账号不存在")
    binding = db.query(models.ParentChildBinding).filter(
        models.ParentChildBinding.parent_id == parent.id,
        models.ParentChildBinding.child_id == req.child_id,
    ).first()
    if not binding:
        raise HTTPException(status_code=404, detail="未绑定该儿童")
    db.delete(binding)
    db.commit()
    return {"status": "success", "message": "解绑成功"}
