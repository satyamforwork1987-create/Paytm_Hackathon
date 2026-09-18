"""Pydantic schemas for request/response serialization."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from app.models.payment import PaymentStatus
from app.models.ai_action import ActionType, ActionOutcome


# ── Customer ──────────────────────────────────────────────────────────────────

class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    mobile: str
    ltv: float = 0.0
    churn_risk: float = Field(0.0, ge=0.0, le=1.0)


class CustomerCreate(CustomerBase):
    pass


class CustomerRead(CustomerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Payment ───────────────────────────────────────────────────────────────────

class PaymentBase(BaseModel):
    order_id: str
    amount: float
    status: PaymentStatus = PaymentStatus.PENDING
    failure_reason: Optional[str] = None
    retry_count: int = 0


class PaymentCreate(PaymentBase):
    customer_id: int


class PaymentRead(PaymentBase):
    id: int
    customer_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── AIAction ──────────────────────────────────────────────────────────────────

class AIActionBase(BaseModel):
    action_type: ActionType
    reasoning: Optional[str] = None
    outcome: ActionOutcome = ActionOutcome.PENDING
    metadata_json: Optional[str] = None


class AIActionCreate(AIActionBase):
    customer_id: int
    payment_id: int


class AIActionRead(AIActionBase):
    id: int
    customer_id: int
    payment_id: int
    executed_at: datetime

    class Config:
        from_attributes = True


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardMetrics(BaseModel):
    total_recovered: float
    recovery_rate: float
    active_cases: int
    escalations: int
    total_failed: int


class RecoveryDataPoint(BaseModel):
    date: str
    recovered: float
    failed: float


class PaginatedPayments(BaseModel):
    items: List[PaymentRead]
    total: int
    page: int
    size: int


class PaginatedAIActions(BaseModel):
    items: List[AIActionRead]
    total: int
    page: int
    size: int


# ── Webhooks ──────────────────────────────────────────────────────────────────

class PaytmWebhookPayload(BaseModel):
    """Paytm sends form-encoded data; this schema is for internal use after parsing."""
    MID: Optional[str] = None
    ORDERID: Optional[str] = None
    TXNID: Optional[str] = None
    TXNAMOUNT: Optional[str] = None
    STATUS: Optional[str] = None
    RESPCODE: Optional[str] = None
    RESPMSG: Optional[str] = None
    CHECKSUMHASH: Optional[str] = None
    BANKTXNID: Optional[str] = None
    TXNDATE: Optional[str] = None
