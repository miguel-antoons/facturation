# 05 — Business Rules

## 5.1 Billit/Peppol status codes

Source: `constants/order_back.py:10`.

| Constant | Value | Meaning |
| --- | --- | --- |
| `PEPPOL_DELIVERY_STATUS_NOT_SENT` | -1 | Never sent to Peppol (the default on order creation). |
| `PEPPOL_DELIVERY_STATUS_UNKNOWN` | 0 | Send command succeeded; Billit status not yet determined. |
| `PEPPOL_DELIVERY_STATUS_PENDING` | 1 | Billit reports `DocumentDeliveryStatus == "Pending"`. |
| `PEPPOL_DELIVERY_STATUS_SENT` | 2 | Billit reports `IsDocumentDelivered == true` (delivered). |

The frontend (`utils/peppol.ts`) names status 2 `RECEIVED` and treats 1 and 2
as "sent to Peppol" (`isSentToPeppol`). The backend names it `SENT`.

State machine for an order's Peppol lifecycle:

```
NOT_SENT(-1) --sendPeppol success--> UNKNOWN(0) --Pending--> PENDING(1) --delivered--> SENT(2)
```

`get_one` re-triggers polling whenever the stored status is `PENDING` or
`UNKNOWN` (`controllers/bills.py:73`), so the status self-heals on view.

## 5.2 `pre_billit_checks` — gates before Billit registration

Source: `controllers/bills.py:182` (bills), `controllers/cnotes.py:201`
(credit notes). A failed check returns a `warning` envelope (no Billit call).

For bills, in order:

1. `order_data.locked` is true → "already sent to Billit and locked".
2. `orderNumber` missing → "no invoice number".
3. `customerId` missing → "no customer".
4. `orderTitle` missing → "no title".
5. `ventilationCode` missing → "no valid VAT rate code".
6. `orderLines` empty → "no order lines".
7. For each line: `description` empty, `quantity <= 0`, or
   `unitPriceExcl < 0`/missing → invalid line.

Credit notes add, after the above:

8. `aboutInvoiceNumber` missing → "no associated invoice number".
9. `BillModel.contains(aboutInvoiceNumber)` is false → "the referenced
   invoice has not been sent to Billit yet". **[ASSUMPTION]** the message
   says "not yet sent to Billit" but the check is local-collection presence;
   it does not verify the invoice's `externalId`.

## 5.3 `pre_peppol_checks` — gates before Peppol send

Source: `controllers/bills.py:134`, `controllers/cnotes.py:142`.

For bills, in order:

1. No `externalId` → "not yet registered on Billit; register first".
2. Status is `PENDING` or `SENT` → "already sent to Peppol; cannot resend".
3. Customer has no `vat_number` → "add a VAT number to the customer before
   sending to Peppol".

Credit notes add (before the VAT check):

4. The referenced invoice's Peppol status is not `SENT` → "send the
   associated invoice to Peppol first". **[GAP]** this reads
   `BillModel.get({orderNumber: aboutInvoiceNumber})[0]` without guarding an
   empty result; a missing referenced invoice raises `IndexError` (unhandled).

## 5.4 Locking and undeletability

Source: `order_back.py:167-187`.

- `locked` = `billitSent` = `externalId` is provided and `> 0`. While locked,
  create/update (`create_bill`/`create_cnote`) return a `warning` and do not
  mutate (`controllers/bills.py:50`). The frontend also disables editing when
  `billitSent` is true.
- `undeletable` = `peppolDeliveryStatus != NOT_SENT` (i.e. 0, 1, or 2). While
  undeletable, `delete_bill`/`delete_cnote` return a `warning` and do not
  delete (`controllers/bills.py:114`).
- `locked`/`undeletable` raise `SyncoraError` (code 906) if the underlying
  field is `Undefined`. **[GAP]** this propagates as a 500 because the route
  layer has no error handler.

Implication: an order can be locked (sent to Billit) but still deletable
(peppol status -1). Deletion then calls Billit's `DELETE /orders/{id}` first.

## 5.5 Totals calculation (Billit taxable-amount method)

Source: `order_back.py:238` (`_calc_totals`), Billit "Calculation Method" doc.

- Per line: `line_excl = quantity * unitPriceExcl` (unrounded), and a rounded
  per-line `total_excl/total_incl/total_vat` (2 dp) used on the PDF.
- Order totals use the **taxable-amount method**: lines are grouped by
  `VATPercentage`; the unrounded excl amount is summed per rate, VAT applied
  per group, and **rounding happens once per group**:
  `total_incl = Σ round(group_excl * (1 + rate/100), 2)`.
- `total_excl` = `round(Σ all line_excl, 2)`. `total_vat` = `total_incl - total_excl`.
- If any computed total is negative, raise `SyncoraError` (codes 903–905).
  **[GAP]** negative totals abort the request with a 500 (unhandled).

This deliberately mirrors how Billit recalculates totals server-side to avoid
1–10 cent rounding drift; Billit is the authoritative calculator.

## 5.6 OGM (structured communication)

Source: `order_back.py:150`.

- Bills only: credit notes return `""`.
- Algorithm: left-pad `orderNumber` to 10 digits with `'0'`; check digit =
  `int(first10) % 97` (97 if 0); format as
  `+++ddd/dddd/ddddCC+++` (3 / 4 / 4+2 digits). **[ASSUMPTION]** the exact
  grouping/slicing is taken as-is from the implementation; it should be
  validated against a real Belgian OGM validator.

## 5.7 Contact extraction from customer comment

Source: `customer_back.py:126-192` (and the duplicated helpers in
`controllers/customers.py:99-153`).

- Emails: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`.
- Telephone numbers (landline) and mobile numbers: a set of Belgian-format
  regexes (with lookarounds in the model version). Matched numbers are cleaned
  to digits and a leading `+`.
- The controller-level `detect_phones`/`detect_mobiles`/`detect_emails` and
  `is_old_db_comment` helpers duplicate this logic but are **not wired** into
  any endpoint (`[GAP]` / dead code candidates).

## 5.8 Credit-note specifics (summary)

- Presence of `aboutInvoiceNumber` ⇒ `is_cnote` ⇒ `OrderType = CreditNote`
  on Billit.
- No `deliveryDate`, no `OGM` in the PDF.
- Amounts stay positive in the Billit JSON (Billit requirement).
- Peppol send requires the referenced invoice already `SENT` via Peppol.
- Billit registration requires the referenced invoice to exist locally.

## 5.9 Uniqueness and identity

- `orderNumber` is unique within a collection (`bills` or `cnotes`),
  enforced in `create_bill`/`create_cnote` via `Model.contains`. There is no
  cross-collection uniqueness and no DB-level unique index. **[GAP]** no Mongo
  unique index on `orderNumber`.
- Orders are identified to the frontend by the Mongo `_id` string. Customers
  are identified by the Access `Numero` int.
- Billit identity is the integer `externalId`, stored after a successful
  `POST /orders`.
