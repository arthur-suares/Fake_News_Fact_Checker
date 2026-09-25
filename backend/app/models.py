import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="processing", nullable=False)
    verdict: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fact_check_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    image_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    evidence: Mapped[list["Evidence"]] = relationship(back_populates="verification", cascade="all, delete-orphan")
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="verification", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    verification_id: Mapped[str] = mapped_column(ForeignKey("verifications.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    rating: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    verification: Mapped[Verification] = relationship(back_populates="evidence")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    verification_id: Mapped[str] = mapped_column(ForeignKey("verifications.id"), nullable=False)
    answers: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    verification: Mapped[Verification] = relationship(back_populates="feedback")
