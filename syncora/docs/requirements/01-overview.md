# 01 — Overview

## 1.1 Product purpose

Syncora is the backend of an invoicing application used by **ANTOONS Luc BV/SRL**
(see `src/pdf/static_data.py`), a small architectural practice. It lets the
user:

- maintain a customer registry,
- draft sales invoices ("bills") and credit notes ("cnotes"),
- generate bilingual (French / Dutch) PDF documents for them,
- register each document on the **Billit** e-invoicing platform, and
- dispatch the registered document over the **Peppol** e-invoicing network,
  tracking its delivery status.

The backend is a thin REST API consumed by a React single-page application
(`../frontend`). It is not a general-purpose accounting engine: it deliberately
delegates VAT/totals calculation semantics and e-invoicing compliance to Billit
(see `06-billit-and-peppol-integration.md`).

## 1.2 In scope / out of scope

**In scope (backend):**

- REST endpoints under `/api/*` for customers, bills, credit notes, and files.
- Persistence of customers (MS Access) and orders (MongoDB).
- Billit order creation, Peppol send command, order deletion, and status
  polling.
- PDF generation for bills, credit notes, and customers.

**Out of scope (owned by other components):**

- The web UI (React frontend).
- Accounting/tax computation beyond what is needed to mirror Billit's
  taxable-amount totals method (see `05-business-rules.md` §5).
- Receiving supplier invoices via Peppol (Billit supports it; Syncora does
  not).
- Authentication/authorization of API callers (see `08-non-functional-requirements.md`).

## 1.3 Users and context

| Actor | Role |
| --- | --- |
| Architect / office staff | Single operational user. Creates customers, invoices, credit notes; triggers Billit registration and Peppol sending. |
| Billit platform | External system. Syncora authenticates with an API key + party ID and treats Billit as the source of truth for order identity (`externalId`) and delivery status. |
| Peppol network | Transport for e-invoices. Reachable only through Billit's send command. |

The application is single-tenant: all orders belong to the one company
identified by `PARTY_ID` in `.env`.

## 1.4 Environments

Two Billit environments exist (per Billit docs "Sandbox VS Production"):

| Environment | Billit API base URL | Used by Syncora via |
| --- | --- | --- |
| Sandbox | `https://api.sandbox.billit.be/v1` | `.env` `URL` (current default) |
| Production | `https://api.billit.be/v1` | `.env` `URL` (switch to go live) |

`.env` keys (from `README.md` and `src/database/*.py`, `controllers/billit.py`):

| Key | Purpose |
| --- | --- |
| `API_SECRET` | Billit API key, sent as the `apiKey` header. |
| `PARTY_ID` | Billit company ID, sent as `partyID` and `contextPartyID` headers. |
| `URL` | Billit API base URL (sandbox or production). |
| `DB_FILE` | Path to the MS Access `.accdb` file (the `Client` table). |
| `MONGO_IP`, `MONGO_PORT`, `MONGO_USER`, `MONGO_PWD`, `MONGO_DB` | MongoDB connection coordinates for the orders database. |

## 1.5 Glossary

| Term | Meaning |
| --- | --- |
| **Bill** | A sales invoice (`Invoice` OrderType). Stored in MongoDB collection `bills`. |
| **Cnote** | A credit note (`CreditNote` OrderType). Stored in MongoDB collection `cnotes`. |
| **Order** | Collective term for a bill or a credit note; both share the `OrderBack` data model. |
| **externalId** | The integer ID Billit returns when an order is created. Stored locally; 0 means "not yet registered on Billit". |
| **Locked** | An order that has been sent to Billit (`externalId > 0`) and can no longer be edited. |
| **Undeletable** | An order whose Peppol delivery status is anything other than `NOT_SENT` (-1); cannot be deleted. |
| **Peppol delivery status** | Local mirror of Billit's `CurrentDocumentDeliveryDetails`: -1 not sent, 0 unknown, 1 pending, 2 sent. |
| **OGM** | Structured communication reference (`+++xxx/xxxx/xxxNN+++`) derived from the order number; bills only. |
| **Ventilation code** | Billit VAT/tax category code carried on the order header (e.g. `2` = 6%, `4` = 21%, `21` = co-contractant / reverse charge). |
| **aboutInvoiceNumber** | The invoice number a credit note refers to. Its presence is what distinguishes a credit note from a bill. |
| **Front / Back** | The `*Front` types are the API contract with the frontend; the `*Back` types are the internal Pydantic models. |
| **Undefined** | A sentinel (`SyncoraUndefined`) meaning "field was never provided", distinct from `None`/empty. Drives serialization and the `is_cnote` test. |

## 1.6 Source map

Quick map from concern → primary source files (all paths relative to `syncora/`):

| Concern | Files |
| --- | --- |
| App entry & blueprint wiring | `src/app.py`, `src/routes/__init__.py` |
| HTTP routes | `src/routes/bills.py`, `customers.py`, `cnotes.py`, `files.py` |
| Business logic | `src/controllers/bills.py`, `customers.py`, `cnotes.py`, `files.py` |
| Billit client | `src/controllers/billit.py` |
| Peppol polling | `src/utils/peppol_poller.py` |
| Data models (Pydantic) | `src/constants/order_back.py`, `customer_back.py`, `order_billit.py`, `customer_billit.py`, `order_front.py`, `order_pdf.py`, `all.py` |
| Persistence — orders | `src/models/order_model.py`, `bills.py`, `cnotes.py` |
| Persistence — customers | `src/models/customers.py` |
| DB connectors | `src/database/mongodb.py`, `access.py` |
| PDF generation | `src/controllers/bill_gen.py`, `cnote_gen.py`, `src/pdf/static_data.py`, `src/pdf/templates/*.html` |
| Errors | `src/utils/generic_error.py` |
| Base model | `src/classes/syncora_db_class.py` |
