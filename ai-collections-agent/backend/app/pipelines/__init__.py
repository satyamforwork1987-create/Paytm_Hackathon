"""Pipelines package."""

from app.pipelines.generate_synthetic import run_pipeline as generate_all
from app.pipelines.ingest_customers import ingest_customer_data
from app.pipelines.ingest_payments import ingest_payment_events

__all__ = ["generate_all", "ingest_customer_data", "ingest_payment_events"]
