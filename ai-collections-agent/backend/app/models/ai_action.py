"""AIAction SQLAlchemy model — records every decision made by the AI agent."""

import enum
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ActionType(str, enum.Enum):
    SEND_LINK = "SEND_LINK"
    OFFER_DISCOUNT = "OFFER_DISCOUNT"
    RETRY = "RETRY"
    ESCALATE = "ESCALATE"


class ActionOutcome(str, enum.Enum):
    RECOVERED = "RECOVERED"
    PENDING = "PENDING"
    FAILED = "FAILED"


class AIAction(Base):
    __tablename__ = "ai_actions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True, nullable=False)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), index=True, nullable=False)
    action_type: Mapped[ActionType] = mapped_column(SAEnum(ActionType), nullable=False)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Gemini-generated explanation")
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    outcome: Mapped[ActionOutcome] = mapped_column(
        SAEnum(ActionOutcome), default=ActionOutcome.PENDING, nullable=False
    )
    # Optional metadata — e.g. payment link URL, discount code, etc.
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="ai_actions")
    payment: Mapped["Payment"] = relationship("Payment", back_populates="ai_actions")

    def __repr__(self) -> str:
        return f"<AIAction id={self.id} type={self.action_type} outcome={self.outcome}>"
