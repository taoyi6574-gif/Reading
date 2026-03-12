"""
统一的 NIRS 数据源选择器。

- sim: 读取 snirf 文件模拟推流（nirs_simulator）
- hardware: 通过 Matlab NDI 工具包连接真机（nirs_hardware）

对外暴露的接口与 `NirsSyncSimulator` 保持一致：
- start_streaming(session_id, db_engine) -> async generator
- stop()
- is_running
"""

from server.app.core.config import settings


def _mode() -> str:
    return (settings.NIRS_MODE or "sim").strip().lower()


class _ManagerProxy:
    def __init__(self):
        self._impl = None

    def reset(self):
        """清空当前数据源缓存，使下一次访问按最新 NIRS_MODE 重新选择实现。"""
        self._impl = None

    @property
    def impl(self):
        if self._impl is not None:
            return self._impl

        mode = _mode()
        if mode == "hardware":
            try:
                from server.app.services.nirs_hardware import get_nirs_hardware_driver
                self._impl = get_nirs_hardware_driver()
                return self._impl
            except Exception as e:
                # 硬件模式初始化失败时回退到模拟，避免后端不可用
                print(f"⚠️ 硬件模式初始化失败，将回退到模拟模式。原因: {e}")

        from server.app.services.nirs_simulator import nirs_manager as sim_manager
        self._impl = sim_manager
        return self._impl

    @property
    def is_running(self) -> bool:
        return bool(getattr(self.impl, "is_running", False))

    async def start_streaming(self, session_id: int, db_engine):
        async for packet in self.impl.start_streaming(session_id, db_engine):
            yield packet

    def stop(self):
        if hasattr(self.impl, "stop"):
            return self.impl.stop()


# 全局单例：供 WebSocket / API 调用
nirs_manager = _ManagerProxy()

