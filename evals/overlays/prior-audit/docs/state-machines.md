# Implicit state machines in depot

Audit from last week. Nothing has been converted yet.

| Machine | Location | Risk | Recommendation |
|---|---|---|---|
| Order lifecycle | depot/orders.py, webhooks.py, fulfilment.py, api.py | High (money) | Convert |
| Job lifecycle | depot/jobs.py | Medium | Convert |
| Checkout flow | depot/checkout.py | Medium | Convert lightly |
| Upload lifecycle | depot/uploads.py | Medium | Convert lightly |
| Tickets | depot/tickets.py | None | Leave alone: already explicit |
| Prefs, banner | depot/prefs.py, banner.py | None | Leave alone: independent flags |

## Order lifecycle

`orders.status` is written from four places with no shared check: `orders.cancel_order`,
`webhooks.payment_succeeded`, `webhooks.refund_issued`, `fulfilment.ship_ready_orders`.
The four timestamps encode the same lifecycle a second time.

Reachable bad states:

- Refunded order ships. `refund_issued` leaves `paid_at` set; `ship_ready_orders` selects on
  `paid_at IS NOT NULL AND shipped_at IS NULL`, so the next pass ships it and sets `shipped`.
- Cancelled order becomes paid and ships. A late `payment_succeeded` after `cancel_order`
  sets `status = 'paid'` with `cancelled_at` still set; the next pass ships it.
- Shipped order goes back to `paid`. A retried `payment_succeeded` after shipping overwrites
  the status; the API then offers `can_cancel`, and `cancel_order` raises.

## Job lifecycle

Three booleans (`running`, `failed`, `done`) on `jobs`.

- `retry` sets `running = 1` and leaves `failed = 1`; `complete` then leaves `done = 1` and
  `failed = 1`, and `summary` counts the job as both.
- `cancel` sets `running = 0`, which is the queued state, so `next_job` hands it out again.

## Checkout flow

`session["step"]` is set by each handler and never checked.

- `submit_payment` works without an address.
- `confirm` twice creates two orders.

## Upload lifecycle

State is implied by part count, a `.lock` file, and a `.bin` file.

- A crash in `assemble` leaves the lock; `status` reports `assembling` forever.
- `add_part` after the last part makes the count exceed `expected_parts`; `status` reports
  `uploading` and `assemble` refuses.
