#!/usr/bin/env python3
"""
simulate_failure.py — Demo script to fire a fake Paytm webhook.

This simulates a TXN_FAILURE webhook from Paytm so you can demo the
AI Collections Agent without needing a real failed payment.

Usage:
    python scripts/simulate_failure.py [--order-id ORD123] [--amount 999] [--customer-id 1]
    
    # Quick demo run:
    python scripts/simulate_failure.py
"""

import asyncio
import argparse
import hashlib
import hmac
import json
import random
import sys
import urllib.parse
from pathlib import Path

import httpx

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

BACKEND_URL = "http://localhost:8000"

FAILURE_REASONS = [
    "Insufficient funds in account",
    "Card declined by issuing bank",
    "Transaction timeout - network error",
    "OTP verification failed",
    "Card expired",
]


def build_fake_paytm_payload(order_id: str, amount: float, mid: str) -> dict:
    """Build a fake Paytm TXN_FAILURE form payload."""
    return {
        "MID": mid,
        "ORDERID": order_id,
        "TXNID": f"FAKE_TXN_{random.randint(100000, 999999)}",
        "TXNAMOUNT": f"{amount:.2f}",
        "STATUS": "TXN_FAILURE",
        "RESPCODE": "227",
        "RESPMSG": random.choice(FAILURE_REASONS),
        "BANKTXNID": "",
        "TXNDATE": "2024-01-15 12:30:45",
    }


async def create_test_payment_if_needed(order_id: str, customer_id: int, amount: float):
    """
    Ensure a payment record exists in the DB before firing the webhook.
    Uses the AI agent's manual trigger endpoint to seed a PENDING payment.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        # First verify the customer exists
        try:
            resp = await client.get(f"{BACKEND_URL}/api/customers/{customer_id}")
            if resp.status_code == 404:
                print(f"  ⚠️  Customer #{customer_id} not found — seed data first with:")
                print(f"       python -m app.pipelines.generate_synthetic")
                print(f"       python -m app.pipelines.ingest_customers")
                return
            print(f"  ✅ Customer #{customer_id} exists")
        except Exception as e:
            print(f"  ⚠️  Could not verify customer: {e}")


async def fire_webhook(order_id: str, amount: float, mid: str, merchant_key: str):
    """Fire a fake TXN_FAILURE webhook to the backend."""
    payload = build_fake_paytm_payload(order_id, amount, mid)

    # Generate fake (but structurally valid) checksum
    # In real Paytm, this would be generated server-side
    # For demo, the backend checksum verification is bypassed if PAYTM_MERCHANT_KEY=test
    param_str = "|".join([str(payload.get(k, "")) for k in sorted(payload.keys())])
    fake_checksum = hmac.new(
        merchant_key.encode(), param_str.encode(), hashlib.sha256
    ).hexdigest()
    payload["CHECKSUMHASH"] = fake_checksum

    print(f"\n🔥 Firing fake TXN_FAILURE webhook...")
    print(f"   Order ID : {order_id}")
    print(f"   Amount   : ₹{amount:.2f}")
    print(f"   Status   : TXN_FAILURE")
    print(f"   Reason   : {payload['RESPMSG']}")
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{BACKEND_URL}/webhooks/paytm",
            data=payload,  # Form-encoded, just like real Paytm
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    print(f"📨 Webhook response [{resp.status_code}]:")
    try:
        print(f"   {json.dumps(resp.json(), indent=2)}")
    except Exception:
        print(f"   {resp.text}")

    return resp.status_code == 200


async def trigger_ai_manually(payment_id: int):
    """Manually trigger AI decision for a payment (bypasses webhook)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{BACKEND_URL}/api/ai/trigger/{payment_id}")
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"\n🤖 AI Decision:")
        print(f"   Action  : {data.get('action_type')}")
        print(f"   Outcome : {data.get('outcome')}")
        print(f"   Reasoning: {data.get('reasoning', '')[:200]}...")
    else:
        print(f"\n⚠️  Manual trigger failed: {resp.status_code} — {resp.text}")


async def check_metrics():
    """Fetch and display current dashboard metrics."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{BACKEND_URL}/api/dashboard/metrics")
    
    if resp.status_code == 200:
        m = resp.json()
        print(f"\n📊 Dashboard Metrics (after simulation):")
        print(f"   Total Recovered : ₹{m.get('total_recovered', 0):,.2f}")
        print(f"   Recovery Rate   : {m.get('recovery_rate', 0):.1f}%")
        print(f"   Active Cases    : {m.get('active_cases', 0)}")
        print(f"   Escalations     : {m.get('escalations', 0)}")


async def main():
    parser = argparse.ArgumentParser(description="Simulate a Paytm payment failure for demo")
    parser.add_argument("--order-id", default=f"DEMO_{random.randint(10000, 99999)}", help="Order ID")
    parser.add_argument("--amount", type=float, default=random.uniform(500, 5000), help="Amount in INR")
    parser.add_argument("--customer-id", type=int, default=1, help="Customer ID in DB")
    parser.add_argument("--mid", default="YOUR_TEST_MID", help="Paytm MID")
    parser.add_argument("--key", default="YOUR_TEST_KEY", help="Paytm Merchant Key")
    parser.add_argument("--payment-id", type=int, help="Payment ID for manual AI trigger")
    args = parser.parse_args()

    print("╔══════════════════════════════════════════════════╗")
    print("║  AI Collections Agent — Demo Simulation Script   ║")
    print("╚══════════════════════════════════════════════════╝")

    # Step 1: Check backend is up
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            health = await client.get(f"{BACKEND_URL}/health")
        print(f"\n✅ Backend is UP: {health.json()}")
    except Exception:
        print(f"\n❌ Backend not reachable at {BACKEND_URL}")
        print("   Start it with: cd backend && uvicorn app.main:app --reload")
        return

    # Step 2: Fire fake webhook
    await fire_webhook(args.order_id, args.amount, args.mid, args.key)

    # Step 3: If payment_id given, trigger AI manually
    if args.payment_id:
        await asyncio.sleep(1)
        await trigger_ai_manually(args.payment_id)

    # Step 4: Show updated metrics
    await asyncio.sleep(1)
    await check_metrics()

    print("\n✨ Open the dashboard at http://localhost:3000 to see the AI in action!\n")


if __name__ == "__main__":
    asyncio.run(main())
