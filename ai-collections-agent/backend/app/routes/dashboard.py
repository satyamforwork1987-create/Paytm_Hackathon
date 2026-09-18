"""
Dashboard API routes — aggregated metrics and paginated lists for the frontend.
"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models.payment import Payment, PaymentStatus
from app.models.ai_action import AIAction, ActionType, ActionOutcome
from app.models.customer import Customer
from app.schemas import (
    DashboardMetrics,
    PaginatedPayments,
    PaginatedAIActions,
    PaymentRead,
    AIActionRead,
    RecoveryDataPoint,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
async def get_metrics(db: AsyncSession = Depends(get_db)):
    """
    Aggregated KPIs for the main dashboard.
    Returns: total_recovered (INR), recovery_rate (%), active_cases, escalations.
    """
    # Total recovered amount (sum of INR)
    recovered_amount_result = await db.execute(
        select(func.sum(Payment.amount)).where(Payment.status == PaymentStatus.RECOVERED)
    )
    total_recovered = recovered_amount_result.scalar() or 0.0

    # Count of payments that were ever failed (FAILED + RECOVERED after failure)
    failed_count_result = await db.execute(
        select(func.count(Payment.id)).where(
            Payment.status.in_([PaymentStatus.FAILED, PaymentStatus.RECOVERED])
        )
    )
    total_failed = failed_count_result.scalar() or 0

    # Count of payments successfully recovered
    recovered_count_result = await db.execute(
        select(func.count(Payment.id)).where(Payment.status == PaymentStatus.RECOVERED)
    )
    recovered_count = recovered_count_result.scalar() or 0

    # Recovery rate = recovered_count / total_failed_count (not amount / count!)
    recovery_rate = round((recovered_count / total_failed * 100), 1) if total_failed > 0 else 0.0

    # Active cases (pending AI actions on non-recovered payments)
    active_result = await db.execute(
        select(func.count(AIAction.id)).where(AIAction.outcome == ActionOutcome.PENDING)
    )
    active_cases = active_result.scalar() or 0

    # Escalations count
    escalation_result = await db.execute(
        select(func.count(AIAction.id)).where(
            and_(
                AIAction.action_type == ActionType.ESCALATE,
                AIAction.outcome == ActionOutcome.PENDING,
            )
        )
    )
    escalations = escalation_result.scalar() or 0

    return DashboardMetrics(
        total_recovered=round(total_recovered, 2),
        recovery_rate=recovery_rate,
        active_cases=active_cases,
        escalations=escalations,
        total_failed=total_failed,
    )


@router.get("/recovery-trend", response_model=list[RecoveryDataPoint])
async def get_recovery_trend(db: AsyncSession = Depends(get_db)):
    """Last 7 days of recovered vs failed revenue for the line chart."""
    results = []
    today = datetime.utcnow().date()

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day)
        day_end = day_start + timedelta(days=1)

        recovered = await db.execute(
            select(func.sum(Payment.amount)).where(
                and_(
                    Payment.status == PaymentStatus.RECOVERED,
                    Payment.updated_at >= day_start,
                    Payment.updated_at < day_end,
                )
            )
        )
        failed = await db.execute(
            select(func.sum(Payment.amount)).where(
                and_(
                    Payment.status == PaymentStatus.FAILED,
                    Payment.created_at >= day_start,
                    Payment.created_at < day_end,
                )
            )
        )
        results.append(
            RecoveryDataPoint(
                date=day.strftime("%b %d"),
                recovered=round(recovered.scalar() or 0.0, 2),
                failed=round(failed.scalar() or 0.0, 2),
            )
        )

    return results


@router.get("/failed-payments", response_model=PaginatedPayments)
async def get_failed_payments(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Paginated list of failed payments for the failed-payments page."""
    offset = (page - 1) * size

    count_result = await db.execute(
        select(func.count(Payment.id)).where(Payment.status == PaymentStatus.FAILED)
    )
    total = count_result.scalar() or 0

    items_result = await db.execute(
        select(Payment)
        .where(Payment.status == PaymentStatus.FAILED)
        .order_by(Payment.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    items = items_result.scalars().all()

    return PaginatedPayments(
        items=[PaymentRead.model_validate(p) for p in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/ai-actions", response_model=PaginatedAIActions)
async def get_ai_actions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Paginated list of AI decisions for the AI log page."""
    offset = (page - 1) * size

    count_result = await db.execute(select(func.count(AIAction.id)))
    total = count_result.scalar() or 0

    items_result = await db.execute(
        select(AIAction)
        .order_by(AIAction.executed_at.desc())
        .offset(offset)
        .limit(size)
    )
    items = items_result.scalars().all()

    return PaginatedAIActions(
        items=[AIActionRead.model_validate(a) for a in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/escalations", response_model=PaginatedAIActions)
async def get_escalations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List of cases flagged for human review."""
    offset = (page - 1) * size

    count_result = await db.execute(
        select(func.count(AIAction.id)).where(
            and_(
                AIAction.action_type == ActionType.ESCALATE,
                AIAction.outcome == ActionOutcome.PENDING,
            )
        )
    )
    total = count_result.scalar() or 0

    items_result = await db.execute(
        select(AIAction)
        .where(
            and_(
                AIAction.action_type == ActionType.ESCALATE,
                AIAction.outcome == ActionOutcome.PENDING,
            )
        )
        .order_by(AIAction.executed_at.desc())
        .offset(offset)
        .limit(size)
    )
    items = items_result.scalars().all()

    return PaginatedAIActions(
        items=[AIActionRead.model_validate(a) for a in items],
        total=total,
        page=page,
        size=size,
    )
