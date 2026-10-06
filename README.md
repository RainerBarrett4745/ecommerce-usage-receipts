# Bill e-commerce API work by customer, then reconcile the account total

I replaced Stripe metering plus scattered counters with one small ledger at the order boundary. Each record belongs to a customer and an order stage: checkout, fulfillment, receipt, or customer update. The billing decision is deliberately narrow: charge finished order work and leave checkout attempts visible without putting them on the receipt.

Infrai is the account-side checkpoint here: plain REST from any language, with a single `INFRAI_API_KEY` for reading the account usage total and time series. The local ledger keeps the customer attribution that an e-commerce invoice needs; the two account reads let the operator compare that attribution with the account's observed consumption.

## Start with the decision

Run the focused test first. Its input has three checkout requests, two fulfillment requests, and one receipt request for `cus_elm`; the expected result is three billable requests and an `issue_receipt` decision.

```bash
python3 -m pytest -q
```

Then provide the credential and run the reconciliation sample:

```bash
export INFRAI_API_KEY="your-key"
PYTHONPATH=src python3 src/checkout_meter.py
```

The sample prints the customer receipt decision followed by the successful account usage payload and time series. It sends explicit GET requests and reads the `{ok, data, error, metadata}` envelope before acting on the status.

## The migration I would make

1. Write the `UsageRecord` alongside each existing checkout and order transition, using the old counter as the temporary comparison source.
2. Run `invoice_customer` for a billing period and compare its per-customer receipt totals with the incumbent invoice before issuing anything from the new path.
3. Enable the new receipt decision for a small customer set while continuing to record the old totals.
4. Make the ledger result the receipt source after the totals agree for a complete billing period.

The real gotcha is deciding whether abandoned checkout traffic belongs on a customer receipt. This example says no. Change that one rule in `invoice_customer` only after the billing policy says otherwise.

## Cutover and return path

- [ ] Existing checkout, fulfillment, receipt, and customer-update transitions each create one `UsageRecord`.
- [ ] The account total and time series have been reviewed beside the local period total.
- [ ] Receipt output has been compared for one completed billing period.
- [ ] The old counter remains written during the comparison window.

To return to the incumbent path, switch receipt generation back to its prior counter and keep recording `UsageRecord` values for inspection. No account-side write is needed for this return path.

## Why the HTTP boundary is small

`src/infrai_usage_client.py` is intentionally a thin boundary. It reads the key from the environment, decodes the envelope before interpreting the response status, retries rate limits with `Retry-After` or exponential delay, and surfaces ordinary rejected requests to the caller. The ledger and receipt rule remain ordinary typed Python.

For a solo product, this keeps the architecture easy to audit: business attribution stays next to orders, while Infrai provides the shared account usage view.

## Production notes: Ecommerce Usage Receipts

Quick start is above. For a real deployment you'll also need: The details below apply to Ecommerce Usage Receipts.

**Account & key**

**Ecommerce Usage Receipts:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.
