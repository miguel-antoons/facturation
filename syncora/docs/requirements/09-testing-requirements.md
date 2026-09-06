# 09 — Testing Requirements

This document defines the **test requirements** for the Syncora backend. It is
derived from `01`–`08` and is written to be **implementation-agnostic where
possible**: tests assert on the observable REST contract, the response envelope
shape, persisted state, and externally visible side effects (Billit HTTP calls,
PDF bytes), not on internal class/method names. Where a requirement is inherently
about internal behaviour (e.g. the taxable-amount rounding method), the test is
expressed in terms of the observable numeric outcome.

Each test case has a stable ID `TC-<area>-<n>` and traces to the requirement
ID(s) it covers (`FR-*`, `API-*`, `NFR-*`). Cases are classified:

- **Sunny** — the happy path; the operation succeeds and produces the documented
  success response.
- **Rainy** — invalid input, missing prerequisites, or an external failure; the
  operation is rejected with a documented `error`/`warning` envelope (never a
  raw 500 unless the requirement explicitly marks it a `[GAP]`).
- **Edge** — boundary values, empty inputs, single-element collections, and
  off-by-one / rounding cases.

A separate **§21 Known-gap regression tests** captures behaviours the
requirements flag as `[GAP]`; these tests pin the *current* (deficient) behaviour
so regressions are detected and the gap can be closed deliberately.

---

## 10. Testing strategy

### 10.1 Layers

| Layer | What it exercises | Isolation |
| --- | --- | --- |
| **API contract tests** | `route → controller → model` through the Flask test client (`app.test_client()`). | MongoDB replaced by an in-memory `mongomock`/fake; MS Access replaced by a fake `CustomerModel`/connector; Billit HTTP replaced by a `requests` mock. These are the primary tests; they assert only on HTTP status, JSON body, headers, and the calls made to the fakes. |
| **Pure-logic unit tests** | Totals, OGM, address split, contact extraction, date formatting, `Undefined` semantics. | No Flask, no DB, no network. Construct `OrderBack`/`CustomerBack` directly. |
| **Integration smoke tests** (optional) | A real `mongomock` round-trip for `OrderModel`; a real WeasyPrint render against the shipped templates. | Skipped in CI if WeasyPrint/JVM system deps are unavailable; marked `@pytest.mark.integration`. |

### 10.2 Implementation-agnosticism rules

1. Tests must not import private helpers (e.g. `pre_billit_checks`) to assert
   results. They POST to the endpoint and assert on the JSON envelope.
2. Tests must not assert on exact French warning *wording* (the strings are not
   part of the contract); they assert on the `status` field (`"success"` /
   `"error"` / `"warning"`) and, where a requirement names a distinct outcome,
   on the presence of a `message` key and the HTTP path taken (e.g. that no
   Billit call was made).
3. Tests assert on the **shape** of `to_front()` (which fields are present /
   absent), not on the internal `exclude={...}` set.
4. Billit interactions are asserted via a fake that records outbound requests
   (method, URL, headers, JSON body); tests never hit the network.
5. PDF tests assert on `Content-Type`, `Content-Disposition`, non-empty body,
   and (for templated PDFs) text fragments in the extracted PDF text — not on
   byte equality.

### 10.3 Fixtures

- `bill_payload`, `cnote_payload`, `customer_payload` — minimal valid request
  bodies matching `03-api-specification.md` §3.1/§3.2/§3.3.
- `existing_bill`, `locked_bill`, `undeletable_bill`, `sent_peppol_bill` —
  orders seeded in the fake Mongo with `externalId`/`peppolDeliveryStatus` set
  to exercise each state.
- `billit_fake` — records `POST /orders`, `POST /orders/commands/send`,
  `DELETE /orders/{id}`, `GET /orders/{id}` and returns configurable status/body.
- `customer_fake` — a dict keyed by `Numero` so list/get/create/update/delete
  behave like the Access layer without a JVM.

---

## 11. Customers (API-CUS-1..5, FR-CUS-1..10)

### 11.1 List customers — `GET /api/customers`

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-CUS-1 | Sunny | DB has several customers | FR-CUS-1, API-CUS-1 | 200; JSON array; each item has exactly `{id, name, surname, company, postal_code, city, mobileNumbers, telephoneNumbers, hasVAT, hasEmail}`; `comment`, `address`, `street`, `number`, `vat_number`, `language` are **not** present. |
| TC-CUS-2 | Edge | DB is empty | FR-CUS-1 | 200; `[]`. |
| TC-CUS-3 | Edge | A customer has no comment | FR-CUS-8 | `hasEmail` is `false`, `mobileNumbers`/`telephoneNumbers` are `[]`. |
| TC-CUS-4 | Edge | A customer comment contains an email and a mobile number | FR-CUS-8, FR-CUS-9 | `hasEmail` true; `mobileNumbers` is a non-empty list of digit-stripped strings; `hasVAT` reflects the presence of `vat_number`. |
| TC-CUS-5 | Edge | A customer with a VAT number but no email | FR-CUS-9 | `hasVAT` true, `hasEmail` false. |

### 11.2 Get one customer — `GET /api/customers/{id}`

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-CUS-6 | Sunny | Existing id | FR-CUS-2, API-CUS-3 | 200; body has stored fields plus computed `street`, `number`; does **not** include `address`, `emails`, `telephoneNumbers`, `mobileNumbers`, `id`. |
| TC-CUS-7 | Sunny | Customer whose `Adresse` is `"Rue X, 12"` | FR-CUS-2 | `street == "Rue X"`, `number == "12"`. |
| TC-CUS-8 | Edge | `Adresse` with no comma (street only) | FR-CUS-2 | `street` = whole string, `number` = `""`. |
| TC-CUS-9 | Edge | `Adresse` with multiple commas | FR-CUS-2 | `street` = first part, `number` = remainder joined. |
| TC-CUS-10 | Edge | `Adresse` empty/missing | FR-CUS-2 | `street`/`number` are empty strings (not null). |
| TC-CUS-11 | Rainy | Non-existent id | API-CUS-3, NFR-REL-2 | Returns a structured error (current impl: unhandled — see §21 gap). |
| TC-CUS-12 | Rainy | Non-integer path segment | API-CUS-3 | 404 before controller (Flask `int` converter). |

### 11.3 Create customer — `POST /api/customers`

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-CUS-13 | Sunny | Valid body with `street`/`number` (no `address`) | FR-CUS-3, FR-CUS-6, API-CUS-2 | 200; `{status:"success", id:<new Numero>}`; persisted `Adresse` equals `"<street> , <number>"`. |
| TC-CUS-14 | Sunny | Body includes only `company` | FR-CUS-3 | Success. |
| TC-CUS-15 | Sunny | `language: "FR"` | FR-CUS-7 | Persisted `Langue` is `"fr"`. |
| TC-CUS-16 | Sunny | `language: "FR"` and `"nl"` | FR-CUS-7 | Both stored lowercased. |
| TC-CUS-17 | Rainy | None of `name`, `surname`, `company` provided | FR-CUS-3 | Returns a controlled error envelope (current impl raises — see §21 gap); no row inserted. |
| TC-CUS-18 | Rainy | Empty body / malformed JSON | API-CUS-2 | Structured error, not a 500 traceback. |
| TC-CUS-19 | Edge | `address` provided explicitly overrides `street`/`number` assembly | FR-CUS-6 | `address` is persisted as-is. |
| TC-CUS-20 | Edge | `street` provided, `number` omitted | FR-CUS-6 | `Adresse` assembled as `"<street> , "`. |
| TC-CUS-21 | Edge | Returned `id` is the new AutoNumber (`MAX(Numero)`) | FR-CUS-3 | `id` reflects the inserted row's id. |

### 11.4 Update customer — `PUT /api/customers/{id}`

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-CUS-22 | Sunny | Update fields on existing customer | FR-CUS-4, API-CUS-4 | 200; `{status:"success", id:<path id>}`; row updated. |
| TC-CUS-23 | Edge | Body omits `id` | FR-CUS-4 | Persisted id is forced to the path id (body cannot override). |
| TC-CUS-24 | Edge | Body includes a different `id` | FR-CUS-4 | Persisted id is the path id, not the body id. |
| TC-CUS-25 | Rainy | Non-existent id | API-CUS-4 | Operation does not crash; documented behaviour (no "not found" check today — see §21 gap). |

### 11.5 Delete customer — `DELETE /api/customers/{id}`

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-CUS-26 | Sunny | Delete existing customer | FR-CUS-5, API-CUS-5 | 200; `{status:"success", id:<path id>}`; row removed. |
| TC-CUS-27 | Edge | Delete a customer referenced by existing bills | FR-CUS-5 | Documented behaviour (no referential guard today — see §21 gap). |

---

## 12. Bills (API-BILL-1..7, FR-BILL-1..8)

### 12.1 List bills — `GET /api/bills`

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-BILL-1 | Sunny | Several bills, customers exist | FR-BILL-1, API-BILL-1 | 200; array of short rows `{orderId, customerName, orderNumber, orderDate, orderTitle}`. |
| TC-BILL-2 | Sunny | `customerName` formatting | FR-BILL-1 | `customerName == "name surname, company"` when company present; `"name surname"` when company empty. |
| TC-BILL-3 | Edge | No bills | FR-BILL-1 | 200; `[]`. |
| TC-BILL-4 | Rainy | A bill references a non-existent customer | FR-BILL-1 | Structured error, not a 500 (current impl: unhandled — see §21 gap). |

### 12.2 Create / update bill — `POST` / `PUT /api/bills[/{id}]`

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-BILL-5 | Sunny | Create with minimal valid body, no `bill_id` ("0") | FR-BILL-2, API-BILL-2 | 200; `{status:"success", id:<mongo_id>}`; persisted doc has `externalId==0`, `peppolDeliveryStatus==-1`. |
| TC-BILL-6 | Sunny | Create with `orderNumber` null/empty | API-BILL-2 | Success (orderNumber may be empty on create per §3.1). |
| TC-BILL-7 | Sunny | Update existing unlocked bill, same orderNumber | FR-BILL-3, API-BILL-4 | Success; row updated; no duplicate error. |
| TC-BILL-8 | Sunny | Update existing bill, change orderNumber to a free one | FR-BILL-3 | Success. |
| TC-BILL-9 | Rainy | Create with `orderNumber` already used by another bill | FR-BILL-3 | `{status:"error", message:...}`; no insert. |
| TC-BILL-10 | Rainy | Update to an `orderNumber` already used by a *different* bill | FR-BILL-3 | `{status:"error", message:...}`; no update. |
| TC-BILL-11 | Rainy | Update a locked bill (`externalId>0`) | FR-BILL-4 | `{status:"warning", message:...}`; row unchanged. |
| TC-BILL-12 | Rainy | Update a non-existent `bill_id` | API-BILL-4 | Structured error (current impl: unhandled `None.locked` — see §21 gap). |
| TC-BILL-13 | Edge | Create with empty `orderLines` list | API-BILL-2 | Documented (create itself does not gate lines; gating is at Billit send — see §14). |
| TC-BILL-14 | Edge | `orderId` returned is a string, not the Mongo `ObjectId` object | FR-BILL-2 | `id` is a string. |

### 12.3 Get one bill — `GET /api/bills/{id}`

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-BILL-15 | Sunny | Existing bill | FR-BILL-5, API-BILL-3 | 200; full `to_front()` shape per §3.5: includes `billitSent`, `peppolDeliveryStatus`, totals, `orderLines` without per-line sub-totals; excludes `orderId`, `externalId`. |
| TC-BILL-16 | Sunny | `peppolDeliveryStatus == PENDING` | FR-BILL-5, FR-POLL-6 | A Peppol status poll is triggered for the bill's `externalId`. |
| TC-BILL-17 | Sunny | `peppolDeliveryStatus == UNKNOWN` | FR-BILL-5, FR-POLL-6 | A poll is triggered. |
| TC-BILL-18 | Edge | `peppolDeliveryStatus == NOT_SENT` | FR-BILL-5 | No poll triggered. |
| TC-BILL-19 | Edge | `peppolDeliveryStatus == SENT` | FR-BILL-5 | No poll triggered. |
| TC-BILL-20 | Rainy | Non-existent id | API-BILL-3, NFR-REL-2 | Structured error (current impl: unhandled — see §21 gap). |
| TC-BILL-21 | Edge | Totals present and non-negative | FR-BILL-5 | `totalExcl`, `totalVAT`, `totalIncl` are numbers; `totalVAT == totalIncl - totalExcl`. |

### 12.4 Delete bill — `DELETE /api/bills/{id}`

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-BILL-22 | Sunny | Delete unregistered bill (`externalId==0`, status -1) | FR-BILL-6, API-BILL-5 | `{status:"success"}`; local doc removed; no Billit call. |
| TC-BILL-23 | Sunny | Delete registered bill (`externalId>0`, status -1) | FR-BILL-6, FR-BILLIT-7 | Billit `DELETE /orders/{externalId}` is called and succeeds (body `true`); local doc removed; `{status:"success"}`. |
| TC-BILL-24 | Rainy | Delete undeletable bill (status 0/1/2) | FR-BILL-6 | `{status:"warning", message:...}`; doc remains; no Billit call. |
| TC-BILL-25 | Rainy | Billit delete fails (non-`true` body) | FR-BILL-6 | Local deletion aborted; an error outcome is returned; local doc remains. |
| TC-BILL-26 | Rainy | Non-existent id | API-BILL-5 | Structured error (current impl: unhandled — see §21 gap). |
| TC-BILL-27 | Edge | Billit delete returns `true` but local delete modifies 0 rows | FR-BILL-6 | `{status:"error"}` (or documented outcome). |

---

## 13. Credit notes (API-CN-1..7, FR-CN-1..6)

Credit notes mirror bills. Only the **deltas** are listed; the bill cases in §12
apply with `cnotes` substituted for `bills` unless overridden here.

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-CN-1 | Sunny | Create cnote with `aboutInvoiceNumber` set | FR-CN-1, API-CN-2 | Success; persisted `aboutInvoiceNumber` present. |
| TC-CN-2 | Sunny | Create bill (no `aboutInvoiceNumber`) | FR-CN-1 | `is_cnote` false (credit-note-specific fields absent). |
| TC-CN-3 | Sunny | Get one cnote | API-CN-3 | `to_front()` includes `aboutInvoiceNumber`; `formatted_delivery_date` empty. |
| TC-CN-4 | Edge | cnote `ogm` is empty | FR-CN-6 | `ogm` returns `""`. |
| TC-CN-5 | Edge | cnote `formatted_delivery_date` is empty even if `deliveryDate` set | FR-CN-6 | Empty string. |
| TC-CN-6 | Rainy | Delete undeletable cnote | API-CN-5 | `{status:"warning"}`; doc remains. |
| TC-CN-7 | Rainy | Update a locked cnote | API-CN-4 | `{status:"warning"}`; row unchanged. |
| TC-CN-8 | Rainy | Duplicate `orderNumber` within `cnotes` | FR-BILL-3 (mirrored) | `{status:"error"}`. |
| TC-CN-9 | Edge | Same `orderNumber` exists in `bills` and `cnotes` | FR-CN-1, §5.9 | Both succeed — uniqueness is per-collection, not cross-collection. |

---

## 14. Billit registration flow (FR-BILLIT-1..7, API-BILL-6, API-CN-6)

`POST /api/bills/sendBillit/{id}` and `POST /api/cnotes/sendBillit/{id}`.

### 14.1 `pre_billit_checks` gates (order is significant)

The checks run **in order**; the first failing check returns a `warning` and
**no Billit call is made**. Each case seeds an order that fails *only* the named
check (all later conditions are valid) and asserts the warning + no outbound
Billit request.

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-BILLIT-1 | Sunny | Valid bill → Billit 200/201 | FR-BILLIT-1..5, API-BILL-6 | `{status:"success"}`; `externalId` persisted as the returned int; order now `locked`. |
| TC-BILLIT-2 | Rainy | Locked bill (`externalId>0`) | FR-BILLIT-1, §5.2.1 | warning; no Billit call. |
| TC-BILLIT-3 | Rainy | `orderNumber` missing/empty | §5.2.2 | warning; no Billit call. |
| TC-BILLIT-4 | Rainy | `customerId` missing | §5.2.3 | warning; no Billit call. |
| TC-BILLIT-5 | Rainy | `orderTitle` missing | §5.2.4 | warning; no Billit call. |
| TC-BILLIT-6 | Rainy | `ventilationCode` missing | §5.2.5 | warning; no Billit call. |
| TC-BILLIT-7 | Rainy | `orderLines` empty | §5.2.6 | warning; no Billit call. |
| TC-BILLIT-8 | Rainy | A line has empty `description` | §5.2.7 | warning; no Billit call. |
| TC-BILLIT-9 | Rainy | A line has `quantity <= 0` | §5.2.7 | warning; no Billit call. |
| TC-BILLIT-10 | Rainy | A line has `unitPriceExcl < 0` | §5.2.7 | warning; no Billit call. |
| TC-BILLIT-11 | Rainy | A line has `unitPriceExcl == 0` | §5.2.7 | warning (0 is falsy); no Billit call. |
| TC-BILLIT-12 | Edge | First line valid, second line invalid | §5.2.7 | Warning refers to the first failing line; no Billit call. |
| TC-BILLIT-13 | Rainy | Billit returns non-2xx | FR-BILLIT-5 | `{status:"error", message:<Billit JSON>}`; `externalId` unchanged. |
| TC-BILLIT-14 | Edge | Billit returns 200 with a non-integer body | FR-BILLIT-5 | Documented behaviour (current impl: unhandled `int()` — see §21 gap). |
| TC-BILLIT-15 | Edge | Billit returns non-JSON error body | FR-BILLIT-5 | Structured error, not a 500 (current impl: unhandled — see §21 gap). |
| TC-BILLIT-16 | Edge | PDF is generated and attached as base64 `OrderPDF` | FR-BILLIT-2, FR-BILLIT-3 | Outbound Billit `POST /orders` body contains `OrderPDF.FileName` and base64 `OrderPDF.FileContent`. |
| TC-BILLIT-17 | Edge | `OrderType` is `Invoice` for bills, `CreditNote` for cnotes | FR-CN-4 | Outbound body `OrderType` matches. |
| TC-BILLIT-18 | Edge | `OrderDirection` is `Income` | FR-CN-4 | Outbound body `OrderDirection == "Income"`. |

### 14.2 Credit-note-specific Billit gates

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-BILLIT-19 | Rainy | cnote with no `aboutInvoiceNumber` | §5.2.8 | warning; no Billit call. |
| TC-BILLIT-20 | Rainy | cnote whose referenced invoice is not in local `bills` | §5.2.9, FR-CN-2 | warning; no Billit call. |
| TC-BILLIT-21 | Edge | cnote whose referenced invoice exists locally but is not yet on Billit | §5.2.9 [ASSUMPTION] | Current behaviour: passes the local check (presence only); document as known assumption. |
| TC-BILLIT-22 | Edge | cnote amounts in outbound JSON are positive | FR-CN-5 | `OrderLines` totals are non-negative. |

### 14.3 Billit customer payload

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-BILLIT-23 | Sunny | Customer has all address fields | §6.3 | Outbound `Customer.Addresses[0]` has `Street`, `StreetNumber`, `City`, `Zipcode`, `CountryCode=="BE"`. |
| TC-BILLIT-24 | Rainy | Customer missing all of `company`/`name`/`surname` | §6.3 | `SyncoraError` 900 surfaced as controlled error (see §21 gap). |
| TC-BILLIT-25 | Edge | `CountryCode` is always `BE` | §6.3 [GAP] | Outbound `CountryCode == "BE"` regardless of input. |
| TC-BILLIT-26 | Edge | Multiple emails/phones → only first sent | §6.3 | `Email`/`Phone`/`Mobile` are single (first) values. |
| TC-BILLIT-27 | Edge | `Language` upper-cased in Billit payload | §6.3 | Outbound `Language` is uppercase. |

---

## 15. Peppol send flow (FR-PEPPOL-1..4, API-BILL-7, API-CN-7)

`POST /api/bills/sendPeppol/{id}` and `POST /api/cnotes/sendPeppol/{id}`.

### 15.1 `pre_peppol_checks` gates (order is significant)

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-PEPPOL-1 | Sunny | Registered bill, status NOT_SENT, customer has VAT → Billit 200/201 | FR-PEPPOL-1..3, API-BILL-7 | `{status:"success"}`; local `peppolDeliveryStatus` set to `UNKNOWN (0)`; poll started; outbound `POST /orders/commands/send` body `{Transporttype:"Peppol", OrderIDs:[externalId]}`. |
| TC-PEPPOL-2 | Rainy | No `externalId` (not registered) | §5.3.1 | warning; no Billit call. |
| TC-PEPPOL-3 | Rainy | Status already `PENDING` | §5.3.2 | warning; no resend. |
| TC-PEPPOL-4 | Rainy | Status already `SENT` | §5.3.2 | warning; no resend. |
| TC-PEPPOL-5 | Rainy | Customer has no `vat_number` | §5.3.3 | warning; no Billit call. |
| TC-PEPPOL-6 | Rainy | Billit send returns non-2xx | FR-PEPPOL-4 | `{status:"error", message:<Billit JSON>}`; status unchanged. |
| TC-PEPPOL-7 | Edge | Billit send returns non-JSON error body | FR-PEPPOL-4 | Structured error, not a 500 (current impl: unhandled — see §21 gap). |

### 15.2 Credit-note-specific Peppol gates

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-PEPPOL-8 | Rainy | Referenced invoice's Peppol status is not `SENT` | FR-CN-3, §5.3.4 | warning; no Billit call. |
| TC-PEPPOL-9 | Rainy | Referenced invoice does not exist locally | §5.3.4 [GAP] | Structured error, not a 500 (current impl: `IndexError` — see §21 gap). |
| TC-PEPPOL-10 | Sunny | Referenced invoice is `SENT` and all other gates pass | FR-CN-3 | `{status:"success"}`; cnote status set to UNKNOWN; poll started. |

---

## 16. Peppol status polling (FR-POLL-1..6)

Polling runs on a daemon thread; tests inject a fake Billit `GET /orders/{id}`
that returns scripted `CurrentDocumentDeliveryDetails` and a fake
`set_peppol_status` callback, then assert the persisted status transitions. Use
short `poll_interval`/`timeout` fixtures.

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-POLL-1 | Sunny | Billit reports `IsDocumentDelivered:true` | FR-POLL-3 | Callback receives `SENT (2)`; polling stops. |
| TC-POLL-2 | Sunny | First poll `DocumentDeliveryStatus=="Pending"`, later `IsDocumentDelivered:true` | FR-POLL-3 | Callback receives `PENDING (1)` then `SENT (2)`. |
| TC-POLL-3 | Sunny | `Pending` reported twice | FR-POLL-3 | `PENDING` set once (first occurrence only). |
| TC-POLL-4 | Rainy | 5 consecutive non-2xx responses | FR-POLL-4 | Polling stops after 5 errors; status not advanced to SENT. |
| TC-POLL-5 | Edge | 1-hour timeout reached without delivery | FR-POLL-4 | Polling stops; status remains last known. |
| TC-POLL-6 | Edge | Same `externalId` polled concurrently | FR-POLL-2 | Only one background task runs per id. |
| TC-POLL-7 | Edge | Error count decays on success | FR-POLL-3 | A success after errors does not reset to 0 abruptly; documented counter behaviour. |
| TC-POLL-8 | Edge | `get_one` triggers a poll when status is PENDING/UNKNOWN | FR-POLL-6 | A poll is started as a side effect of the GET. |
| TC-POLL-9 | Edge | `get_one` does not poll when status is NOT_SENT/SENT | FR-POLL-6 | No poll started. |
| TC-POLL-10 | Edge | Status update persisted via callback | FR-POLL-5 | Fake Mongo doc's `peppolDeliveryStatus` updated. |
| TC-POLL-11 | Edge | Poller is a process singleton | FR-POLL-1 | Two constructions return the same instance. |

---

## 17. Totals, OGM, and pure logic (§5.5, §5.6)

These are pure-logic unit tests on `OrderBack` constructed directly.

### 17.1 Taxable-amount totals

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-TOTAL-1 | Sunny | Single line, qty 1, price 100, VAT 6% | §5.5 | `totalExcl==100.00`, `totalIncl==106.00`, `totalVAT==6.00`. |
| TC-TOTAL-2 | Sunny | Two lines same VAT rate 21%, 100 + 200 | §5.5 | `totalExcl==300.00`, `totalIncl==363.00`. |
| TC-TOTAL-3 | Edge | Two lines different rates (6% 100, 21% 100) | §5.5 | `totalExcl==200.00`; `totalIncl == round(100*1.06,2)+round(100*1.21,2) == 227.00`. |
| TC-TOTAL-4 | Edge | Rounding drift case: three 6% lines of 33.33 each | §5.5 | `totalIncl == round(99.99*1.06, 2) == 105.99` (grouped, not per-line). |
| TC-TOTAL-5 | Edge | Zero VAT (reverse charge code 21) | §5.5 | `totalVAT==0.00`, `totalIncl==totalExcl`. |
| TC-TOTAL-6 | Edge | Empty `orderLines` | §5.5 | `totalExcl==0.00`, `totalIncl==0.00`, `totalVAT==0.00`. |
| TC-TOTAL-7 | Rainy | Negative computed total (negative price) | §5.5 | `SyncoraError` (codes 903–905) surfaced as controlled error (see §21 gap). |
| TC-TOTAL-8 | Edge | Per-line totals are line-rounded independently | §5.5 | Each line `total_excl` is `round(qty*price,2)`. |
| TC-TOTAL-9 | Edge | `totalVAT == totalIncl - totalExcl` | §5.5 | Holds for all multi-rate cases. |

### 17.2 OGM

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-OGM-1 | Sunny | `orderNumber` shorter than 10 digits, e.g. "2026-1" | §5.6 | OGM matches `+++ddd/dddd/ddddCC+++` with check digit `int(padded10) % 97` (97 if 0). |
| TC-OGM-2 | Edge | `orderNumber` exactly 10 digits | §5.6 | No extra padding. |
| TC-OGM-3 | Edge | `orderNumber` longer than 10 chars | §5.6 [ASSUMPTION] | Document current behaviour (ljust only pads; overflow kept). |
| TC-OGM-4 | Edge | Check digit computes to 0 | §5.6 | Stored as 97. |
| TC-OGM-5 | Edge | Credit note | FR-CN-6 | `ogm == ""`. |

### 17.3 Dates and locking

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-DATE-1 | Sunny | `orderDate` ISO → `dd/mm/YYYY` | §5.5 | `formatted_order_date` matches. |
| TC-DATE-2 | Edge | Empty date string | §2.5.2 | `""`. |
| TC-LOCK-1 | Sunny | `externalId>0` → locked | §5.4 | `locked`/`billitSent` true. |
| TC-LOCK-2 | Edge | `externalId==0` | §5.4 | locked false. |
| TC-LOCK-3 | Rainy | `externalId` is `Undefined` | §5.4, §5.4 [GAP] | `SyncoraError` 906 surfaced as controlled error (see §21 gap). |
| TC-LOCK-4 | Sunny | `peppolDeliveryStatus != -1` → undeletable | §5.4 | undeletable true for 0,1,2. |
| TC-LOCK-5 | Edge | `peppolDeliveryStatus == -1` | §5.4 | undeletable false. |
| TC-LOCK-6 | Rainy | `peppolDeliveryStatus` is `Undefined` | §5.4 [GAP] | `SyncoraError` 906 surfaced as controlled error (see §21 gap). |
| TC-LOCK-7 | Edge | Locked but deletable (externalId>0, status -1) | §5.4 | `locked` true, `undeletable` false. |

---

## 18. Files / PDF (FR-FILE-1..4, FR-PDF-1..6, API-FILE-1..3)

PDF assertions use the response headers + extracted PDF text (e.g. via
`pypdf`); tests are skipped if WeasyPrint system deps are unavailable.

### 18.1 File endpoints

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-FILE-1 | Sunny | `GET /api/files/customers/{id}` | FR-FILE-1, API-FILE-1 | 200; `Content-Type: application/pdf`; `Content-Disposition: inline; filename=customer_<id>.pdf`; non-empty body. |
| TC-FILE-2 | Sunny | `GET /api/files/bills/{id}` | FR-FILE-2, API-FILE-2 | 200; `application/pdf`; `inline; filename=bill_<id>.pdf`. |
| TC-FILE-3 | Sunny | `GET /api/files/cnotes/{id}` | FR-FILE-3, API-FILE-3 | 200; `application/pdf`; `inline; filename=cnote_<id>.pdf`. |
| TC-FILE-4 | Rainy | Non-existent customer id | API-FILE-1 | Structured error (current impl: unhandled — see §21 gap). |
| TC-FILE-5 | Rainy | Non-existent bill id | API-FILE-2 | Structured error (current impl: unhandled — see §21 gap). |
| TC-FILE-6 | Rainy | Non-integer customer path segment | API-FILE-1 | 404 (Flask `int` converter). |

### 18.2 Bill / cnote PDF content

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-PDF-1 | Sunny | FR customer | FR-PDF-1 | Extracted text contains FR labels (seller block, "Total", etc.). |
| TC-PDF-2 | Sunny | NL customer (language not "FR") | FR-PDF-1 | Extracted text contains NL labels. |
| TC-PDF-3 | Edge | `ventilationCode == "2"` | FR-PDF-3 | 6% certificate text present. |
| TC-PDF-4 | Edge | `ventilationCode == "4"` | FR-PDF-3 | 6% certificate text absent. |
| TC-PDF-5 | Edge | `ventilationCode == "21"` | §7.3 | Reverse-charge / autoliquidation legal text present. |
| TC-PDF-6 | Sunny | General conditions appended | FR-PDF-4 | PDF has more than one page; final pages are the conditions. |
| TC-PDF-7 | Sunny | Monetary amounts use comma separator | FR-PDF-2 | Extracted text shows `"12,34"` style (not `12.34`). |
| TC-PDF-8 | Sunny | cnote PDF omits delivery date and OGM, shows about-invoice number | FR-PDF-5 | No delivery-date line, no OGM; about-invoice number visible. |
| TC-PDF-9 | Sunny | Same bytes sent to Billit and served by file endpoint | FR-PDF-6 | The base64 in the Billit `POST /orders` body decodes to bytes equal to (or matching the text of) the file-endpoint PDF. |
| TC-PDF-10 | Edge | Customer info PDF lists the documented fields | FR-FILE-1 | Extracted text contains number, name/surname, company, address, VAT, language, architect name, comment. |
| TC-PDF-11 | Edge | All order-line units empty → `unit` column hidden | §7.2 | Template renders without unit column (template flag). |
| TC-PDF-12 | Edge | Salutation + contact name present → salutation shown | §7.2 | Salutation line present. |
| TC-PDF-13 | Edge | Empty `orderLines` at PDF generation | §7.2 [GAP] | Documented behaviour (current impl: `IndexError` on `orderLines[0]` — see §21 gap). |

---

## 19. Non-functional & cross-cutting (NFR-*)

### 19.1 Error handling envelope

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-NFR-1 | Rainy | Negative total triggered via API | NFR-REL-1 | Controlled JSON error (status `error`), not an HTML 500. |
| TC-NFR-2 | Rainy | `ItemNotFoundError` from `get_one` | NFR-REL-2 | Structured error with HTTP 400-ish semantics. |
| TC-NFR-3 | Rainy | Billit non-2xx forwarded | NFR-REL-3 | `{status:"error", message:<Billit JSON>}`; no crash. |
| TC-NFR-4 | Rainy | cnote Peppol send with missing referenced invoice | NFR-REL-5 | Structured error, not `IndexError` 500. |
| TC-NFR-5 | Edge | All error envelopes have a `status` field | §2.6 | Every non-success response body includes `status` in `{error,warning}`. |

### 19.2 Concurrency & performance

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-NFR-6 | Edge | Customer writes serialised through one lock | NFR-PERF-1 | Concurrent create/update calls do not interleave (fake connector records lock acquire/release ordering). |
| TC-NFR-7 | Edge | Poller does not block request handling | NFR-REL-4 | A `sendPeppol` that starts a poll returns before the poll completes. |
| TC-NFR-8 | Edge | Listing returns the full collection | NFR-PERF-5 | `GET /api/bills` returns all seeded docs (no pagination). |

### 19.3 Data integrity

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-NFR-9 | Sunny | Created order has `externalId`/`peppolDeliveryStatus` defaults | NFR-DI-2 | Persisted doc has both fields set (0 and -1). |
| TC-NFR-10 | Rainy | `orderNumber` uniqueness at DB level | NFR-DI-1 [GAP] | Document current behaviour: uniqueness enforced in code only (see §21 gap). |
| TC-NFR-11 | Edge | Access connector refreshes on `.accdb` mtime change | NFR-DI-3 | Fake connector reconnects when mtime advances. |

### 19.4 Security & observability

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-NFR-12 | Edge | Billit `apiKey`/`partyID` sent on every Billit call | §6.1 | Outbound headers contain both. |
| TC-NFR-13 | Edge | `apiKey` never appears in response bodies/logs | NFR-SEC-2 | Assert the fake recorded no leaked secret in returned envelopes. |
| TC-NFR-14 | Edge | No auth on `/api/*` | NFR-SEC-1 [GAP] | Unauthenticated request succeeds (documented gap). |
| TC-NFR-15 | Edge | Billit calls have an explicit timeout | NFR-PERF-4 [GAP] | Outbound `requests` calls pass a finite timeout (document current: none — see §21 gap). |

### 19.5 Tooling

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-NFR-16 | Edge | `prek run --all-files` passes | NFR-MAINT-1 | CI lint step is green. |
| TC-NFR-17 | Edge | `pytest` runs with `pythonpath=["src"]` | NFR-MAINT-2 | Suite discovers/runs from repo root. |

---

## 20. Billit delete & send (FR-BILLIT-7, §6.4, §6.6)

| ID | Class | Scenario | Trace | Expected |
| --- | --- | --- | --- | --- |
| TC-BILLIT-DEL-1 | Sunny | `DELETE /orders/{id}` returns body `true` | FR-BILLIT-7, §6.6 | Treated as success; local delete proceeds. |
| TC-BILLIT-DEL-2 | Rainy | `DELETE /orders/{id}` returns body other than `true` | §6.6 | Treated as failure; error text forwarded; local delete aborted. |
| TC-BILLIT-DEL-3 | Edge | `DELETE /orders/{id}` returns 2xx with non-`true` body | §6.6 | Still treated as failure (only `b"true"` is success). |
| TC-BILLIT-DEL-4 | Sunny | `send` body shape | §6.4 | Outbound `POST /orders/commands/send` body `{Transporttype:"Peppol", OrderIDs:[<externalId>]}`. |
| TC-BILLIT-DEL-5 | Edge | Only `Peppol` transport used | §6.4 | No other `Transporttype` value ever sent. |

---

## 21. Known-gap regression tests

These tests **pin the current (deficient) behaviour** so that any change is
detected. Each is marked `@pytest.mark.gap` and should be **converted to a
sunny/rainy assertion** once the corresponding `[GAP]` in `01`–`08` is closed.
They are not part of the contracted behaviour and must not be relied upon by
the frontend.

| ID | Scenario | Trace (GAP) | Pinned current behaviour |
| --- | --- | --- | --- |
| TC-GAP-1 | Update non-existent bill | §12.2, NFR-REL-1 | Raises / 500 (unhandled `None.locked`). |
| TC-GAP-2 | `get_one` missing order | NFR-REL-2 | `ItemNotFoundError` propagates as 500 (no error handler). |
| TC-GAP-3 | cnote Peppol with missing referenced invoice | §5.3.4, NFR-REL-5 | `IndexError` → 500. |
| TC-GAP-4 | Billit returns non-integer success body | FR-BILLIT-5 | `int()` → 500. |
| TC-GAP-5 | Billit returns non-JSON error body | FR-BILLIT-5, FR-PEPPOL-4 | `.json()` → 500. |
| TC-GAP-6 | Negative totals via API | NFR-REL-1, §5.5 | `SyncoraError` 903–905 → 500. |
| TC-GAP-7 | `locked`/`undeletable` with `Undefined` field | §5.4 | `SyncoraError` 906 → 500. |
| TC-GAP-8 | Customer create with no name/surname/company | FR-CUS-3 | `SyncoraError` 1000 → 500. |
| TC-GAP-9 | `orderNumber` uniqueness only in code | NFR-DI-1 | No DB unique index; concurrent inserts can duplicate. |
| TC-GAP-10 | Billit `requests` have no timeout | NFR-PERF-4 | Outbound calls pass `timeout=None`. |
| TC-GAP-11 | `get_customer` returns a string body, not JSON `Content-Type` | API-CUS-3 | Response `Content-Type` is not `application/json`. |
| TC-GAP-12 | PDF generation uses CWD-relative paths | §7.5 | Generation fails unless CWD is the repo root. |
| TC-GAP-13 | `format_dyn_data` on empty `orderLines` | §7.2 | `IndexError` on `orderLines[0]`. |
| TC-GAP-14 | Poller singleton ignores later constructor args | §6.7 | `poll_interval`/`timeout` overrides after first instantiation have no effect. |
| TC-GAP-15 | `delete_cnote` warning mentions Billit, not Peppol | §12.4 vs cnotes | Message wording inconsistency (not contract; informational). |
| TC-GAP-16 | `CountryCode` hardcoded to `BE` | §6.3 | Non-BE customers cannot be sent to Billit. |
| TC-GAP-17 | `.env` re-read on every Billit call | NFR-PERF-3 | `dotenv_values` invoked per call (perf only). |
| TC-GAP-18 | `print()` of responses/bodies to stdout | NFR-OBS-2 | Billit error bodies and `to_front()` are printed. |

---

## 22. Traceability summary

Every requirement ID in `01`–`08` is covered by at least one test case above.
Coverage matrix (requirement doc → test sections):

- `01-overview` (scope, glossary) → informs all sections.
- `02-architecture-and-data` (envelope, error model, data models) → §10, §17,
  §19.
- `03-api-specification` (endpoints & bodies) → §11–§15, §18.
- `04-functional-requirements` (FR-*) → §11–§18 (per area).
- `05-business-rules` (state machine, gates, totals, OGM, locking) → §14, §15,
  §17.
- `06-billit-and-peppol-integration` (headers, payloads, polling) → §14, §15,
  §16, §20.
- `07-pdf-generation` (FR-PDF-*) → §18.
- `08-non-functional-requirements` (NFR-*) → §19, §21.

### Conventions for implementers

- Use `pytest` with `pythonpath = ["src"]` (per `pyproject.toml`).
- Fake Billit with `responses` or a custom `requests` transport adapter; never
  network.
- Fake MongoDB with `mongomock`; fake Access with an in-memory dict behind the
  `CustomerModel` interface.
- Mark integration-only PDF tests with `@pytest.mark.integration`; skip when
  WeasyPrint system deps are missing.
- Keep assertions on the JSON `status` field and request shape; do not pin
  French message strings.
