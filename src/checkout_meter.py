"""Runnable reconciliation example for e-commerce usage billing."""

from __future__ import annotations

from decimal import Decimal

from infrai_usage_client import InfraiUsageClient
from usage_ledger import OrderStage, UsageRecord, invoice_customer


def demo_records() -> list[UsageRecord]:
    return [
        UsageRecord("cus_elm", "ord_100", OrderStage.CHECKOUT, 1),
        UsageRecord("cus_elm", "ord_100", OrderStage.FULFILLMENT, 2),
        UsageRecord("cus_elm", "ord_100", OrderStage.RECEIPT, 1),
        UsageRecord("cus_elm", "ord_100", OrderStage.CUSTOMER_UPDATE, 1),
    ]


def main() -> None:
    client = InfraiUsageClient()
    account_total = client.usage()
    account_series = client.usage_timeseries()
    invoice = invoice_customer(demo_records(), "cus_elm", Decimal("0.01"))
    print(f"customer={invoice.customer_id} billable_requests={invoice.billable_requests}")
    print(f"decision={invoice.decision} amount_usd={invoice.amount_usd}")
    print(f"account_usage={account_total}")
    print(f"account_usage_timeseries={account_series}")


if __name__ == "__main__":
    main()
