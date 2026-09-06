# 06 — Billit & Peppol Integration

This document maps Syncora's behaviour to the Billit REST API
(<https://docs.billit.be/docs>). All Billit calls are in
`src/controllers/billit.py` and `src/utils/peppol_poller.py`.

## 6.1 Authentication and headers

`get_headers()` (`controllers/billit.py:70`) sends, on every call:

| Header | Value | Billit doc |
| --- | --- | --- |
| `accept` | `application/json` | — |
| `apiKey` | `.env API_SECRET` | "PartyID and Key" / "Header values" |
| `partyID` | `.env PARTY_ID` | identifies the sending company |
| `contextPartyID` | `.env PARTY_ID` | same as partyID (single-company use) |

Billit also supports `Authorization` (OAuth) and `Idempotent-Key`; Syncora
uses neither. **[GAP]** `.env` is re-read with `dotenv_values(...)` on every
Billit call (and inside `peppol_poller`); values are not cached.

## 6.2 Create order — `POST {URL}/orders`

Source: `controllers/billit.py:102`, `constants/order_billit.py`.

Payload is `OrderBillit` (built from `OrderBack.model_dump()` + `Customer` +
base64 `OrderPDF`). Key fields mapped:

| Billit field | Syncora source | Notes |
| --- | --- | --- |
| `OrderType` | computed | `Invoice` or `CreditNote` (from `AboutInvoiceNumber`). |
| `OrderDirection` | constant | `Income`. |
| `OrderNumber` | `orderNumber` | Human invoice/cnote number. |
| `OrderDate` / `ExpiryDate` / `DeliveryDate` | `orderDate`/`expiryDate`/`deliveryDate` | `DeliveryDate` optional (credit notes). |
| `OrderTitle` | `orderTitle` | Billit `BuyerReference`. |
| `VentilationCode` | `ventilationCode` | VAT/tax category (see §6.5). |
| `TotalExcl`/`TotalIncl`/`TotalVAT` | computed totals | Taxable-amount method (§05.5). |
| `AboutInvoiceNumber` | `aboutInvoiceNumber` | Credit notes only; Billit validates the referenced invoice exists. |
| `Customer` | `CustomerBillit` | See §6.3. |
| `OrderLines` | `OrderLinesBillit` | Per-line description/qty/unit/excl/unit/VAT + line totals. |
| `OrderPDF` | `{FileName, FileContent(base64)}` | Self-generated PDF (§07). |

Response: Billit returns the integer order ID in the body (`response.json()`);
`send_billit` casts it to `int` and stores it via the `callback`
(`set_external_id`). Success = HTTP 200/201.

Per Billit docs ("Creating Sales Invoices"): totals are recalculated by
Billit; the customer is auto-created/matched by VAT/email/address; VAT
percentage must be valid for the sender's country. Syncora relies on these
behaviours.

## 6.3 Customer payload — `CustomerBillit`

Source: `constants/customer_billit.py`.

| Billit field | Syncora source | Notes |
| --- | --- | --- |
| `Nr` | `CustomerBack.id` | ERP customer number. |
| `Name` | `company` | Commercial name. |
| `VATNumber` | `vat_number` | Required for Peppol. |
| `Zipcode`, `City`, `Street`, `StreetNumber` | postal_code/city/street/number | min_length=1 enforced. |
| `CountryCode` | `BE` (constant) | **[GAP]** hardcoded; non-BE customers are not supported. |
| `ContactFirstName`/`ContactLastName` | `surname`/`name` | — |
| `Language` | `language` (upper-cased) | — |
| `Email`/`Phone`/`Mobile` | first of the computed lists | Single value each. |
| `PartyType` | `Customer` (constant) | — |
| `Addresses` | one `InvoiceAddress` | Computed from the address fields. |

Validator: at least one of `Name`/`ContactFirstName`/`ContactLastName` must be
set (`SyncoraError` 900).

## 6.4 Send via Peppol — `POST {URL}/orders/commands/send`

Source: `controllers/billit.py:92`, Billit "Sending the Sales Invoice" doc.

```json
{ "Transporttype": "Peppol", "OrderIDs": [<externalId>] }
```

- Only orders already registered on Billit (having `externalId`) can be sent.
- Billit validates Peppol compliance and receiver reachability; failures come
  back as non-2xx with an error body, which Syncora forwards as `error`.
- Syncora only uses `Peppol`. Other transport types (Email, other networks)
  are not exposed.

## 6.5 Ventilation codes

Source: `constants/order_back.py` (string code carried on the order), Billit
"Ventilation Codes (VAT)" doc. The frontend exposes three options
(`pages/billing.tsx:41`):

| Code | Label (UI) | VAT % sent | Billit meaning |
| --- | --- | --- | --- |
| `2` | 6% | 6.0 | Low rate (6% BE), TaxCategory S |
| `4` | 21% | 21.0 | High rate (21% BE), TaxCategory S |
| `21` | Co-contractant | 0.0 | VAT reverse charge, TaxCategory AE |

`1` (0%) is present in the backend constant set and commented out in the
frontend. Other Billit codes (`3`, `22`, `24`, `51`, `55`, `70`, `101`…)
are accepted by the backend (it forwards any string) but not exposed in the
UI.

Per Billit docs: the ventilation code on the header governs lines with 0% VAT
(TaxCategory). For non-zero rates it is optional but Syncora always sends it.

## 6.6 Delete order — `DELETE {URL}/orders/{order_id}`

Source: `controllers/billit.py:79`. Called from `delete_bill`/`delete_cnote`
when `externalId` is set. Billit returns body `true` on success; Syncora treats
`response.content == b"true"` as success and otherwise returns the error text.

## 6.7 Peppol status polling — `GET {URL}/orders/{externalId}`

Source: `utils/peppol_poller.py`, Billit "Get Status Info via API" doc.

Syncora reads `CurrentDocumentDeliveryDetails` from the order object:

| Billit value | Local status set |
| --- | --- |
| `IsDocumentDelivered: true` | `SENT` (2) |
| `DocumentDeliveryStatus: "Pending"` (first occurrence) | `PENDING` (1) |
| otherwise | (continue polling) |

Billit also exposes `DocumentDeliveryStatus: "Error"`, `DocumentRefusedReasonTC`,
`DocumentRefusedInfo`, and a `Messages` array (IMR/MLR feedback). **[GAP]**
Syncora does not capture error/refusal feedback or messages — only the
delivered/pending boolean is mirrored locally.

Polling parameters (defaults in `PeppolStatusPoller.__init__`):
`poll_interval=5s`, `max_errors=5`, `timeout=3600s`. The callback is
`OrderModel.set_peppol_status`. **[GAP]** the singleton keeps constructor args
from the first instantiation only (`__new__` returns the cached instance;
`__init__` short-circuits via `_initialized`), so per-call `poll_interval` /
`timeout` overrides after the first poller are ignored.

## 6.8 Billit environment and production readiness

- Current `.env` targets the **sandbox** (`api.sandbox.billit.be/v1`).
- Moving to production is a `.env` change (`URL`, `API_SECRET`, `PARTY_ID`),
  per Billit "Sandbox VS Production" / "Activate on Production". No code
  change is required, but Peppol registration/verification of the company on
  the production network is a prerequisite outside Syncora.
