"""
AI Decision Engine — uses Google Gemini (gemini-1.5-flash) to decide
the best recovery action for a failed payment.

Decision matrix:
  LTV > 5000 AND retry_count < 2  → SEND_LINK  (personalized payment link)
  LTV > 5000 AND retry_count >= 2 → OFFER_DISCOUNT (10% off)
  LTV <= 5000 AND retry_count < 3 → RETRY (auto-retry)
  retry_count >= 3                → ESCALATE to human
"""

import json
import logging
from datetime import datetime
from typing import Optional

import google.generativeai as genai

from app.config import settings
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.ai_action import AIAction, ActionType, ActionOutcome
from app.services.paytm_service import paytm_service

logger = logging.getLogger(__name__)

# Lazy Gemini client — initialized on first use to avoid module-import side effects
_gemini_model = None

def _get_gemini_model():
    """Return (and cache) the Gemini GenerativeModel, initializing on first call."""
    global _gemini_model
    if _gemini_model is None:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
    return _gemini_model


def _determine_action_type(customer: Customer, payment: Payment) -> ActionType:
    """
    Rule-based decision logic (hard rules, Gemini adds reasoning narrative).
    """
    if payment.retry_count >= 3:
        return ActionType.ESCALATE
    if customer.ltv > 5000:
        if payment.retry_count < 2:
            return ActionType.SEND_LINK
        else:
            return ActionType.OFFER_DISCOUNT
    else:
        return ActionType.RETRY


async def _get_gemini_reasoning(
    customer: Customer,
    payment: Payment,
    action_type: ActionType,
) -> str:
    """
    Ask Gemini to explain WHY this action was chosen and HOW to personalize it.
    Falls back to a template string if the API call fails.
    """
    prompt = f"""
You are an AI Collections Agent for Paytm — a payment recovery specialist.

## Customer Profile
- Name: {customer.name}
- Lifetime Value (LTV): ₹{customer.ltv:,.0f}
- Churn Risk Score: {customer.churn_risk:.2f} (0=low, 1=high)
- Email: {customer.email}

## Failed Payment Details
- Amount: ₹{payment.amount:,.2f}
- Failure Reason: {payment.failure_reason or "Unknown"}
- Number of retries so far: {payment.retry_count}
- Order ID: {payment.order_id}

## Decision Taken
Action: **{action_type.value}**

## Your Task
In 2-3 concise sentences:
1. Explain WHY this is the optimal recovery action for this specific customer.
2. Mention what personalization should be applied (tone, offer, urgency level).
3. Estimate likelihood of recovery (Low / Medium / High).

Be direct, analytical, and data-driven. Do not add greetings or filler text.
"""

    try:
        response = await _get_gemini_model().generate_content_async(prompt)
        reasoning = response.text.strip()
        logger.info("Gemini reasoning generated for customer_id=%s", customer.id)
        return reasoning
    except Exception as exc:
        logger.warning("Gemini API error, using fallback reasoning: %s", exc)
        return _fallback_reasoning(customer, payment, action_type)


def _fallback_reasoning(customer: Customer, payment: Payment, action: ActionType) -> str:
    """Template-based fallback when Gemini is unavailable."""
    templates = {
        ActionType.SEND_LINK: (
            f"High-value customer (LTV ₹{customer.ltv:,.0f}) with {payment.retry_count} prior retries. "
            f"Sending a personalized payment link with warm tone. Recovery likelihood: High."
        ),
        ActionType.OFFER_DISCOUNT: (
            f"Premium customer with LTV ₹{customer.ltv:,.0f} showing payment friction after {payment.retry_count} attempts. "
            f"Offering 10% discount to reduce barrier. Recovery likelihood: Medium-High."
        ),
        ActionType.RETRY: (
            f"Standard customer (LTV ₹{customer.ltv:,.0f}). Auto-retry attempt {payment.retry_count + 1}. "
            f"Failure reason: {payment.failure_reason or 'Network issue'}. Recovery likelihood: Medium."
        ),
        ActionType.ESCALATE: (
            f"Customer has exceeded {payment.retry_count} retry attempts. "
            f"Automated recovery exhausted; escalating to human agent for direct intervention. Recovery likelihood: Low."
        ),
    }
    return templates.get(action, "Action taken based on payment recovery policy.")


async def decide_action(
    customer: Customer,
    payment: Payment,
    db_session=None,
) -> AIAction:
    """
    Main entrypoint — decides the recovery action and creates an AIAction record.

    Args:
        customer: Customer ORM object
        payment: Payment ORM object (must be FAILED status)
        db_session: Optional async DB session to persist the action

    Returns:
        AIAction ORM object (not yet committed if db_session is None)
    """
    action_type = _determine_action_type(customer, payment)
    reasoning = await _get_gemini_reasoning(customer, payment, action_type)

    # Build metadata payload based on action
    metadata = {}

    if action_type == ActionType.SEND_LINK:
        try:
            link_data = await paytm_service.generate_payment_link(
                amount=payment.amount,
                customer_email=customer.email,
                customer_mobile=customer.mobile,
                order_id=f"RECOVER_{payment.order_id}",
            )
            metadata["payment_link"] = link_data.get("shortUrl")
            metadata["recover_order_id"] = link_data.get("order_id")
        except Exception as exc:
            logger.error("Failed to generate payment link: %s", exc)
            metadata["error"] = str(exc)

    elif action_type == ActionType.OFFER_DISCOUNT:
        discounted_amount = payment.amount * 0.90
        try:
            link_data = await paytm_service.generate_payment_link(
                amount=discounted_amount,
                customer_email=customer.email,
                customer_mobile=customer.mobile,
                order_id=f"DISC_{payment.order_id}",
            )
            metadata["payment_link"] = link_data.get("shortUrl")
            metadata["discount_percent"] = 10
            metadata["original_amount"] = payment.amount
            metadata["discounted_amount"] = discounted_amount
        except Exception as exc:
            logger.error("Failed to generate discount link: %s", exc)
            metadata["error"] = str(exc)

    elif action_type == ActionType.RETRY:
        try:
            retry_data = await paytm_service.retry_payment(
                amount=payment.amount,
                customer_email=customer.email,
                customer_mobile=customer.mobile,
                original_order_id=payment.order_id,
            )
            metadata["retry_order_id"] = retry_data.get("order_id")
            metadata["retry_link"] = retry_data.get("shortUrl")
        except Exception as exc:
            logger.error("Failed to initiate retry: %s", exc)
            metadata["error"] = str(exc)

    ai_action = AIAction(
        customer_id=customer.id,
        payment_id=payment.id,
        action_type=action_type,
        reasoning=reasoning,
        executed_at=datetime.utcnow(),
        outcome=ActionOutcome.PENDING,
        metadata_json=json.dumps(metadata),
    )

    if db_session:
        db_session.add(ai_action)
        await db_session.flush()
        logger.info(
            "AIAction created: id=%s type=%s customer_id=%s",
            ai_action.id,
            action_type,
            customer.id,
        )

    return ai_action
