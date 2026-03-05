"""
独立执行以创建数据库表（首次部署或迁移时使用）。
在项目根目录执行: python server/init_db.py  或  cd server && python init_db.py
"""
import sys
import os

# 支持从项目根或 server 目录运行
if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)

from server.app.db.base import engine
from server.app.db import models

if __name__ == "__main__":
    models.Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
