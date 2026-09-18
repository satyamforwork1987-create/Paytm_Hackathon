"""
Paytm Webhook receiver.

POST /webhooks/paytm — Called by Paytm when a transaction completes or fails.

Flow:
  1. Parse form-encoded body from Paytm
  2. Verify checksum (reject if invalid)
  3. Idempotency check — skip if order_id already processed
  4. TXN_FAILURE → trigger AI decision engine
  5. TXN_SUCCESS → mark payment recovered, update AIAction outcome
"""

import logging
from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db, AsyncSessionLocal
from app.models.payment import Payment, PaymentStatus
from app.models.customer import Customer
from app.models.ai_action import AIAction, ActionOutcome
from app.services.ai_decision_engine import decide_action
from app.services.escalation_service import escalate_to_human
from app.utils.paytm_checksum import verify_checksum
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/paytm")
async def paytm_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Paytm sends form-encoded POST data after every transaction attempt.
    We verify the checksum first, then route based on STATUS.
    """
    # ── Step 1: Parse form body ───────────────────────────────────────────
    form_data = await request.form()
    payload = dict(form_data)
    logger.info("Received Paytm webhook: ORDERID=%s STATUS=%s", payload.get("ORDERID"), payload.get("STATUS"))

    # ── Step 2: Verify checksum ───────────────────────────────────────────
    checksum = payload.pop("CHECKSUMHASH", None)
    if not checksum:
        logger.warning("Webhook rejected: missing CHECKSUMHASH")
        raise HTTPException(status_code=400, detail="Missing checksum")

    if not verify_checksum(payload, settings.PAYTM_MERCHANT_KEY, checksum):
        logger.warning("Webhook rejected: invalid checksum for order %s", payload.get("ORDERID"))
        raise HTTPException(status_code=400, detail="Invalid checksum")

    order_id = payload.get("ORDERID")
    status = payload.get("STATUS")
    amount_str = payload.get("TXNAMOUNT", "0")

    if not order_id:
        raise HTTPException(status_code=400, detail="Missing ORDERID")

    # ── Step 3: Idempotency check ─────────────────────────────────────────
    result = await db.execute(select(Payment).where(Payment.order_id == order_id))
    payment = result.scalar_one_or_none()

    if payment is None:
        logger.warning("No payment record found for order_id=%s", order_id)
        # Could be a new payment; create a stub record
        return {"status": "ignored", "reason": "no_payment_record"}

    if payment.status == PaymentStatus.RECOVERED:
        logger.info("Idempotency skip: order_id=%s already recovered", order_id)
        return {"status": "already_processed"}

    # ── Step 4: Handle TXN_SUCCESS ────────────────────────────────────────
    if status == "TXN_SUCCESS":
        payment.status = PaymentStatus.RECOVERED
        await db.commit()

        # Update latest pending AI action outcome
        action_result = await db.execute(
            select(AIAction)
            .where(AIAction.payment_id == payment.id, AIAction.outcome == ActionOutcome.PENDING)
            .order_by(AIAction.executed_at.desc())
            .limit(1)
        )
        ai_action = action_result.scalar_one_or_none()
        if ai_action:
            ai_action.outcome = ActionOutcome.RECOVERED
            await db.commit()

        logger.info("✅ Payment RECOVERED: order_id=%s amount=%s", order_id, amount_str)
        return {"status": "recovered", "order_id": order_id}

    # ── Step 5: Handle TXN_FAILURE ────────────────────────────────────────
    if status == "TXN_FAILURE":
        failure_reason = payload.get("RESPMSG", "Unknown failure")
        payment.status = PaymentStatus.FAILED
        payment.failure_reason = failure_reason
        payment.retry_count += 1
        await db.flush()

        # Fetch customer
        cust_result = await db.execute(
            select(Customer).where(Customer.id == payment.customer_id)
        )
        customer = cust_result.scalar_one_or_none()
        if not customer:
            await db.commit()
            return {"status": "no_customer"}

        # Trigger AI decision engine in background so webhook returns fast
        # Pass IDs only — background task will open its own session
        background_tasks.add_task(
            _run_ai_decision, customer.id, payment.id
        )

        await db.commit()
        logger.info("❌ Payment FAILED: order_id=%s reason=%s → AI triggered", order_id, failure_reason)
        return {"status": "failed", "action": "ai_triggered", "order_id": order_id}

    logger.info("Unhandled status=%s for order=%s", status, order_id)
    return {"status": "unhandled", "payment_status": status}


async def _run_ai_decision(customer_id: int, payment_id: int):
    """Background task: run AI decision and persist the action. Opens its own DB session."""
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        try:
            cust_result = await db.execute(select(Customer).where(Customer.id == customer_id))
            customer = cust_result.scalar_one_or_none()
            pay_result = await db.execute(select(Payment).where(Payment.id == payment_id))
            payment = pay_result.scalar_one_or_none()
            if not customer or not payment:
                logger.error("Background task: customer or payment not found (cid=%s, pid=%s)", customer_id, payment_id)
                return

            ai_action = await decide_action(customer, payment, db_session=db)
            await db.commit()

            from app.models.ai_action import ActionType
            if ai_action.action_type == ActionType.ESCALATE:
                await escalate_to_human(ai_action, customer, payment, db)
                await db.commit()

        except Exception as exc:
            logger.error("AI decision failed for payment_id=%s: %s", payment_id, exc)
            await db.rollback()
