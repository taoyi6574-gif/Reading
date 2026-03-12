import time
import asyncio
import numpy as np
import mne
from datetime import datetime, timedelta
from server.app.db import models
from server.app.db.base import SessionLocal
from server.app.services.Rdata import MatlabN  # 导入你的通信模块
from server.app.core.config import settings

# 设置 MNE 日志级别
mne.set_log_level('WARNING')


class NirsHardwareDriver:
    def __init__(self):
        self.is_running = False
        self.current_session_id = None
        self.start_time = None

        # 注意：Matlab 引擎初始化很慢且可能在未安装时失败，
        # 因此改为延迟初始化（在 connect_device 时才创建）。
        self.rdata = None
        self._is_connected = False

        # 2. 配置 MNE 通道信息 (复用你提供的 channel names)
        # 730nm 和 850nm 的通道定义
        self.ch_names = [
            "S1_D1 730", "S1_D12 730", "S2_D2 730", "S2_D7 730", "S3_D2 730", "S3_D3 730", "S3_D8 730", "S4_D3 730",
            "S4_D4 730", "S4_D9 730",
            "S5_D4 730", "S5_D10 730", "S6_D5 730", "S6_D21 730", "S6_D22 730", "S7_D12 730", "S7_D19 730", "S8_D2 730",
            "S8_D7 730", "S8_D8 730",
            "S9_D3 730", "S9_D8 730", "S9_D9 730", "S10_D4 730", "S10_D9 730", "S10_D10 730", "S11_D21 730",
            "S11_D22 730", "S11_D23 730", "S12_D12 730",
            "S12_D14 730", "S12_D19 730", "S12_D20 730", "S13_D17 730", "S13_D20 730", "S14_D15 730", "S14_D18 730",
            "S14_D21 730", "S14_D23 730", "S15_D15 730",
            "S15_D18 730", "S16_D6 730", "S16_D13 730", "S17_D1 730", "S17_D12 730", "S17_D17 730", "S17_D20 730",
            "S18_D1 730", "S18_D17 730", "S19_D14 730",
            "S19_D20 730", "S20_D5 730", "S20_D11 730", "S20_D15 730", "S20_D21 730", "S21_D11 730", "S21_D15 730",
            "S22_D6 730", "S22_D13 730", "S23_D16 730",
            "S23_D24 730", "S24_D16 730", "S24_D24 730",
            "S1_D1 850", "S1_D12 850", "S2_D2 850", "S2_D7 850", "S3_D2 850", "S3_D3 850", "S3_D8 850", "S4_D3 850",
            "S4_D4 850", "S4_D9 850",
            "S5_D4 850", "S5_D10 850", "S6_D5 850", "S6_D21 850", "S6_D22 850", "S7_D12 850", "S7_D19 850", "S8_D2 850",
            "S8_D7 850", "S8_D8 850",
            "S9_D3 850", "S9_D8 850", "S9_D9 850", "S10_D4 850", "S10_D9 850", "S10_D10 850", "S11_D21 850",
            "S11_D22 850", "S11_D23 850", "S12_D12 850",
            "S12_D14 850", "S12_D19 850", "S12_D20 850", "S13_D17 850", "S13_D20 850", "S14_D15 850", "S14_D18 850",
            "S14_D21 850", "S14_D23 850", "S15_D15 850",
            "S15_D18 850", "S16_D6 850", "S16_D13 850", "S17_D1 850", "S17_D12 850", "S17_D17 850", "S17_D20 850",
            "S18_D1 850", "S18_D17 850", "S19_D14 850",
            "S19_D20 850", "S20_D5 850", "S20_D11 850", "S20_D15 850", "S20_D21 850", "S21_D11 850", "S21_D15 850",
            "S22_D6 850", "S22_D13 850", "S23_D16 850",
            "S23_D24 850", "S24_D16 850", "S24_D24 850"
        ]

        self.sfreq = 11.0
        self.rawinfo = mne.create_info(ch_names=self.ch_names, sfreq=self.sfreq, ch_types='fnirs_cw_amplitude')

        # 设置探头位置信息 (Loc)
        # 注意：这里我们只做数值转换，如果没有 monqecs.fif 文件，可以注释掉 set_montage
        for i in range(63):
            self.rawinfo['chs'][i]['loc'][9] = 730
        for i in range(63):
            self.rawinfo['chs'][i + 63]['loc'][9] = 850

        # 尝试加载 Montage，如果失败则跳过 (防止代码崩溃)
        try:
            self.mon = mne.channels.read_dig_fif('monqecs.fif')
            self.mon.rename_channels({k: v for k, v in zip(self.mon.ch_names, self.ch_names)})  # 需要映射逻辑，此处简化
        except:
            print("⚠️ 警告: 未找到 monqecs.fif，将跳过 3D 拓扑定位，仅计算数值。")
            self.mon = None

    async def connect_device(self):
        """异步连接设备"""
        if self.rdata is None:
            print("正在初始化 Matlab 引擎，请稍候...")
            # 可能抛异常：matlab engine 未安装 / NDI 目录不存在
            self.rdata = await asyncio.to_thread(MatlabN)
            print("Matlab 引擎初始化完成！")

        print(f"正在连接 NIRS 设备 (IP {settings.NDI_IP}, PORT {settings.NDI_PORT})...")
        # 由于 Matlab 调用是阻塞的，我们把它放到线程池里跑，防止卡死服务器
        res = await asyncio.to_thread(self.rdata.connect)
        self._is_connected = res == 1
        if self._is_connected:
            print("✅ 设备连接成功！")
        else:
            print("❌ 设备连接失败")
        return self._is_connected

    async def disconnect_device(self) -> bool:
        """断开设备连接。"""
        if self.rdata is None:
            self._is_connected = False
            return True
        try:
            await asyncio.to_thread(self.rdata.disconnect)
        except Exception:
            pass
        self._is_connected = False
        print("设备已断开连接")
        return True

    def get_device_status(self) -> dict:
        """返回设备连接状态。"""
        connected = False
        if self.rdata is not None:
            try:
                connected = self.rdata.is_connected()
            except Exception:
                pass
        self._is_connected = connected
        return {"connected": connected, "mode": "hardware"}

    async def start_streaming(self, session_id: int):
        """
        核心循环：
        1. 获取 Raw Data (Matlab)
        2. 转换为 HbO/HbR (MNE)
        3. 存入数据库
        4. 推送前端
        """
        # 1. 尝试连接 (如果还没连上)
        is_connected = await self.connect_device()
        if not is_connected:
            yield {"error": "Device Connection Failed"}
            return

        self.is_running = True
        self.current_session_id = session_id
        self.start_time = datetime.now()

        # 数据库写入缓冲
        db_buffer = []
        BATCH_SIZE = 20  # 每20帧写一次库

        # 左右前额叶通道索引 (根据你的代码 index 变量)
        # 注意：转换后的数据通道顺序可能会变，这里需要根据 MNE 的输出调整
        # 这里假设 Beer-Lambert 转换后，通道依然对应
        # 左侧: [9,10,11,12,24,25,26]
        # 右侧: [3,4,5,7,18,19,20]
        left_indices = [9, 10, 11, 12, 24, 25, 26]
        right_indices = [3, 4, 5, 7, 18, 19, 20]

        db = SessionLocal()

        print("▶️ 开始实时数据流...")

        try:
            while self.is_running:
                loop_start = time.time()

                # --- A. 从设备获取数据 (阻塞调用放到线程中) ---
                # rdata.getData() 返回的是一帧或多帧数据
                raw_frame = await asyncio.to_thread(self.rdata.getData)

                # 如果设备暂时没数据，休息一下继续
                if not raw_frame or len(raw_frame) == 0:
                    await asyncio.sleep(0.01)
                    continue

                # --- B. 数据处理 (MNE) ---
                # 1. 转置并处理格式 (参考你的 server.py)
                m = np.abs(np.array(raw_frame).T)

                # 你的代码里删除了后半部分? np.delete(m, np.s_[63:63 + 63], axis=0)
                # 这里我们假设 m 的形状符合 rawinfo (126 channels)
                # 如果不符合，需要在这里做 reshape

                # 2. 构建 MNE RawArray
                raw_intensity = mne.io.RawArray(m, self.rawinfo, verbose=False)

                # 3. 转换: 光强 -> 光密度 -> 血红蛋白
                raw_od = mne.preprocessing.nirs.optical_density(raw_intensity, verbose=False)
                raw_haemo = mne.preprocessing.nirs.beer_lambert_law(raw_od, ppf=0.1, verbose=False)

                # 4. 提取 HbO (通常 MNE 会输出 HbO 和 HbR，这里我们需要取数据)
                # get_data 返回 (Channels x Time)，这里 Time=1
                hbo_hbr_data = raw_haemo.get_data()

                # MNE 转换后，通道数会翻倍 (126 -> 252: 126 HbO + 126 HbR)
                # 通常 HbO 排在前面，或者交替排列。这里简化假设前一半是 HbO
                # 建议打印 raw_haemo.ch_names 来确认

                # 提取一帧数据的值
                current_data = hbo_hbr_data[:, -1]  # 取最新一个点

                # 计算 ROI (左右前额叶 HbO)
                # MNE 通道命名通常是 "S1_D1 730 hbo"
                # 我们简单取索引平均
                try:
                    val_left = np.mean(current_data[left_indices]) * 1e6  # uM
                    val_right = np.mean(current_data[right_indices]) * 1e6
                except:
                    val_left = 0
                    val_right = 0

                # --- C. 计算同步时间戳 ---
                # 使用 loop_start 确保时间连续性
                timestamp = datetime.now()

                # --- D. 存入数据库 ---
                db_record = {
                    "session_id": session_id,
                    "timestamp": timestamp,
                    "hbo_lpfc_raw": float(val_left),
                    "hbo_rpfc_raw": float(val_right)
                }
                db_buffer.append(db_record)

                if len(db_buffer) >= BATCH_SIZE:
                    db.bulk_insert_mappings(models.NirsRawData, db_buffer)
                    db.commit()
                    db_buffer = []

                # --- E. 推送前端 ---
                focus_state = "HIGH" if val_left > val_right else "LOW"
                packet = {
                    "timestamp": timestamp.timestamp(),
                    "raw_data": {"hbo": float(val_left), "hbr": float(val_right)},
                    "analysis": {"focus_level": focus_state}
                }
                yield packet

                # --- F. 控制采样率 ---
                # 设备采样率是 11Hz，大约 0.09s 一次
                # 如果 getData 本身是阻塞等待数据的，这里就不需要 sleep
                # 如果 getData 是立即返回的，需要 sleep
                # await asyncio.sleep(1/self.sfreq)

        except Exception as e:
            print(f"Hardware Streaming Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if db_buffer:
                db.bulk_insert_mappings(models.NirsRawData, db_buffer)
                db.commit()
            db.close()
            print("设备流结束")

    def stop(self):
        self.is_running = False


_nirs_driver_singleton = None


def get_nirs_hardware_driver() -> NirsHardwareDriver:
    """按需创建硬件驱动单例，避免 import 时启动 Matlab 引擎导致服务启动失败。"""
    global _nirs_driver_singleton
    if _nirs_driver_singleton is None:
        _nirs_driver_singleton = NirsHardwareDriver()
    return _nirs_driver_singleton