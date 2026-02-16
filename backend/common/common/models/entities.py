from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    Numeric,
    Enum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.db.base import Base


class CampaignStatus(str, PyEnum):
    draft = "draft"
    active = "active"
    paused = "paused"
    completed = "completed"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    credits_balance: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="owner")


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    goal: Mapped[str] = mapped_column(Text)
    audience: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(50), default=CampaignStatus.draft.value
    )

    owner: Mapped["User"] = relationship(back_populates="campaigns")
    assets: Mapped[list["Asset"]] = relationship(back_populates="campaign")


class Asset(Base, TimestampMixin):
    __tablename__ = "assets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), index=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    asset_type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    current_version: Mapped[int] = mapped_column(Integer, default=1)

    campaign: Mapped["Campaign"] = relationship(back_populates="assets")
    versions: Mapped[list["AssetVersion"]] = relationship(back_populates="asset")


class AssetVersion(Base, TimestampMixin):
    __tablename__ = "asset_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    change_note: Mapped[str] = mapped_column(String(255), default="")

    asset: Mapped["Asset"] = relationship(back_populates="versions")


class CreditLedger(Base):
    __tablename__ = "credit_ledger"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    delta: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(120))
    reference_id: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class UsageEvent(Base):
    __tablename__ = "usage_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    service: Mapped[str] = mapped_column(String(80))
    endpoint: Mapped[str] = mapped_column(String(120))
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 4), default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
