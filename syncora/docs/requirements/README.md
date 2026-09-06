# Syncora Backend — Requirements

This directory captures the requirements for the **Syncora** backend, the Flask
service that powers the `facturation` invoicing application. The requirements
were reverse-engineered from the backend source in `syncora/src/`, the Billit
API documentation at <https://docs.billit.be/docs>, and the way the sibling
React frontend (`../frontend/src`) consumes the API.

## Document index

| Document | Contents |
| --- | --- |
| [01-overview.md](01-overview.md) | Product purpose, scope, users, glossary, environment, and a trace of which code files back each requirement. |
| [02-architecture-and-data.md](02-architecture-and-data.md) | Component architecture, technology stack, the two storage systems (MS Access + MongoDB), configuration/environment, and the full data model. |
| [03-api-specification.md](03-api-specification.md) | The REST contract: every endpoint, HTTP method, path parameter, request body, and response shape, matched to the frontend calls. |
| [04-functional-requirements.md](04-functional-requirements.md) | Functional requirements grouped by entity (customers, bills, credit notes, files) and by flow (Billit registration, Peppol sending, status polling). |
| [05-business-rules.md](05-business-rules.md) | Cross-cutting rules: validation gates, the Billit/Peppol state machine, invoice locking, undeletability, total calculation, OGM generation, and credit-note specifics. |
| [06-billit-and-peppol-integration.md](06-billit-and-peppol-integration.md) | Mapping between Syncora data and the Billit REST API, header/authentication handling, and the Peppol delivery-status polling loop. |
| [07-pdf-generation.md](07-pdf-generation.md) | Requirements for the invoice, credit-note, and customer PDF documents (bilingual FR/NL, templating, general-conditions merge). |
| [08-non-functional-requirements.md](08-non-functional-requirements.md) | Reliability, performance, security, concurrency, observability, and tooling constraints. |

## How to read these requirements

- Each functional/API requirement is tagged with a stable ID (e.g. `FR-CUS-1`,
  `API-BILL-3`) so it can be referenced by tests and change requests.
- Where a requirement reflects an observed behaviour in the current code, the
  backing source file is cited (e.g. `controllers/bills.py:33`). Where a
  requirement is implied by the Billit docs or the frontend but is **not** yet
  enforced by the backend, it is marked **[GAP]** with a short rationale.
- Assumptions that could not be confirmed from the code are marked
  **[ASSUMPTION]**.

## Scope of the backend

The backend owns:

1. Customer master data (read/write), persisted in a legacy MS Access
   database (`Client` table).
2. Sales invoices ("bills") and credit notes ("cnotes"), persisted in
   MongoDB.
3. Bilingual (FR/NL) PDF generation for invoices, credit notes, and customers.
4. Registration of invoices/credit notes on the **Billit** e-invoicing
   platform (POST `/v1/orders`), including a self-generated PDF attachment.
5. Sending registered documents via the **Peppol** network
   (POST `/v1/orders/commands/send`).
6. Polling Billit for Peppol delivery status and persisting it locally.

The backend does **not** own the UI. The React frontend is a separate
application that talks to the backend exclusively over the `/api/*` REST
endpoints (proxied in dev via Vite, in production via the docker-compose
network).
