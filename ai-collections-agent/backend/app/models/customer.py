"""Customer SQLAlchemy model."""

from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    mobile: Mapped[str] = mapped_column(String(15), nullable=False)
    ltv: Mapped[float] = mapped_column(Float, default=0.0, comment="Lifetime value in INR")
    churn_risk: Mapped[float] = mapped_column(Float, default=0.0, comment="0-1 float, higher = riskier")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    # Relationships
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="customer", lazy="selectin")
    ai_actions: Mapped[list["AIAction"]] = relationship("AIAction", back_populates="customer", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Customer id={self.id} email={self.email} ltv={self.ltv}>"
