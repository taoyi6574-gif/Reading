import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from server.app.services.nirs_manager import nirs_manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket Connected")

    try:
        # 等待前端发送 "START" 指令
        # 格式: {"command": "START", "session_id": 123}
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)

            if data.get("command") == "START":
                session_id = data.get("session_id")
                print(f"收到开始指令，Session ID: {session_id}")

                # 开始推流循环
                async for packet in nirs_manager.start_streaming(session_id, None):
                    await websocket.send_text(json.dumps(packet))

                    # 检查是否收到停止指令 (这里简化处理，实际需异步监听)
                    # 在 FastApi WebSocket 中混合读写比较复杂，
                    # 这里的实现是：一旦开始，就一直推流直到连接断开或后端停止
                    if not nirs_manager.is_running:
                        break

            elif data.get("command") == "STOP":
                nirs_manager.stop()
                print("收到停止指令")
                break

    except WebSocketDisconnect:
        nirs_manager.stop()
        print("Client Disconnected")
    except Exception as e:
        print(f"WS Error: {e}")