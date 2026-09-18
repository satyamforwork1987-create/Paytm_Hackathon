"""Payment SQLAlchemy model."""

import enum
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, Integer, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PaymentStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    RECOVERED = "RECOVERED"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True, nullable=False)
    order_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False, comment="Amount in INR")
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False
    )
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="payments")
    ai_actions: Mapped[list["AIAction"]] = relationship("AIAction", back_populates="payment", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} order_id={self.order_id} status={self.status}>"
