import os
import mne
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.base import SessionLocal, engine
from app.db import models

# 1. 确保数据库表已创建
models.Base.metadata.create_all(bind=engine)


def parse_filename(filename):
    """
    解析文件名元数据
    格式示例: 通用_2024-08-13_20-15-18_00_qecs_男_1980-01-01_-2wavelength.snirf
    """
    parts = filename.split('_')
    try:
        # 根据你的文件名结构定位信息
        date_str = parts[1]  # 2024-08-13
        time_str = parts[2].replace('-', ':')  # 20-15-18 -> 20:15:18
        subject_code = parts[4]  # qecs
        gender = parts[5]  # 男
        dob_str = parts[6]  # 1980-01-01

        start_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        dob = datetime.strptime(dob_str, "%Y-%m-%d")

        # 计算年龄
        age = (start_time - dob).days // 365

        return {
            "code": subject_code,
            "gender": gender,
            "age": age,
            "start_time": start_time
        }
    except Exception as e:
        print(f"文件名解析失败 ({filename}): {e}")
        return None


def process_and_import(file_path):
    print(f"🚀 开始处理文件: {os.path.basename(file_path)}")

    db: Session = SessionLocal()

    try:
        # --- 1. 处理被试信息 (Subject) ---
        filename = os.path.basename(file_path)
        meta = parse_filename(filename)

        if not meta:
            print("❌ 跳过：元数据解析失败")
            return

        # 查找或创建被试
        subject = db.query(models.Subject).filter_by(subject_code=meta['code']).first()
        if not subject:
            subject = models.Subject(
                subject_code=meta['code'],
                age=meta['age'],
                gender=meta['gender']
            )
            db.add(subject)
            db.commit()
            db.refresh(subject)
            print(f"✅ 创建新被试: {subject.subject_code} (Age: {subject.age})")
        else:
            print(f"ℹ️ 被试已存在: {subject.subject_code}")

        # --- 2. 创建阅读会话 (ReadingSession) ---
        session = models.ReadingSession(
            subject_id=subject.id,
            book_title=filename,
            book_id=filename,  # 与 reading_sessions.book_id 一致
            start_time=meta['start_time']
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        print(f"✅ 创建新会话 Session ID: {session.id}")

        # --- 3. MNE 数据处理 (核心算法) ---
        print("⏳ 正在读取 SNIRF 文件并转换血氧浓度...")
        raw = mne.io.read_raw_snirf(file_path, preload=True, verbose=False)

        # 光密度 -> 血红蛋白浓度
        raw_od = mne.preprocessing.nirs.optical_density(raw)
        raw_haemo = mne.preprocessing.nirs.beer_lambert_law(raw_od, ppf=0.1)

        # 获取数据 (转置为 Time x Channels)
        data_matrix = raw_haemo.get_data().T
        times = raw_haemo.times  # 相对时间数组 [0.0, 0.1, 0.2 ...]

        # ROI 通道索引 (基于你提供的代码)
        left_indices = [9, 10, 11, 12, 24, 25, 26]
        right_indices = [3, 4, 5, 7, 18, 19, 20]

        # --- 4. 批量存入数据库 (NirsRawData) ---
        objects = []
        batch_size = 2000  # 每次提交2000条，提高速度

        # 预先检查维度，防止索引越界
        n_channels = data_matrix.shape[1]

        print(f"⏳ 正在入库 {len(times)} 帧数据 (这可能需要几秒钟)...")

        for i, relative_time in enumerate(times):
            frame = data_matrix[i]

            # 计算 ROI 均值 (左/右前额叶)
            # 简单处理：仅当通道数足够时计算，否则填0
            try:
                # 假设前一半是 HbO (MNE 转换后的通常顺序)
                hbo_frame = frame[:n_channels // 2]

                # 再次检查索引是否在范围内
                val_left = np.mean(hbo_frame[left_indices]) if max(left_indices) < len(hbo_frame) else 0
                val_right = np.mean(hbo_frame[right_indices]) if max(right_indices) < len(hbo_frame) else 0
            except:
                val_left = 0
                val_right = 0

            # 计算绝对时间戳 (Start Time + Relative Time)
            # 对应文档：同步时间戳
            current_timestamp = meta['start_time'] + timedelta(seconds=float(relative_time))

            record = models.NirsRawData(
                session_id=session.id,
                timestamp=current_timestamp,
                hbo_lpfc_raw=float(val_left),
                hbo_rpfc_raw=float(val_right),
                # 预处理字段留空，或在这里直接填入如果已经做过滤波
                hbo_lpfc_filtered=None,
                hbo_rpfc_filtered=None
            )
            objects.append(record)

            # 批量写入
            if len(objects) >= batch_size:
                db.bulk_save_objects(objects)
                db.commit()
                objects = []

        # 处理剩余尾部数据
        if objects:
            db.bulk_save_objects(objects)
            db.commit()

        # 更新会话结束时间
        session.end_time = meta['start_time'] + timedelta(seconds=float(times[-1]))
        db.commit()

        print(f"🎉 文件处理完成！共导入 {len(times)} 条 NIRS 数据。")

    except Exception as e:
        print(f"❌ 处理过程中出错: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # 请修改这里的路径为你实际的文件路径
    snirf_file_path = r"D:\ProgramData\Reading\server\data\通用_2024-08-13_20-15-18_00_qecs_男_1980-01-01_-2wavelength.snirf"

    if os.path.exists(snirf_file_path):
        process_and_import(snirf_file_path)
    else:
        print(f"未找到文件: {snirf_file_path}")
        print("请确保你在 server 目录下创建了 data 文件夹并将 snirf 文件放入。")