# Test findings & suspected bugs

While writing the test suite against `docs/requirements/09-testing-requirements.md`,
the following behaviours diverged from the spec or from the stated test
expectations. Each is pinned by a test (search for the `TC-*` id) so a future
change is detected. They are **not** part of the contracted behaviour and must
not be relied upon by the frontend.

## 1. OGM crashes for non-digit order numbers (high impact)

`OrderBack.ogm` (`src/constants/order_back.py:154-161`) does:

```python
ref_numbers = self.orderNumber.ljust(10, "0")
check_digit = int(ref_numbers[:10]) % 97
```

`ljust` only **pads**; it does not strip non-digits. So for the frontend's
invoice-number format `"2026-1"` (the very example used in TC-OGM-1),
`int("2026-10000")` raises `ValueError: invalid literal for int()`.

This is not a corner case: **bill PDF generation calls `order_data.ogm`, so any
bill whose `orderNumber` is not pure digits cannot be printed or sent to
Billit.** Credit notes are unaffected (`ogm` returns `""` for them).

* Pinned by `tests/unit/test_ogm.py::test_ogm_non_digit_order_number_crashes`
  (`@pytest.mark.gap`).
* Worked around in the PDF-content tests by using a digit-only `orderNumber`
  (`"2026000001"`); the crash itself is the test above.

## 2. `to_front()` omits the order totals

Spec §3.5 and TC-BILL-15 / TC-BILL-21 state that `GET /api/bills/{id}` returns
`totalExcl`, `totalVAT`, `totalIncl`. The implementation's `to_front()`
(`src/constants/order_back.py:219-236`) explicitly excludes
`total_excl` / `total_incl` / `total_vat`, so **none of the totals appear in
the response**. The frontend reads `billitSent` and `peppolDeliveryStatus`
(§3.5) but apparently does not rely on the totals from this endpoint.

* Pinned by `tests/api/test_bills.py::test_get_bill_response_omits_totals`
  (`@pytest.mark.gap`). The non-negative/identity checks are done at the model
  level in `test_get_bill_totals_are_non_negative_via_model` and in
  `tests/unit/test_totals.py`.

## 3. `total_vat` is not rounded (floating-point noise)

`OrderBack.total_vat` (`src/constants/order_back.py:140-148`) returns the
**unrounded** difference `_total_incl - _total_excl`, while `total_excl` and
`total_incl` are each rounded to 2 dp. For some multi-rate orders the result
carries float noise, e.g. `31.91999999999996` instead of `31.92`. The spec
identity `totalVAT == totalIncl - totalExcl` still holds *exactly* (same
subtraction), which is what TC-TOTAL-9 asserts.

## 4. Negative totals are unreachable through the API (TC-GAP-6 / TC-NFR-1)

The spec expects a negative calculated total to surface as a `SyncoraError`
(903-905) → 500 via the API. In practice `pre_billit_checks` rejects any line
with `unitPriceExcl < 0` or `quantity <= 0` with a **warning** *before* any
total is ever computed, and `to_front()` excludes the totals anyway. So the
903-905 path is only reachable by constructing an `OrderBack` directly (done in
`tests/unit/test_totals.py::test_total_negative_raises`). Via the API, a
negative-price bill is simply rejected at the gate.

* Pinned by
  `tests/gaps/test_gaps.py::test_negative_total_unreachable_via_api_gated_instead`.

## 5. TC-GAP-1's "None.locked" is not the actual failure path

TC-GAP-1 (update a non-existent bill) is described as "unhandled `None.locked`".
`create_bill` calls `BillModel.get_one(db_id)` first, which raises
`ItemNotFoundError` for a missing id **before** `existing.locked` is ever
reached. So the observable behaviour is still an unhandled 500, but the
exception is `ItemNotFoundError`, not `AttributeError`.

* Pinned by `tests/api/test_bills.py::test_update_nonexistent_bill_is_unhandled`.

## 6. OGM "overflow" is dropped, not kept (TC-OGM-3 [ASSUMPTION])

The spec's [ASSUMPTION] for order numbers longer than 10 chars says "overflow
kept". The implementation uses `ref_numbers[:10]` for the check digit and
`ref_numbers[0:3]/[3:7]/[7:10]` for the formatted groups, so any character
beyond index 9 is **silently dropped** from the OGM (e.g.
`"12345678901"` → `"+++123/4567/89020+++"`, the trailing `1` is lost).

* Pinned by `tests/unit/test_ogm.py::test_ogm_longer_than_ten_chars_drops_overflow`.

## 7. `hasVAT` is the `Undefined` sentinel, not `False`, when `vat_number` is unset

`CustomerBack.hasVAT` uses `ret_def(self.vat_number, bool(self.vat_number))`,
which returns the `Undefined` sentinel when `vat_number` was never provided
rather than `False`. `Undefined` is falsy and is dropped by the
`SyncoraModel` serializer, so for a customer loaded from the Access DB the
field is `False`/`True` (the column is read as `""` or a value). This is a
latent sharp edge rather than a live bug, but worth noting.

## 8. TC-CUS-18 (malformed JSON) is a Flask 4xx, not a structured envelope

TC-CUS-18 expects a "structured error, not a 500 traceback". A non-JSON body is
rejected by Flask with `415 Unsupported Media Type` (or `400`), which is indeed
not a 500, but it is also **not** the project's JSON `ResponseMessage`
envelope. No route-level handler converts it.

* Pinned by `tests/api/test_customers.py::test_create_customer_malformed_body_is_not_500`
  (asserts `status_code in (400, 415)`).

## 9. Updating a non-existent customer silently creates it (TC-CUS-25)

`update_customer` has no existence check; `CustomerModel.update` upserts, so
`PUT /api/customers/{unknown}` returns `{status:"success"}` and a new row
appears. Documented as current behaviour (no referential/not-found guard).

## 10. `GET /api/customers/{id}` returns a JSON string, not a Flask JSON response

`get_customer` returns `customer.to_front()` which is `json.dumps(...)` (a
`str`), so the route returns it with `Content-Type: text/html`, not
`application/json`. This is the known TC-GAP-11; confirmed and pinned by
`tests/gaps/test_gaps.py::test_get_customer_response_is_not_json_content_type`.
