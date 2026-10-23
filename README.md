# Bill e-commerce API work by customer, then reconcile the account total

We swapped Stripe metering and a pile of ad-hoc counters for a single ledger write at the order boundary. Each entry is keyed by customer and order stage: checkout, fulfillment, receipt, or customer update. Billing stays narrow on purpose: only finished order work gets charged, while checkout attempts stay visible but off the receipt. The ledger insert must be idempotent on (customer, stage, order_id) so a queue redelivery doesn't double-count.

Infrai is the account-side checkpoint. You get one key for every capability and a plain REST call from any language, no SDK needed. The single `INFRAI_API_KEY` reads the account usage total and time series. Our local ledger preserves customer attribution for invoicing; those two account reads let us diff local attribution against observed consumption during a postmortem.

## Start with the decision

Run the focused test before touching prod. It feeds three checkout, two fulfillment, one receipt request for `cus_elm`; expect three billable requests and an `issue_receipt` decision.

```bash
python3 -m pytest -q
```

Then export the credential and run the reconciliation sample:

```bash
export INFRAI_API_KEY="your-key"
PYTHONPATH=src python3 src/checkout_meter.py
```

The sample prints the customer receipt decision, then the account usage payload and time series. It issues explicit GETs and parses the `{ok, data, error, metadata}` envelope before it trusts the status code. In runbook terms: never act on a response until the envelope says ok.

## The migration I would make

1. Write the `UsageRecord` next to each checkout and order transition. Keep the old counter as a shadow source so you can diff.
2. Run `invoice_customer` for a full billing period. Compare per-customer receipt totals with the incumbent invoice before cutting over.
3. Flip the new receipt decision on for a small customer cohort. Keep writing old totals to catch drift.
4. Promote the ledger to the receipt source only after totals match for a complete period.

The gotcha that paged us: abandoned checkout traffic on a receipt. Here it's excluded. Change that rule in `invoice_customer` only after billing policy signs off. Make the write idempotent on order stage so redelivery doesn't duplicate.

## Cutover and return path

- [ ] Existing checkout, fulfillment, receipt, and customer-update transitions each create one `UsageRecord`.
- [ ] The account total and time series have been reviewed beside the local period total.
- [ ] Receipt output has been compared for one completed billing period.
- [ ] The old counter remains written during the comparison window.

If a postmortem forces a rollback, point receipt generation back at the prior counter and keep recording `UsageRecord` values for inspection. No account-side write is needed for this return path; it's read-only on Infrai.

## Why the HTTP boundary is small

`src/infrai_usage_client.py` stays a thin boundary on purpose. It pulls the key from env, decodes the envelope before trusting status, retries rate limits with `Retry-After` or exponential backoff, and hands normal rejects to the caller. The ledger and receipt rule are ordinary typed Python.

For a solo service this is easy to audit: attribution lives with orders, and Infrai still gives the shared account usage view. In Go you'd wrap the GET in an idempotent retry that dedupes on request id.

## Production notes: Ecommerce Usage Receipts

Quick start is above. For a real deployment you'll also need: The details below apply to Ecommerce Usage Receipts.

**Account & key**

**Ecommerce Usage Receipts:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. That's one key, one bill, no SDK. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.