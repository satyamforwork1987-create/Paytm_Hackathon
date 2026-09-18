"""
AI Agent manual trigger endpoints.
Allows the frontend or operators to manually trigger AI decisions
or resolve escalations without waiting for a webhook.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.payment import Payment, PaymentStatus
from app.models.customer import Customer
from app.models.ai_action import AIAction, ActionOutcome
from app.services.ai_decision_engine import decide_action
from app.services.escalation_service import resolve_escalation
from app.schemas import AIActionRead

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["ai-agent"])


@router.post("/trigger/{payment_id}", response_model=AIActionRead)
async def manually_trigger_ai(payment_id: int, db: AsyncSession = Depends(get_db)):
    """
    Manually trigger AI decision for a specific failed payment.
    Useful for demo and testing.
    """
    pay_result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = pay_result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status not in [PaymentStatus.FAILED, PaymentStatus.PENDING]:
        raise HTTPException(status_code=400, detail=f"Payment status is {payment.status}, not FAILED")

    cust_result = await db.execute(select(Customer).where(Customer.id == payment.customer_id))
    customer = cust_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    ai_action = await decide_action(customer, payment, db_session=db)
    await db.commit()
    await db.refresh(ai_action)

    logger.info("Manual AI trigger: payment_id=%d → action=%s", payment_id, ai_action.action_type)
    return AIActionRead.model_validate(ai_action)


@router.post("/escalations/{action_id}/resolve")
async def resolve_escalation_endpoint(action_id: int, db: AsyncSession = Depends(get_db)):
    """Human agent marks escalation as resolved."""
    success = await resolve_escalation(action_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Escalation not found")
    await db.commit()
    return {"status": "resolved", "action_id": action_id}


@router.get("/status/{action_id}", response_model=AIActionRead)
async def get_action_status(action_id: int, db: AsyncSession = Depends(get_db)):
    """Get current status of an AI action."""
    result = await db.execute(select(AIAction).where(AIAction.id == action_id))
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="AI action not found")
    return AIActionRead.model_validate(action)
