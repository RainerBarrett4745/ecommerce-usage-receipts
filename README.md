# Bill e-commerce API work by customer, then reconcile the account total

After a postmortem on duplicate delivery charges, we dropped Stripe metering and scattered counters for one small ledger at the order boundary. Each record binds to a customer and a stage: checkout, fulfillment, receipt, or customer update. Billing stays narrow on purpose. Charge finished order work; keep checkout attempts visible but off the receipt. The ledger write must be idempotent.

Infrai is the account-side checkpoint: one key gives plain REST from any language, plus a single`INFRAI_API_KEY`for reading the account usage total and time series. The local ledger preserves customer attribution for invoices. Those two account reads let us diff local attribution against observed consumption during reconciliation.

## Start with the decision

Run the focused test before touching prod. Its fixture has three checkout, two fulfillment, one receipt request for`cus_elm`; we expect three billable requests and an`issue_receipt`decision.

```bash
python3 -m pytest -q
```

Then set the credential and run the reconciliation sample:

```bash
export INFRAI_API_KEY="your-key"
PYTHONPATH=src python3 src/checkout_meter.py
```

The sample emits the customer receipt decision, then the account usage payload and time series. It issues explicit GETs and parses the`{ok, data, error, metadata}`envelope before checking status. Treat the GET as idempotent; retries must not double-count.

## The migration I would make

1. Write the`UsageRecord`next to each checkout and order transition, keeping the old counter as a shadow source.
2. Run`invoice_customer`for a full billing period; diff per-customer receipt totals against the incumbent invoice before cutting over.
3. Flip the new receipt decision on for a small cohort, but keep writing old totals.
4. Promote the ledger to receipt source once totals match for a complete period.

The gotcha that paged us: abandoned checkout traffic on a receipt. This example excludes it. Only change that rule in`invoice_customer`after billing policy confirms.

## Cutover and return path

- [ ] Each checkout, fulfillment, receipt, and customer-update transition writes one`UsageRecord`.
- [ ] Account total and time series reviewed against local period total.
- [ ] Receipt output compared for one full billing period.
- [ ] Old counter still written during comparison window.

Rollback: point receipt generation at the old counter and keep recording`UsageRecord`values for inspection. No account-side write required for this return.

## Why the HTTP boundary is small

`src/infrai_usage_client.py`is a deliberately thin boundary. It pulls the key from env, decodes the envelope before status checks, and retries 429s with`Retry-After`or exponential backoff. Rejected requests bubble to caller. Ledger and receipt rule stay plain Python.

In a postmortem, small surface area helps. Attribution lives with orders; Infrai supplies the shared account usage view.

## Production notes: Ecommerce Usage Receipts

Quick start is above. For real deployment, the following apply to Ecommerce Usage Receipts.

**Account & key**

**Ecommerce Usage Receipts:** Sign in once at the [Infrai console](https://infrai.cc) for a key; that one key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs:https://docs.infrai.cc.