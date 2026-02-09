# server/app/services/nirs_driver.py
import math
import time
import random
import asyncio
from typing import Dict, Any


class NIRSDriver:
    def __init__(self):
        self.is_running = False
        self._tick = 0.0

    async def get_stream_data(self) -> Dict[str, Any]:
        """
        生成单帧数据包，模拟 NIRS 设备读取
        """
        self._tick += 0.1

        # 1. 模拟生理信号 (HbO 和 HbR 通常呈负相关)
        # 叠加正弦波模拟心跳(1.2Hz)和呼吸(0.3Hz)
        base_hbo = (math.sin(self._tick) * 0.5 +
                    math.sin(self._tick * 5) * 0.1 +
                    random.uniform(-0.02, 0.02))

        base_hbr = (math.cos(self._tick) * 0.5 +
                    math.cos(self._tick * 5) * 0.1 +
                    random.uniform(-0.02, 0.02)) * -1  # 反向

        # 2. 模拟专注度算法逻辑 (Mock ML Model)
        # 每 15 秒切换一次状态，方便你演示前端变化
        cycle = int(time.time()) % 30
        if cycle < 10:
            focus = "NORMAL"
            action = "KEEP"
        elif cycle < 20:
            focus = "LOW"
            action = "ENHANCE_UI"  # 指示前端放大字体
        else:
            focus = "HIGH"
            action = "SIMPLIFY_UI"

        return {
            "timestamp": time.time(),
            "raw_data": {
                "hbo": round(base_hbo, 4),
                "hbr": round(base_hbr, 4)
            },
            "analysis": {
                "focus_level": focus,
                "cognitive_load": round(random.random(), 2),
                "adaptive_action": action
            }
        }


# 创建全局单例，供不同 API 调用
nirs_service = NIRSDriver()