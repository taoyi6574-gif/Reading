# server/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "NIRS Adaptive System"
    API_V1_STR: str = "/api/v1"

    # 模拟数据采样率 (Hz)
    SAMPLING_RATE: int = 10
    # 数据发送间隔 (秒)
    SEND_INTERVAL: float = 0.1

    class Config:
        case_sensitive = True


settings = Settings()