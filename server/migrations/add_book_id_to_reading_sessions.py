"""
为 reading_sessions 表添加 book_id 列（若不存在）。
在项目根目录执行: python server/migrations/add_book_id_to_reading_sessions.py
"""
import sys
import os

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)

def run():
    from server.app.db.base import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT COUNT(1) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'reading_sessions'
              AND COLUMN_NAME = 'book_id'
        """))
        if r.scalar() > 0:
            print("Column book_id already exists. Skip.")
            return
        conn.execute(text("""
            ALTER TABLE reading_sessions
            ADD COLUMN book_id VARCHAR(120) NULL COMMENT '书籍ID，与书架列表 id 一致' AFTER book_title
        """))
        conn.execute(text("CREATE INDEX ix_reading_sessions_book_id ON reading_sessions (book_id)"))
        conn.commit()
    print("Added column book_id to reading_sessions.")

if __name__ == "__main__":
    run()
