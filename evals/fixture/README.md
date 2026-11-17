# depot

Order fulfilment backend for a small online shop. Python standard library only, SQLite storage.

## Layout

- `depot/db.py`: schema and connection helper.
- `depot/orders.py`, `depot/webhooks.py`, `depot/fulfilment.py`: the order path.
- `depot/api.py`: JSON shapes served to clients.
- `depot/checkout.py`: the web checkout flow, kept in the session.
- `depot/jobs.py`: background job runner (label printing, export).
- `depot/uploads.py`: chunked upload of product images.
- `depot/tickets.py`: support tickets.
- `depot/prefs.py`, `depot/banner.py`: account preferences and the promo banner.

## Who depends on what

- The mobile app (released, about 9,000 installs) reads `status` from `api.order_json` and
  switches on the strings `pending`, `paid`, `shipped`, `refunded`, `cancelled`.
- The finance export reads the `orders` table directly every night: `status`, `paid_at`,
  `refunded_at`, `total_cents`.
- The payment provider calls `webhooks.payment_succeeded` and `webhooks.refund_issued`.
  It retries, and it can deliver events minutes late or out of order.
- The warehouse runs `fulfilment.ship_ready_orders` every ten minutes.

## Tests

```
python3 -m unittest discover -s tests
```
