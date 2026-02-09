# server/run.py
import uvicorn

if __name__ == "__main__":
    # reload=True 表示代码修改后自动重启，方便开发
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)