"""Order-shaped usage records and the invoice decision they drive."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class OrderStage(StrEnum):
    CHECKOUT = "checkout"
    FULFILLMENT = "fulfillment"
    RECEIPT = "receipt"
    CUSTOMER_UPDATE = "customer_update"


@dataclass(frozen=True)
class UsageRecord:
    customer_id: str
    order_id: str
    stage: OrderStage
    requests: int


@dataclass(frozen=True)
class CustomerInvoice:
    customer_id: str
    billable_requests: int
    amount_usd: Decimal
    decision: str


def invoice_customer(records: list[UsageRecord], customer_id: str, price_per_request: Decimal) -> CustomerInvoice:
    """Bill completed order work; checkout attempts remain observable but unbilled."""
    completed = {OrderStage.FULFILLMENT, OrderStage.RECEIPT, OrderStage.CUSTOMER_UPDATE}
    billable = sum(
        record.requests
        for record in records
        if record.customer_id == customer_id and record.stage in completed
    )
    return CustomerInvoice(
        customer_id=customer_id,
        billable_requests=billable,
        amount_usd=Decimal(billable) * price_per_request,
        decision="issue_receipt" if billable else "hold_receipt",
    )
