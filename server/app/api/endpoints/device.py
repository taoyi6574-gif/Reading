"""
设备连接管理：connect / disconnect / status
用于前端「设备连接页」的按钮调用。
- POST /device/connect   -> 连接设备
- POST /device/disconnect -> 断开设备
- GET  /device/status    -> 查询连接状态
"""

from fastapi import APIRouter

from server.app.core.config import settings

router = APIRouter()


def _mode() -> str:
    return (settings.NIRS_MODE or "sim").strip().lower()


def _get_hardware_driver():
    """获取硬件驱动单例，仅 hardware 模式有效。"""
    from server.app.services.nirs_hardware import get_nirs_hardware_driver
    return get_nirs_hardware_driver()


@router.post("/mode")
async def device_set_mode(body: dict):
    """
    运行时切换数据源模式。
    body: {"mode": "sim" | "hardware"}
    """
    mode = str(body.get("mode", "")).strip().lower()
    if mode not in ("sim", "hardware"):
        return {"ok": False, "message": "mode 只支持 sim 或 hardware"}

    # 若从 hardware 切到 sim，先尝试断开设备（不中断也没关系）
    if mode == "sim":
        try:
            driver = _get_hardware_driver()
            await driver.disconnect_device()
        except Exception:
            pass

    settings.NIRS_MODE = mode

    # 让推流选择器按最新模式重选实现
    try:
        from server.app.services.nirs_manager import nirs_manager
        nirs_manager.reset()
    except Exception:
        pass

    return {"ok": True, "mode": mode, "message": f"已切换到 {mode} 模式"}


@router.post("/connect")
async def device_connect():
    """
    连接 NIRS 设备。
    - hardware 模式：初始化 Matlab Engine，调用 ndiConnect 与设备建立连接。
    - sim 模式：无需连接，直接返回 ready。
    """
    mode = _mode()
    if mode == "sim":
        return {
            "ok": True,
            "mode": "sim",
            "connected": True,
            "message": "模拟模式，无需连接物理设备，可直接开始采集。",
        }

    try:
        driver = _get_hardware_driver()
        connected = await driver.connect_device()
        return {
            "ok": connected,
            "mode": "hardware",
            "connected": connected,
            "message": "设备连接成功" if connected else "设备连接失败，请检查设备与端口配置。",
        }
    except Exception as e:
        return {
            "ok": False,
            "mode": "hardware",
            "connected": False,
            "message": f"连接异常: {str(e)}",
        }


@router.post("/disconnect")
async def device_disconnect():
    """
    断开 NIRS 设备连接。
    - hardware 模式：调用 ndiDisconnect 断开与设备的连接。
    - sim 模式：无实际操作。
    """
    mode = _mode()
    if mode == "sim":
        return {
            "ok": True,
            "mode": "sim",
            "message": "模拟模式，无设备连接需断开。",
        }

    try:
        driver = _get_hardware_driver()
        await driver.disconnect_device()
        return {
            "ok": True,
            "mode": "hardware",
            "message": "设备已断开连接。",
        }
    except Exception as e:
        return {
            "ok": False,
            "mode": "hardware",
            "message": f"断开异常: {str(e)}",
        }


@router.get("/status")
async def device_status():
    """
    查询设备连接状态。
    - mode: sim | hardware
    - connected: 是否已连接（sim 模式下为 true，表示可采集）
    """
    mode = _mode()
    if mode == "sim":
        return {
            "mode": "sim",
            "connected": True,
            "message": "模拟模式，可随时开始采集。",
        }

    try:
        driver = _get_hardware_driver()
        status = driver.get_device_status()
        return {
            "mode": status.get("mode", "hardware"),
            "connected": status.get("connected", False),
            "message": "设备已连接" if status.get("connected") else "设备未连接。",
        }
    except Exception as e:
        return {
            "mode": "hardware",
            "connected": False,
            "message": f"查询异常: {str(e)}",
        }
