"""
Escalation service — handles cases the AI cannot resolve autonomously.
In production, this would send Slack/email/PagerDuty alerts.
"""

import logging
from datetime import datetime
from app.models.ai_action import AIAction, ActionOutcome
from app.models.customer import Customer
from app.models.payment import Payment

logger = logging.getLogger(__name__)


async def escalate_to_human(
    ai_action: AIAction,
    customer: Customer,
    payment: Payment,
    db_session=None,
) -> dict:
    """
    Mark a case as escalated and notify human agents.

    In production: fire Slack webhook, create Jira ticket, send email.
    For the demo: logs the event and updates the outcome.
    """
    logger.warning(
        "🚨 ESCALATION REQUIRED — customer=%s payment=%s amount=₹%.2f retries=%d",
        customer.email,
        payment.order_id,
        payment.amount,
        payment.retry_count,
    )

    escalation_payload = {
        "escalated_at": datetime.utcnow().isoformat(),
        "customer_name": customer.name,
        "customer_email": customer.email,
        "payment_order_id": payment.order_id,
        "amount": payment.amount,
        "retry_count": payment.retry_count,
        "failure_reason": payment.failure_reason,
        "ai_reasoning": ai_action.reasoning,
        "status": "OPEN",
    }

    # TODO (production): Send Slack/email notification here
    # e.g.: await slack_client.chat_postMessage(channel="#collections", text=...)

    logger.info("Escalation payload: %s", escalation_payload)
    return escalation_payload


async def resolve_escalation(ai_action_id: int, db_session) -> bool:
    """Mark an escalated case as resolved by a human agent."""
    from sqlalchemy import select
    result = await db_session.execute(
        select(AIAction).where(AIAction.id == ai_action_id)
    )
    action = result.scalar_one_or_none()
    if not action:
        logger.warning("Escalation not found: id=%d", ai_action_id)
        return False

    action.outcome = ActionOutcome.RECOVERED
    await db_session.flush()
    logger.info("Escalation resolved by human: ai_action_id=%d", ai_action_id)
    return True
