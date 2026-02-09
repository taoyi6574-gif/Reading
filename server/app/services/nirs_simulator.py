import mne
import time
import asyncio
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from server.app.db import models
from server.app.db.base import SessionLocal

#我们需要一个新的服务文件，专门负责读取文件并模拟设备流。

# 这一步是为了防止 MNE 输出太多日志
mne.set_log_level('WARNING')


class NirsSyncSimulator:
    def __init__(self):
        self.is_running = False
        self.current_session_id = None
        self.start_time = None
        self.raw_data = None
        self.sfreq = 10.0  # 默认采样率
        self._generator = None

        # 预加载文件 (这里替换为你实际的 .nirs 或 .snirf 文件路径)
        # 建议放在 server/data/ 目录下
        self.file_path = "data/通用_2024-08-13_20-15-18_00_qecs_男_1980-01-01_-2wavelength.snirf"
        self.load_data()

    def load_data(self):
        """加载文件并转换为血氧浓度"""
        try:
            print(f"正在加载 NIRS 模拟数据: {self.file_path} ...")
            # 使用 MNE 读取
            raw = mne.io.read_raw_snirf(self.file_path, preload=True)

            # 光密度 -> 血红蛋白浓度
            raw_od = mne.preprocessing.nirs.optical_density(raw)
            raw_haemo = mne.preprocessing.nirs.beer_lambert_law(raw_od, ppf=0.1)

            self.sfreq = raw_haemo.info['sfreq']
            # 转置为 (Time, Channels)
            self.data_matrix = raw_haemo.get_data().T
            self.times = raw_haemo.times
            print(f"数据加载完毕，时长: {self.times[-1]:.1f}s, 采样率: {self.sfreq}Hz")

        except Exception as e:
            print(f"加载 NIRS 文件失败: {e}。将使用随机数据回退模式。")
            self.data_matrix = None

    async def start_streaming(self, session_id: int, db_engine):
        """
        核心方法：开启同步流
        同时做两件事：
        1. Yield 数据给 WebSocket (前端显示)
        2. 批量写入 Database (数据存储)
        """
        self.is_running = True
        self.current_session_id = session_id
        self.start_time = datetime.now()  # === 关键：确立时间零点 ===

        # 定义左右前额叶通道索引 (根据你的设备定义)
        # 假设：前一半是 HbO
        left_indices = [9, 10, 11, 12, 24, 25, 26]
        right_indices = [3, 4, 5, 7, 18, 19, 20]

        row_idx = 0
        total_rows = len(self.data_matrix) if self.data_matrix is not None else 100000

        # 数据库批处理缓冲
        db_buffer = []
        batch_size = 50  # 每50条(约5秒)写一次库，避免IO太频繁

        # 创建独立的数据库会话用于写入
        db = SessionLocal()

        try:
            while self.is_running:
                loop_start = time.time()

                # 1. 获取当前帧数据
                if self.data_matrix is not None:
                    # 循环播放文件
                    current_idx = row_idx % total_rows
                    frame = self.data_matrix[current_idx]

                    # 简单计算 ROI (实际算法可在此优化)
                    n_ch = len(frame) // 2
                    val_left = np.mean(frame[:n_ch][left_indices]) * 1e6  # 转为 uM 单位方便看
                    val_right = np.mean(frame[:n_ch][right_indices]) * 1e6
                else:
                    # 失败时的随机数据
                    val_left = np.random.rand()
                    val_right = np.random.rand()

                # 2. 计算精准的同步时间戳
                # 不依赖系统当前时间，而是依赖 "开始时间 + 偏移量"
                # 这样即使代码卡顿，时间戳也是均匀连续的
                timestamp = self.start_time + timedelta(seconds=row_idx / self.sfreq)

                # 3. 准备数据包 (给前端)
                # 简单模拟专注度算法
                focus_level = "HIGH" if val_left > val_right else "LOW"

                packet = {
                    "timestamp": timestamp.timestamp(),
                    "raw_data": {"hbo": float(val_left), "hbr": float(val_right)},
                    "analysis": {"focus_level": focus_level}
                }

                # 4. 存入数据库缓冲 (给后端存储)
                db_record = {
                    "session_id": session_id,
                    "timestamp": timestamp,
                    "hbo_lpfc_raw": float(val_left),
                    "hbo_rpfc_raw": float(val_right)
                }
                db_buffer.append(db_record)

                # 5. 批量写入数据库
                if len(db_buffer) >= batch_size:
                    db.bulk_insert_mappings(models.NirsRawData, db_buffer)
                    db.commit()
                    db_buffer = []

                # 6. 发送给 WebSocket
                yield packet

                # 7. 严格控制频率 (Sleep)
                row_idx += 1
                elapsed = time.time() - loop_start
                wait_time = (1.0 / self.sfreq) - elapsed
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

        except Exception as e:
            print(f"Streaming Error: {e}")
        finally:
            # 收尾：把剩下的数据存进去
            if db_buffer:
                db.bulk_insert_mappings(models.NirsRawData, db_buffer)
                db.commit()
            db.close()
            print("Session Stream Ended")

    def stop(self):
        self.is_running = False


# 全局单例
nirs_manager = NirsSyncSimulator()