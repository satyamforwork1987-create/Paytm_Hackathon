"""
Customer CRUD routes.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.ai_action import AIAction
from app.schemas import CustomerRead, CustomerCreate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("/", response_model=list[CustomerRead])
async def list_customers(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * size
    result = await db.execute(
        select(Customer).order_by(Customer.ltv.desc()).offset(offset).limit(size)
    )
    return result.scalars().all()


@router.get("/{customer_id}")
async def get_customer(customer_id: int, db: AsyncSession = Depends(get_db)):
    """Customer detail view with payment history and AI action history."""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    payments_result = await db.execute(
        select(Payment)
        .where(Payment.customer_id == customer_id)
        .order_by(Payment.created_at.desc())
        .limit(20)
    )
    payments = payments_result.scalars().all()

    actions_result = await db.execute(
        select(AIAction)
        .where(AIAction.customer_id == customer_id)
        .order_by(AIAction.executed_at.desc())
        .limit(10)
    )
    actions = actions_result.scalars().all()

    return {
        "customer": CustomerRead.model_validate(customer),
        "payments": [
            {
                "id": p.id,
                "order_id": p.order_id,
                "amount": p.amount,
                "status": p.status,
                "failure_reason": p.failure_reason,
                "retry_count": p.retry_count,
                "created_at": p.created_at.isoformat(),
            }
            for p in payments
        ],
        "ai_actions": [
            {
                "id": a.id,
                "action_type": a.action_type,
                "reasoning": a.reasoning,
                "outcome": a.outcome,
                "executed_at": a.executed_at.isoformat(),
                "metadata": a.metadata_json,
            }
            for a in actions
        ],
    }


@router.post("/", response_model=CustomerRead, status_code=201)
async def create_customer(payload: CustomerCreate, db: AsyncSession = Depends(get_db)):
    customer = Customer(**payload.model_dump())
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer
