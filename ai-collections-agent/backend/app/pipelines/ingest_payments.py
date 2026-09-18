"""
══════════════════════════════════════════
DATA PIPELINE — REPLACE WITH REAL SOURCE
══════════════════════════════════════════
This is a placeholder. To integrate real data:
1. Replace the source URL/connection string below
2. Update the schema mapping in the SCHEMA_MAP dict
3. Remove the synthetic generator call

Current behavior: reads from /data/payments.json and simulates webhook events
TODO: Replace with real Paytm transaction sync or webhook replay
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# TODO: Replace this with real Paytm transaction sync or webhook replay
# Examples:
#   source = "https://securegw.paytm.in/v3/order/bulkQuery"  # Paytm bulk API
#   source = "kafka://broker:9092/paytm-transactions"        # Kafka stream
#   source = "backend/data/payments.json"                    # Local file (current)
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_SOURCE = "backend/data/payments.json"

SCHEMA_MAP = {
    # "source_field": "db_field"
    # TODO: Update these mappings when connecting Paytm bulk transaction API
    "id": "id",
    "customer_id": "customer_id",
    "order_id": "order_id",
    "amount": "amount",
    "status": "status",
    "failure_reason": "failure_reason",
    "retry_count": "retry_count",
    "created_at": "created_at",
}


async def ingest_payment_events(source: str = DEFAULT_SOURCE) -> int:
    """
    Ingest payment events from source into the database.

    Args:
        source: Path, Kafka topic, or API endpoint for payment data.
                TODO: Replace with real Paytm transaction sync.

    Returns:
        Number of payment events ingested.
    """
    # TODO: Replace this block with real Paytm transaction connector
    # ── STUB: Read from local JSON ────────────────────────────────────────
    source_path = Path(source)
    if not source_path.exists():
        logger.warning("Source file not found: %s — run generate_synthetic.py first", source)
        return 0

    with open(source_path) as f:
        raw_data = json.load(f)

    logger.info("Loaded %d payment records from %s", len(raw_data), source)

    # Apply schema mapping
    mapped_payments = [
        {db_field: record.get(src_field) for src_field, db_field in SCHEMA_MAP.items()}
        for record in raw_data
    ]

    # Persist to database
    from app.database import AsyncSessionLocal, init_db
    from app.models.payment import Payment, PaymentStatus

    await init_db()

    ingested = 0
    async with AsyncSessionLocal() as session:
        for data in mapped_payments:
            from sqlalchemy import select
            result = await session.execute(
                select(Payment).where(Payment.order_id == data["order_id"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                continue  # Idempotent — skip duplicates

            try:
                status = PaymentStatus(data["status"])
            except ValueError:
                status = PaymentStatus.PENDING

            payment = Payment(
                customer_id=int(data["customer_id"]),
                order_id=data["order_id"],
                amount=float(data.get("amount", 0)),
                status=status,
                failure_reason=data.get("failure_reason"),
                retry_count=int(data.get("retry_count", 0)),
            )
            session.add(payment)
            ingested += 1

        await session.commit()

    logger.info("✅ Ingested %d new payment events into database", ingested)
    return ingested


async def ingest_ai_actions(source: str = "backend/data/ai_actions.json") -> int:
    """
    Load pre-generated AI action records for demo purposes.
    TODO: In production, AI actions are created by the decision engine in real-time.
    """
    source_path = Path(source)
    if not source_path.exists():
        logger.warning("AI actions file not found: %s", source)
        return 0

    with open(source_path) as f:
        raw_data = json.load(f)

    from app.database import AsyncSessionLocal
    from app.models.ai_action import AIAction, ActionType, ActionOutcome
    from sqlalchemy import select

    ingested = 0
    async with AsyncSessionLocal() as session:
        for data in raw_data:
            try:
                action = AIAction(
                    customer_id=int(data["customer_id"]),
                    payment_id=int(data["payment_id"]),
                    action_type=ActionType(data["action_type"]),
                    reasoning=data.get("reasoning"),
                    outcome=ActionOutcome(data.get("outcome", "PENDING")),
                    metadata_json=data.get("metadata_json", "{}"),
                )
                session.add(action)
                ingested += 1
            except Exception as exc:
                logger.warning("Skipping AI action: %s", exc)

        await session.commit()

    logger.info("✅ Ingested %d AI action records", ingested)
    return ingested


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = asyncio.run(ingest_payment_events())
    print(f"Ingested {count} payment events")
