"""
══════════════════════════════════════════
DATA PIPELINE — REPLACE WITH REAL SOURCE
══════════════════════════════════════════
This is a placeholder. To integrate real data:
1. Replace the source URL/connection string below
2. Update the schema mapping in the SCHEMA_MAP dict
3. Remove the synthetic generator call

Generates synthetic data for demo purposes using the Faker library.
Run with:  python -m app.pipelines.generate_synthetic
"""

import asyncio
import json
import random
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Allow running as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from faker import Faker
from faker.providers import internet, person, phone_number

fake = Faker("en_IN")  # Indian locale for realistic names & numbers
fake.add_provider(internet)
fake.add_provider(person)
fake.add_provider(phone_number)

random.seed(42)  # Reproducible synthetic data

# ─────────────────────────────────────────────────────────────────────────────
# SCHEMA MAP — update these when connecting real data sources
# ─────────────────────────────────────────────────────────────────────────────
CUSTOMER_SCHEMA_MAP = {
    # "real_field_name": "our_db_field_name"
    "customer_id": "id",
    "full_name": "name",
    "email_address": "email",
    "phone": "mobile",
    "lifetime_value": "ltv",
    "churn_score": "churn_risk",
}

PAYMENT_SCHEMA_MAP = {
    "txn_ref": "order_id",
    "txn_amount": "amount",
    "txn_status": "status",
    "failure_msg": "failure_reason",
    "attempt_count": "retry_count",
}

# ─────────────────────────────────────────────────────────────────────────────
# Failure reasons pool (realistic Paytm failure messages)
# ─────────────────────────────────────────────────────────────────────────────
FAILURE_REASONS = [
    "Insufficient funds in account",
    "Card declined by issuing bank",
    "Transaction timeout - network error",
    "OTP verification failed",
    "Card expired",
    "Daily transaction limit exceeded",
    "Invalid CVV entered",
    "Bank server unavailable",
    "UPI PIN mismatch",
    "Net banking session expired",
]


def generate_customers(count: int = 50) -> list[dict]:
    """Generate synthetic customer records."""
    customers = []
    for i in range(1, count + 1):
        ltv = round(random.uniform(500, 50000), 2)
        churn_risk = round(random.uniform(0.0, 1.0), 2)

        # High LTV customers tend to have lower churn risk
        if ltv > 20000:
            churn_risk = round(churn_risk * 0.4, 2)

        customers.append({
            "id": i,
            "name": fake.name(),
            "email": fake.unique.email(),
            "mobile": f"9{random.randint(100000000, 999999999)}",
            "ltv": ltv,
            "churn_risk": churn_risk,
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(30, 730))).isoformat(),
        })

    print(f"✅ Generated {len(customers)} customers")
    return customers


def generate_payments(customers: list[dict], payments_per_customer: int = 4) -> list[dict]:
    """
    Generate synthetic payment records.
    ~20% failure rate across all payments.
    """
    payments = []
    payment_id = 1

    payment_statuses_pool = (
        ["SUCCESS"] * 8 + ["FAILED"] * 2  # 20% failure
    )

    for customer in customers:
        for j in range(payments_per_customer):
            status = random.choice(payment_statuses_pool)
            amount = round(random.uniform(99, 9999), 2)
            created_at = datetime.utcnow() - timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
            )

            payment = {
                "id": payment_id,
                "customer_id": customer["id"],
                "order_id": f"ORD{payment_id:08d}SYNTH",
                "amount": amount,
                "status": status,
                "failure_reason": random.choice(FAILURE_REASONS) if status == "FAILED" else None,
                "retry_count": random.randint(0, 3) if status == "FAILED" else 0,
                "created_at": created_at.isoformat(),
                "updated_at": created_at.isoformat(),
            }
            payments.append(payment)
            payment_id += 1

    failed_count = sum(1 for p in payments if p["status"] == "FAILED")
    print(f"✅ Generated {len(payments)} payments ({failed_count} failed, {failed_count/len(payments)*100:.1f}% failure rate)")
    return payments


async def generate_ai_actions(payments: list[dict], customers_by_id: dict) -> list[dict]:
    """Generate AI action records for failed payments."""
    from app.models.ai_action import ActionType, ActionOutcome

    actions = []
    action_id = 1

    for payment in payments:
        if payment["status"] != "FAILED":
            continue

        customer = customers_by_id[payment["customer_id"]]
        ltv = customer["ltv"]
        retry_count = payment["retry_count"]

        # Mirror the decision engine logic
        if retry_count >= 3:
            action_type = "ESCALATE"
        elif ltv > 5000 and retry_count < 2:
            action_type = "SEND_LINK"
        elif ltv > 5000 and retry_count >= 2:
            action_type = "OFFER_DISCOUNT"
        else:
            action_type = "RETRY"

        outcomes_pool = ["RECOVERED"] * 6 + ["PENDING"] * 3 + ["FAILED"] * 1
        if action_type == "ESCALATE":
            outcomes_pool = ["PENDING"] * 7 + ["RECOVERED"] * 2 + ["FAILED"] * 1

        actions.append({
            "id": action_id,
            "customer_id": payment["customer_id"],
            "payment_id": payment["id"],
            "action_type": action_type,
            "reasoning": f"Synthetic reasoning for demo — action {action_type} chosen based on LTV ₹{ltv:,.0f} and {retry_count} retries.",
            "executed_at": payment["created_at"],
            "outcome": random.choice(outcomes_pool),
            "metadata_json": "{}",
        })
        action_id += 1

    print(f"✅ Generated {len(actions)} AI actions")
    return actions


async def run_pipeline(output_dir: str = "backend/data"):
    """
    Main pipeline entry point.
    Generates all synthetic data and saves to JSON files.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print("\n🔄 Running Synthetic Data Pipeline...")
    print("=" * 50)

    customers = generate_customers(50)
    payments = generate_payments(customers, payments_per_customer=4)
    customers_by_id = {c["id"]: c for c in customers}
    ai_actions = await generate_ai_actions(payments, customers_by_id)

    # Save to JSON files (used by ingest_customers.py and ingest_payments.py)
    with open(f"{output_dir}/customers.json", "w") as f:
        json.dump(customers, f, indent=2)

    with open(f"{output_dir}/payments.json", "w") as f:
        json.dump(payments, f, indent=2)

    with open(f"{output_dir}/ai_actions.json", "w") as f:
        json.dump(ai_actions, f, indent=2)

    print("=" * 50)
    print(f"📁 Data saved to: {output_dir}/")
    print("   ├── customers.json")
    print("   ├── payments.json")
    print("   └── ai_actions.json")
    print("\n✨ Run 'python -m app.pipelines.ingest_customers' to load into DB")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
