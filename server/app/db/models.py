# server/app/db/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from server.app.db.base import Base


class Subject(Base):
    """
    【隐私安全层】被试/儿童信息表
    对应文档：确保数据的隐私安全
    设计策略：不存储儿童真实姓名，仅使用 subject_code (如 'S001') 进行脱敏管理。
    """
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    subject_code = Column(String(50), unique=True, index=True, comment="被试编号，如 S001")
    age = Column(Integer, comment="年龄，用于适配不同认知水平的基准线")
    gender = Column(String(10), nullable=True, comment="性别")
    created_at = Column(DateTime, default=datetime.now)

    # 关联该儿童所有的阅读记录
    sessions = relationship("ReadingSession", back_populates="subject")


class User(Base):
    """
    用户表：儿童账号、家长账号、管理员账号统一存储。
    role: CHILD / PARENT / ADMIN。
    儿童账号的 subject_id 关联 subjects 表，用于阅读数据（reading_sessions 等）。
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False, comment="登录账号")
    password_hash = Column(String(128), nullable=False, comment="密码哈希")
    role = Column(String(20), nullable=False, index=True, comment="CHILD / PARENT / ADMIN")
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True, comment="仅儿童账号：关联被试/阅读数据")
    display_name = Column(String(64), nullable=True, comment="显示名，如 小明、家长")
    created_at = Column(DateTime, default=datetime.now)

    subject = relationship("Subject", backref="user", uselist=False)
    bound_children = relationship(
        "ParentChildBinding",
        foreign_keys="ParentChildBinding.parent_id",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    bound_by_parents = relationship(
        "ParentChildBinding",
        foreign_keys="ParentChildBinding.child_id",
        back_populates="child",
        cascade="all, delete-orphan",
    )


class ParentChildBinding(Base):
    """
    家长-儿童关联表：记录哪位家长绑定了哪位儿童，绑定后可查看该儿童阅读数据。
    """
    __tablename__ = "parent_child_bindings"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (UniqueConstraint("parent_id", "child_id", name="uq_parent_child"),)

    parent = relationship("User", foreign_keys=[parent_id], back_populates="bound_children")
    child = relationship("User", foreign_keys=[child_id], back_populates="bound_by_parents")


class ReadingSession(Base):
    """
    【流程控制层】阅读会话表
    对应文档：生成阅读报告，记录阅读时长
    作用：将一次完整的阅读过程（从打开书到结束）作为一个 Session。
    """
    __tablename__ = "reading_sessions"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    book_title = Column(String(100), comment="阅读书目")
    book_id = Column(String(120), nullable=True, index=True, comment="书籍ID，与书架列表 id 一致，如 小王子.txt，用于阅读历史")

    start_time = Column(DateTime, default=datetime.now, comment="开始时间")
    end_time = Column(DateTime, nullable=True, comment="结束时间")

    # --- 结果指标 (用于生成最终报告) ---
    avg_focus_score = Column(Float, default=0.0, comment="本次阅读平均专注度")
    intervention_count = Column(Integer, default=0, comment="触发自适应干预的总次数")

    # 关联关系
    subject = relationship("Subject", back_populates="sessions")
    nirs_data = relationship("NirsRawData", back_populates="session")
    behavior_events = relationship("BehaviorEvent", back_populates="session")
    evaluation_logs = relationship("EvaluationLog", back_populates="session")


class NirsRawData(Base):
    """
    【NIRS采集模块】生理信号数据表
    对应文档：实时采集血氧浓度，使用滤波算法去除干扰
    特点：高频存储 (如 10Hz)，建议配合批量插入策略使用。
    """
    __tablename__ = "nirs_raw_data"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("reading_sessions.id"))
    timestamp = Column(DateTime, index=True, comment="同步时间戳")

    # --- 原始采集数据 (Raw) ---
    # 根据你的代码逻辑，存储左/右前额叶的均值
    hbo_lpfc_raw = Column(Float, comment="左前额叶 HbO 原始值")
    hbo_rpfc_raw = Column(Float, comment="右前额叶 HbO 原始值")

    # --- 预处理后数据 (Filtered) ---
    # 对应文档提到的“滤波算法去除运动干扰”
    hbo_lpfc_filtered = Column(Float, nullable=True, comment="左前额叶 HbO 滤波后值")
    hbo_rpfc_filtered = Column(Float, nullable=True, comment="右前额叶 HbO 滤波后值")

    # 如果需要存储所有通道的原始帧，可以使用 JSON 字段 (可选)
    # full_frame_json = Column(JSON, nullable=True, comment="全通道数据备份")

    session = relationship("ReadingSession", back_populates="nirs_data")


class BehaviorEvent(Base):
    """
    【行为采集模块】行为交互表
    对应文档：记录停留时长、翻页频率等行为指标
    特点：事件驱动，数据较稀疏。
    """
    __tablename__ = "behavior_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("reading_sessions.id"))
    timestamp = Column(DateTime, default=datetime.now, comment="事件发生时间")

    # 事件类型：PAGE_TURN(翻页), CLICK(点击), SCROLL(滑动), PAUSE(暂停)
    event_type = Column(String(50), index=True)

    # 事件详情：例如 "Page 5 -> Page 6" 或 "Stayed 45s"
    event_value = Column(String(255))

    session = relationship("ReadingSession", back_populates="behavior_events")


class EvaluationLog(Base):
    """
    【多模态评估 & 自适应调度模块】核心算法日志表
    对应文档：多模态融合 -> 输出评估结果 -> 自适应调整内容
    作用：这是你算法有效性的直接证据，记录了系统每一刻的“思考过程”。
    """
    __tablename__ = "evaluation_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("reading_sessions.id"))
    timestamp = Column(DateTime, default=datetime.now)

    # --- 1. 输入特征 (多模态) ---
    nirs_feature_val = Column(Float, comment="提取的生理特征值")
    behavior_feature_val = Column(Float, comment="提取的行为特征值")

    # --- 2. 融合评估结果 ---
    # 对应文档：加权评分或回归分析输出
    fusion_score = Column(Float, comment="多模态融合专注度评分 (0-100)")
    # 对应文档：低(<60)/中(60-85)/高(>85)
    focus_level = Column(String(20), comment="专注度等级: LOW/MEDIUM/HIGH")

    # --- 3. 自适应调度动作 ---
    # 对应文档：立即启动强干预 / 轻度优化 / 维持
    system_action = Column(String(50), comment="系统执行的动作，如 ENLARGE_FONT")
    action_details = Column(String(255), nullable=True, comment="动作参数，如 'Font size 24px'")

    session = relationship("ReadingSession", back_populates="evaluation_logs")