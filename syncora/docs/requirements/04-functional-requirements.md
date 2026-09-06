# 04 — Functional Requirements

Requirements are grouped by entity/flow and tagged `FR-<area>-N`. "Source"
citations are relative to `syncora/src/`.

## 4.1 Customers (FR-CUS)

| ID | Requirement | Source |
| --- | --- | --- |
| FR-CUS-1 | The backend shall list customers from the Access `Client` table, returning `id, name, surname, company, postal_code, city, mobileNumbers, telephoneNumbers, hasVAT, hasEmail`. | `controllers/customers.py:26` |
| FR-CUS-2 | The backend shall return one customer by `Numero` with all stored fields plus computed `street`/`number` (from `Adresse`) and contact info (from `Commentaire`). | `controllers/customers.py:61`, `customer_back.py:112` |
| FR-CUS-3 | The backend shall create a customer. It must reject creation when none of `name`, `surname`, or `company` is provided (`SyncoraError` code 1000). | `controllers/customers.py:66` |
| FR-CUS-4 | The backend shall update a customer by `Numero`, forcing `id` to the path id. | `controllers/customers.py:79` |
| FR-CUS-5 | The backend shall delete a customer by `Numero`. | `controllers/customers.py:90` |
| FR-CUS-6 | On create, the backend shall assemble a single `Adresse` string from `street` + `number` when `address` is not supplied. | `customer_back.py:202` |
| FR-CUS-7 | The backend shall store `language` lowercased. | `customer_back.py:216` |
| FR-CUS-8 | The backend shall derive `emails`, `telephoneNumbers`, and `mobileNumbers` from `comment` by regex; these are not persisted. | `customer_back.py:126-192` |
| FR-CUS-9 | The backend shall expose `hasVAT` and `hasEmail` booleans (computed). | `customer_back.py:194-200` |
| FR-CUS-10 | The backend shall recognise "new-format" customer comments as those starting and ending with `##` (`is_old_db_comment`). **[GAP]** This helper exists in `controllers/customers.py:153` but is not wired into any flow. | `controllers/customers.py:153` |

## 4.2 Bills (FR-BILL)

| ID | Requirement | Source |
| --- | --- | --- |
| FR-BILL-1 | The backend shall list all bills, joining each bill with its customer from Access to build `customerName` = `"name surname, company"`. | `controllers/bills.py:81` |
| FR-BILL-2 | The backend shall create a bill in MongoDB, initialising `externalId=0` and `peppolDeliveryStatus=-1`. | `models/order_model.py:37` |
| FR-BILL-3 | The backend shall reject creating/updating a bill whose `orderNumber` already exists in `bills`, unless the duplicate belongs to the bill being edited. | `controllers/bills.py:33` |
| FR-BILL-4 | The backend shall reject updating a bill that is locked (already sent to Billit). | `controllers/bills.py:50` |
| FR-BILL-5 | The backend shall return one bill as `OrderBack.to_front()` and, when its Peppol status is `PENDING` or `UNKNOWN`, trigger an asynchronous status poll. | `controllers/bills.py:70` |
| FR-BILL-6 | The backend shall delete a bill. It must refuse deletion when the bill is undeletable (Peppol status ≠ -1). If the bill has an `externalId`, it must first delete the order on Billit; if Billit deletion fails, the local deletion is aborted. | `controllers/bills.py:112` |
| FR-BILL-7 | The backend shall register a bill on Billit (see §4.4). | `controllers/bills.py:253` |
| FR-BILL-8 | The backend shall send a registered bill via Peppol (see §4.5). | `controllers/bills.py:167` |

## 4.3 Credit notes (FR-CN)

The credit-note flows mirror bills (`controllers/cnotes.py`) with these
additions:

| ID | Requirement | Source |
| --- | --- | --- |
| FR-CN-1 | A credit note is an order whose `aboutInvoiceNumber` is present (i.e. not `Undefined`). | `order_back.py:163` |
| FR-CN-2 | The backend shall reject sending a credit note to Billit unless its `aboutInvoiceNumber` is set and the referenced invoice exists in the local `bills` collection (`BillModel.contains`). | `controllers/cnotes.py:231-249` |
| FR-CN-3 | The backend shall reject sending a credit note to Peppol unless the referenced invoice's Peppol status is `SENT`. | `controllers/cnotes.py:164-174` |
| FR-CN-4 | The Billit `OrderType` for a credit note must be `CreditNote` and `OrderDirection` must be `Income`. | `order_billit.py:64-69` |
| FR-CN-5 | Credit-note amounts sent to Billit must remain **positive** in JSON (Billit credit-note rule). **[ASSUMPTION]** Syncora does not negate amounts; this matches the Billit doc but should be verified against the PDF sign convention. | Billit "Credit Note" doc |
| FR-CN-6 | Credit notes have no delivery date and no OGM (`formatted_delivery_date` returns `""`, `ogm` returns `""`). | `order_back.py:152-197` |

## 4.4 Billit registration flow (FR-BILLIT)

Applies to both bills and credit notes (`controllers/bills.py:253`,
`controllers/cnotes.py:287`, `controllers/billit.py:102`).

| ID | Requirement | Source |
| --- | --- | --- |
| FR-BILLIT-1 | Before sending, the backend shall run `pre_billit_checks` (see `05-business-rules.md` §2). | `controllers/bills.py:182` |
| FR-BILLIT-2 | The backend shall generate a PDF for the order (see `07-pdf-generation.md`). | `controllers/bills.py:261` |
| FR-BILLIT-3 | The backend shall build a Billit payload: the order dump merged with `Customer`, and an `OrderPDF` (`FileName`, base64 `FileContent`). | `controllers/billit.py:109` |
| FR-BILLIT-4 | The backend shall POST the payload to `{URL}/orders` with Billit headers. | `controllers/billit.py:119` |
| FR-BILLIT-5 | On HTTP 200/201, the backend shall store the returned integer as `externalId` (callback) and return success. On other codes, it shall return `error` forwarding Billit's JSON. | `controllers/billit.py:124-128` |
| FR-BILLIT-6 | Once `externalId > 0`, the order is **locked**: subsequent create/update must be rejected. | `order_back.py:167` |
| FR-BILLIT-7 | The backend shall support deleting a Billit order via `DELETE {URL}/orders/{order_id}`; success is when the response body equals `b"true"`. | `controllers/billit.py:79` |

## 4.5 Peppol send flow (FR-PEPPOL)

Applies to both bills and credit notes (`controllers/bills.py:167`,
`controllers/cnotes.py:186`, `controllers/billit.py:92`).

| ID | Requirement | Source |
| --- | --- | --- |
| FR-PEPPOL-1 | Before sending, the backend shall run `pre_peppol_checks` (see `05-business-rules.md` §3). | `controllers/bills.py:134` |
| FR-PEPPOL-2 | The backend shall POST `{Transporttype:"Peppol", OrderIDs:[externalId]}` to `{URL}/orders/commands/send`. | `controllers/billit.py:92` |
| FR-PEPPOL-3 | On HTTP 200/201, the backend shall set the local Peppol status to `UNKNOWN` (0) and start polling. | `controllers/bills.py:172` |
| FR-PEPPOL-4 | On non-2xx, the backend shall return `error` forwarding Billit's JSON. | `controllers/bills.py:178` |

## 4.6 Peppol status polling (FR-POLL)

Source: `utils/peppol_poller.py`.

| ID | Requirement | Source |
| --- | --- | --- |
| FR-POLL-1 | `PeppolStatusPoller` shall be a process singleton keyed by class (`__new__`). | `peppol_poller.py:41` |
| FR-POLL-2 | Polling for a given `externalId` shall run on a background daemon thread (asyncio loop), at most once per id concurrently. | `peppol_poller.py:53` |
| FR-POLL-3 | Each poll shall GET `{URL}/orders/{externalId}` and read `CurrentDocumentDeliveryDetails`: `IsDocumentDelivered` → set status `SENT` (2); `DocumentDeliveryStatus == "Pending"` (first time) → set `PENDING` (1). | `peppol_poller.py:84` |
| FR-POLL-4 | Polling shall run until delivered, a 1-hour timeout, or 5 consecutive errors; interval 5 s. | `peppol_poller.py:27-76` |
| FR-POLL-5 | Status updates shall call the model callback `set_peppol_status(external_id, status)`, persisting to MongoDB. | `controllers/bills.py:176`, `order_model.py:66` |
| FR-POLL-6 | `get_one` shall trigger a poll when the stored status is `PENDING` or `UNKNOWN`, so the frontend sees a refreshed status on open. | `controllers/bills.py:73` |

## 4.7 Files / PDF (FR-FILE)

| ID | Requirement | Source |
| --- | --- | --- |
| FR-FILE-1 | The backend shall produce a customer info PDF (ReportLab) with number, name/surname, company, address, VAT, language, architect name, comment. | `controllers/files.py:17` |
| FR-FILE-2 | The backend shall produce a bill PDF by templating + merging general conditions. | `controllers/files.py:46`, `07-pdf-generation.md` |
| FR-FILE-3 | The backend shall produce a credit-note PDF analogously. | `controllers/files.py:56` |
| FR-FILE-4 | PDFs shall be returned inline with `Content-Type: application/pdf`. | `controllers/files.py:39` |
