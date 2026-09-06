# 03 — REST API Specification

All endpoints are served under `/api/*` by the Flask app. The frontend reaches
them via a same-origin proxy (Vite dev proxy to `:5000`, or nginx in
production). Request/response bodies are JSON unless noted (file endpoints
return `application/pdf`).

There is **no authentication** on these endpoints (see `08` NFRs). HTTP status
codes are Flask defaults (200 for normal responses, including validation
"warning"/"error" envelopes); the outcome is conveyed by the `status` field in
the JSON body.

Response envelope (`ResponseMessage`, `constants/all.py`):

```
{ "id"?: int|str, "status": "success"|"error"|"warning", "message"?: str, "code"?: int }
```

## 3.1 Bills — `routes/bills.py`

| ID | Method & path | Purpose | Source |
| --- | --- | --- | --- |
| API-BILL-1 | `GET /api/bills` | List all bills (short form). | `controllers/bills.py:81` |
| API-BILL-2 | `POST /api/bills` | Create a bill. | `controllers/bills.py:29` |
| API-BILL-3 | `GET /api/bills/{bill_id}` | Get one bill (full form); may trigger a Peppol status refresh. | `controllers/bills.py:70` |
| API-BILL-4 | `PUT /api/bills/{bill_id}` | Update a bill (delegates to create with `db_id`). | `controllers/bills.py:108` |
| API-BILL-5 | `DELETE /api/bills/{bill_id}` | Delete a bill locally and on Billit if registered. | `controllers/bills.py:112` |
| API-BILL-6 | `POST /api/bills/sendBillit/{bill_id}` | Register/send the bill to Billit. | `controllers/bills.py:253` |
| API-BILL-7 | `POST /api/bills/sendPeppol/{bill_id}` | Send the registered bill via Peppol. | `controllers/bills.py:167` |

### Request bodies

**POST/PUT `/api/bills[/{bill_id}]`** — `OrderFront` (built by frontend
`pages/billing.tsx:354`):

```jsonc
{
  "customerId": 12,            // int, required (Client.Numero)
  "orderTitle": "Chantier ...", // required
  "orderDate": "2026-09-06",    // ISO date
  "expiryDate": "2026-09-20",
  "deliveryDate": "2026-09-06",
  "orderNumber": "2026-001",    // unique within bills; null/empty allowed on create
  "ventilationCode": "2",       // Billit VAT code ("2"|"4"|"21"...)
  "orderLines": [
    { "description": "...", "quantity": 1, "unitPriceExcl": 100.0,
      "unit": "h", "VATPercentage": 6.0 }
  ]
}
```

The `bill_id` path param is the Mongo `_id` string. The frontend uses
`"0"` to mean "create new".

### Responses

- **API-BILL-1** returns an array of `OrderFrontShort`:
  `{ orderId, customerName, orderNumber, orderDate, orderTitle }`.
  `customerName` is computed as `"name surname, company"` from the Access DB
  (`controllers/bills.py:81`).
- **API-BILL-2/4** return `{ "status": "success", "id": "<mongo_id>" }` on
  success; `{ "status": "error", "message": "..." }` on duplicate order
  number; `{ "status": "warning", "message": "..." }` if the bill is locked
  (already sent to Billit).
- **API-BILL-3** returns the full `OrderBack.to_front()` payload (see §3.4).
- **API-BILL-5** returns `{ "status": "success" }` or `error`/`warning`
  (undeletable / Billit delete failure).
- **API-BILL-6/7** return `{ "status": "success" }` or
  `{ "status": "error", "message": <Billit JSON> }`.

## 3.2 Credit notes — `routes/cnotes.py`

Mirror of the bills API, paths under `/api/cnotes`. Differences are noted in
`04-functional-requirements.md` §4.3 and `05-business-rules.md` §7.

| ID | Method & path | Purpose |
| --- | --- | --- |
| API-CN-1 | `GET /api/cnotes` | List all credit notes (short form). |
| API-CN-2 | `POST /api/cnotes` | Create a credit note. |
| API-CN-3 | `GET /api/cnotes/{cnote_id}` | Get one credit note. |
| API-CN-4 | `PUT /api/cnotes/{cnote_id}` | Update a credit note. |
| API-CN-5 | `DELETE /api/cnotes/{cnote_id}` | Delete a credit note. |
| API-CN-6 | `POST /api/cnotes/sendBillit/{cnote_id}` | Register on Billit. |
| API-CN-7 | `POST /api/cnotes/sendPeppol/{cnote_id}` | Send via Peppol. |

**POST/PUT body** adds `aboutInvoiceNumber` (the referenced invoice number);
`deliveryDate` is omitted by the frontend for credit notes
(`pages/creditNote.tsx:367`):

```jsonc
{
  "customerId": 12,
  "orderTitle": "...",
  "orderDate": "...",
  "expiryDate": "...",
  "orderNumber": "C2026-001",
  "aboutInvoiceNumber": "2026-001",   // present ⇒ credit note
  "ventilationCode": "2",
  "orderLines": [ ... ]
}
```

## 3.3 Customers — `routes/customers.py`

| ID | Method & path | Purpose | Source |
| --- | --- | --- | --- |
| API-CUS-1 | `GET /api/customers` | List customers (list/autocomplete form). | `controllers/customers.py:26` |
| API-CUS-2 | `POST /api/customers` | Create a customer. | `controllers/customers.py:66` |
| API-CUS-3 | `GET /api/customers/{customer_id}` | Get one customer (full form). | `controllers/customers.py:61` |
| API-CUS-4 | `PUT /api/customers/{customer_id}` | Update a customer. | `controllers/customers.py:79` |
| API-CUS-5 | `DELETE /api/customers/{customer_id}` | Delete a customer. | `controllers/customers.py:90` |

`customer_id` is the Access `Numero` (int).

**POST/PUT body** (`pages/customer.tsx:212`):

```jsonc
{
  "name": "Dupont", "surname": "Luc", "company": "Acme",
  "street": "Rue X", "number": "12",       // assembled into Adresse
  "postal_code": "1000", "city": "Bruxelles",
  "vat_number": "BE0...", "language": "fr", // lowercased server-side
  "salutation": "Mr.", "architect_name": "...", "comment": "..."
}
```

**API-CUS-1** returns an array with a **subset** of fields:
`{ id, name, surname, company, postal_code, city, mobileNumbers,
telephoneNumbers, hasVAT, hasEmail }` (`controllers/customers.py:42`). The
frontend (`components/clientAutocomplete.tsx`, `pages/customerList.tsx`)
relies on `hasEmail`, `hasVAT`, `mobileNumbers`, `telephoneNumbers`.

**API-CUS-3** returns `CustomerBack.to_front()` JSON (excludes `id`, `address`,
`emails`, `telephoneNumbers`, `mobileNumbers`; includes computed `street`,
`number`). **[GAP]** `get_customer` returns a `str` (via `json.dumps`) rather
than a Flask `Response`; the route does not `jsonify` it — works because Flask
accepts a string body, but the `Content-Type` is not explicitly JSON.

## 3.4 Files — `routes/files.py`

| ID | Method & path | Purpose | Response |
| --- | --- | --- | --- |
| API-FILE-1 | `GET /api/files/customers/{customer_id}` | Customer info PDF (ReportLab). | `application/pdf`, inline, `customer_<id>.pdf` |
| API-FILE-2 | `GET /api/files/bills/{bill_id}` | Bill PDF (templated). | `application/pdf`, inline, `bill_<id>.pdf` |
| API-FILE-3 | `GET /api/files/cnotes/{cnote_id}` | Credit-note PDF (templated). | `application/pdf`, inline, `cnote_<id>.pdf` |

`Content-Disposition: inline; filename=...`. Used by the frontend "Print"
buttons (`pages/billing.tsx:436`, `customer.tsx:309`, `creditNote.tsx:450`).

## 3.5 `OrderBack.to_front()` shape (GET one bill/cnote)

Returned by API-BILL-3 / API-CN-3. Field aliases (`by_alias=True`) with
`orderId`, `externalId`, and the order-line sub-totals excluded
(`constants/order_back.py:219`):

```jsonc
{
  "customerId": 12,
  "customerName": "Luc Dupont, Acme",   // only if set (list path)
  "orderNumber": "2026-001",
  "orderDate": "...", "expiryDate": "...", "deliveryDate": "...",
  "orderTitle": "...",
  "ventilationCode": "2",
  "aboutInvoiceNumber": "...",          // credit notes only
  "peppolDeliveryStatus": -1,
  "billitSent": false,
  "totalExcl": 100.0, "totalVAT": 6.0, "totalIncl": 106.0,
  "orderLines": [
    { "description": "...", "quantity": 1, "unitPriceExcl": 100.0,
      "unit": "h", "VATPercentage": 6.0 }
  ]
}
```

The frontend reads `billitSent` (bool) and `peppolDeliveryStatus` (int) to
gate the Save/Billit/Peppol buttons (`pages/billing.tsx:118`).
