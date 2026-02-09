from fastapi import APIRouter, HTTPException
from server.app.services.book_loader import get_all_books, parse_book_content

router = APIRouter()

@router.get("/list")
def list_books():
    """获取书架列表"""
    return {"status": "success", "data": get_all_books()}

@router.get("/content/{book_filename}")
def get_book(book_filename: str):
    """获取特定书籍的完整内容"""
    content = parse_book_content(book_filename)
    if not content:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"status": "success", "data": content}