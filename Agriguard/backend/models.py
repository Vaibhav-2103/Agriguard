import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="farmer", nullable=False)  # "farmer" or "expert"
    preferred_language = Column(String(10), default="en", nullable=False)  # en, hi, pa
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    expert_reviews = relationship("ExpertReview", back_populates="expert")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    image_path = Column(String(500), nullable=False)
    overlay_path = Column(String(500), nullable=True)
    crop = Column(String(100), nullable=True)
    location = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    predicted_class = Column(String(150), nullable=True)
    confidence = Column(Float, nullable=True)
    top3_json = Column(Text, nullable=True)  # JSON string of top 3 classes & probabilities
    severity = Column(String(20), nullable=True)  # "Low", "Medium", "High", or None for healthy
    severity_ratio = Column(Float, nullable=True)  # 0.0 - 1.0
    status = Column(String(50), default="completed", nullable=False)  # completed, needs_better_image, low_confidence
    insight_json = Column(Text, nullable=True)  # full knowledge base insight dict serialized to JSON
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="reports")
    conversations = relationship("Conversation", back_populates="report", cascade="all, delete-orphan")
    expert_reviews = relationship("ExpertReview", back_populates="report", cascade="all, delete-orphan")
    processing_logs = relationship("ProcessingLog", back_populates="report")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(200), default="General AgriBot Chat", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="conversations")
    report = relationship("Report", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.id")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")


class ExpertReview(Base):
    __tablename__ = "expert_reviews"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    expert_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    verdict = Column(String(50), nullable=False)  # "agree", "disagree", "needs_more_info"
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    report = relationship("Report", back_populates="expert_reviews")
    expert = relationship("User", back_populates="expert_reviews")


class ProcessingLog(Base):
    __tablename__ = "processing_logs"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="SET NULL"), nullable=True, index=True)
    success = Column(Boolean, nullable=False, default=True)
    error = Column(Text, nullable=True)
    duration_ms = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    report = relationship("Report", back_populates="processing_logs")
