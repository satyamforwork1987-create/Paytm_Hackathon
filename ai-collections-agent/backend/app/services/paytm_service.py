"""
Paytm Payment Gateway service wrapper.
All calls use STAGING endpoints (WEBSTAGING) — no real money moves.

Staging base URL: https://securegw-stage.paytm.in
Docs: https://developer.paytm.com/docs/
"""

import json
import uuid
import logging
import httpx
from app.config import settings
from app.utils.paytm_checksum import generate_checksum

logger = logging.getLogger(__name__)

STAGING_BASE = settings.PAYTM_STAGING_BASE


class PaytmService:
    """Async wrapper around Paytm Staging Payment Gateway APIs."""

    def __init__(self):
        self.mid = settings.PAYTM_MID
        self.key = settings.PAYTM_MERCHANT_KEY
        self.website = settings.PAYTM_WEBSITE
        self.callback_url = settings.PAYTM_CALLBACK_URL

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Generate Payment Link
    # ─────────────────────────────────────────────────────────────────────────

    async def generate_payment_link(
        self,
        amount: float,
        customer_email: str,
        customer_mobile: str,
        order_id: str | None = None,
    ) -> dict:
        """
        Generate a Paytm payment link for collection recovery.

        Returns:
            {
                "shortUrl": "https://paytm.me/...",
                "order_id": "ORD_...",
                "status": "SUCCESS"
            }
        """
        order_id = order_id or f"RECOVER_{uuid.uuid4().hex[:12].upper()}"
        amount_str = f"{amount:.2f}"

        params = {
            "MID": self.mid,
            "ORDER_ID": order_id,
            "CUST_ID": customer_email,
            "MOBILE_NO": customer_mobile,
            "EMAIL": customer_email,
            "TXN_AMOUNT": amount_str,
            "CHANNEL_ID": "WEB",
            "WEBSITE": self.website,
            "CALLBACK_URL": self.callback_url,
            "INDUSTRY_TYPE_ID": "Retail",
        }

        checksum = generate_checksum(params, self.key)
        params["CHECKSUMHASH"] = checksum

        url = f"{STAGING_BASE}/theia/api/v1/generateLink"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=params)
            resp.raise_for_status()
            data = resp.json()

        logger.info("Payment link generated: order_id=%s", order_id)
        return {
            "shortUrl": data.get("body", {}).get("shortUrl", f"https://paytm.me/test/{order_id}"),
            "order_id": order_id,
            "status": data.get("body", {}).get("resultInfo", {}).get("resultStatus", "PENDING"),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Initiate Refund
    # ─────────────────────────────────────────────────────────────────────────

    async def initiate_refund(
        self,
        order_id: str,
        amount: float,
        reason: str = "Customer requested",
    ) -> dict:
        """
        Initiate a refund for an already-successful transaction.

        Returns:
            { "refund_id": "...", "status": "PENDING" }
        """
        ref_id = f"REFUND_{uuid.uuid4().hex[:10].upper()}"
        amount_str = f"{amount:.2f}"

        params = {
            "MID": self.mid,
            "ORDERID": order_id,
            "REFID": ref_id,
            "TXNTYPE": "REFUND",
            "REFUNDAMOUNT": amount_str,
        }

        checksum = generate_checksum(params, self.key)
        params["CHECKSUMHASH"] = checksum

        url = f"{STAGING_BASE}/v2/process/refund/initiatePayout"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=params)
            resp.raise_for_status()
            data = resp.json()

        logger.info("Refund initiated: order_id=%s refund_id=%s", order_id, ref_id)
        return {
            "refund_id": ref_id,
            "status": data.get("STATUS", "PENDING"),
            "reason": reason,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Check Transaction Status
    # ─────────────────────────────────────────────────────────────────────────

    async def check_transaction_status(self, order_id: str) -> dict:
        """
        Poll Paytm to check current transaction status.

        Returns:
            { "status": "TXN_SUCCESS" | "TXN_FAILURE" | "PENDING", "txn_id": "...", "amount": "..." }
        """
        params = {
            "MID": self.mid,
            "ORDERID": order_id,
        }

        checksum = generate_checksum(params, self.key)
        params["CHECKSUMHASH"] = checksum

        url = f"{STAGING_BASE}/order/status"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=params)
            resp.raise_for_status()
            data = resp.json()

        status = data.get("STATUS", "PENDING")
        logger.info("Transaction status check: order_id=%s status=%s", order_id, status)
        return {
            "status": status,
            "txn_id": data.get("TXNID"),
            "amount": data.get("TXNAMOUNT"),
            "resp_msg": data.get("RESPMSG"),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Retry Payment (generate new link for same amount)
    # ─────────────────────────────────────────────────────────────────────────

    async def retry_payment(
        self, amount: float, customer_email: str, customer_mobile: str, original_order_id: str
    ) -> dict:
        """Create a fresh payment link for an auto-retry scenario."""
        new_order_id = f"RETRY_{original_order_id[:8]}_{uuid.uuid4().hex[:6].upper()}"
        return await self.generate_payment_link(amount, customer_email, customer_mobile, new_order_id)


paytm_service = PaytmService()
