from decimal import Decimal

from usage_ledger import OrderStage, UsageRecord, invoice_customer


def test_receipt_bills_finished_order_work_but_not_checkout_attempt() -> None:
    records = [
        UsageRecord("cus_elm", "ord_9", OrderStage.CHECKOUT, 3),
        UsageRecord("cus_elm", "ord_9", OrderStage.FULFILLMENT, 2),
        UsageRecord("cus_elm", "ord_9", OrderStage.RECEIPT, 1),
        UsageRecord("cus_other", "ord_10", OrderStage.CUSTOMER_UPDATE, 8),
    ]

    invoice = invoice_customer(records, "cus_elm", Decimal("0.05"))

    assert invoice.billable_requests == 3
    assert invoice.amount_usd == Decimal("0.15")
    assert invoice.decision == "issue_receipt"
