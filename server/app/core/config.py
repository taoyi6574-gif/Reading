# server/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "NIRS Adaptive System"
    API_V1_STR: str = "/api/v1"

    # NIRS 数据源模式：sim(文件模拟) | hardware(真机：Matlab NDI)
    NIRS_MODE: str = "sim"

    # ---- 硬件/Matlab NDI 连接参数 ----
    # 说明：你的参考代码中使用 ip='0.0.0.0', port=5566，通常表示本机监听该端口等待设备连接。
    NDI_IP: str = "0.0.0.0"
    NDI_PORT: int = 5566
    NDI_PACKAGE_DIR: str = "NDI Package V1.3.2/NDI"

    # ---- 模拟数据文件路径（相对 server/ 目录）----
    NIRS_SIM_FILE: str = "data/通用_2024-08-13_20-15-18_00_qecs_男_1980-01-01_-2wavelength.snirf"

    # 模拟数据采样率 (Hz)
    SAMPLING_RATE: int = 10
    # 数据发送间隔 (秒)
    SEND_INTERVAL: float = 0.1

    class Config:
        case_sensitive = True


settings = Settings()