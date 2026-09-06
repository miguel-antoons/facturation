# 02 — Architecture and Data

## 2.1 High-level architecture

```
React frontend (../frontend)
      |  fetch /api/*  (Vite dev proxy :5000, prod nginx proxy)
      v
Flask app  (src/app.py)
  |-- routes/        HTTP layer, blueprints
  |-- controllers/   orchestration + validation gates
  |-- models/         persistence (Mongo + Access)
  |-- constants/      Pydantic data models / DTOs
  |-- pdf/            HTML->PDF generation
  |-- utils/          peppol poller, errors
      |
      +--> MongoDB (orders: bills, cnotes)
      +--> MS Access .accdb (customers: Client table)
      +--> Billit REST API (api.sandbox.billit.be/v1)
              +--> Peppol network (via Billit send command)
```

The backend is a layered monolith. The flow for a request is:

`route → controller → (model → database) → jsonify(response)`.

There is no service/repository abstraction beyond `models/`; controllers
call models directly and also call the Billit client (`controllers/billit.py`).

## 2.2 Technology stack

| Layer | Technology | Notes |
| --- | --- | --- |
| Web framework | Flask 3 (`src/app.py`) | Blueprints registered in `routes/__init__.py`. |
| Validation/DTOs | Pydantic v2 | `SyncoraModel` base + custom `Undefined` sentinel (`constants/all.py`). |
| Orders DB | MongoDB via PyMongo 4 | `database/mongodb.py`; per-request `MongoClient` via context manager. |
| Customers DB | MS Access via JDBC/UCanAccess | `database/access.py` + `jaydebeapi`; requires a JVM (Docker image installs `default-jdk`). |
| Billit client | `requests` | `controllers/billit.py`. |
| PDF | WeasyPrint + Jinja2 + PyPDF2 | `controllers/bill_gen.py`, `cnote_gen.py`; ReportLab for the simple customer PDF. |
| Dates | `python-dateutil` | Order date parsing/formatting (`constants/order_back.py`). |
| Runtime | Python ≥ 3.14 (`pyproject.toml`, `README.md`) | **[GAP]** `docker/Dockerfile` pins `python:3.13`; the image and the declared requirement disagree. |
| WSGI | Gunicorn | `docker/Dockerfile` CMD; `app.run(debug=True)` only when run directly. |
| Lint/format | prek (Black, Ruff, pyupgrade, isort) | `prek.toml`. |
| Tests | pytest, `pythonpath = ["src"]` | `tests/` (sources present as compiled `.pyc`; see `08` NFRs). |

## 2.3 Customers storage — MS Access

Source: `src/database/access.py`, `src/models/customers.py`,
`src/constants/customer_back.py`.

- Connection is a process-wide singleton `SmartAccessConnector` (`access._db`),
  lazily created from `DB_FILE` + the bundled `ucanaccess-5.1.3-uber.jar`.
- The connector **reconnects** when the `.accdb` file's mtime changes or the
  connection has been idle longer than `idle_timeout_sec` (10080 s = 7 days in
  `get_connection()`).
- All queries go through `execute_query()`, which holds a single
  `threading.Lock` for the **entire** operation — MS Access is effectively
  single-writer and Syncora serialises all access (see NFRs).
- The `Client` table uses French column names:

  | API field | Access column |
  | --- | --- |
  | id | `Numero` |
  | name | `Nom` |
  | surname | `Prenom` |
  | company | `Societe` |
  | comment | `Commentaire` |
  | address | `Adresse` |
  | postal_code | `Codepostal` |
  | city | `Localite` |
  | vat_number | `TVA` |
  | language | `Langue` |
  | architect_name | `Nom Architecte` |
  | salutation | `Titre` |

- Address is stored as a single `Adresse` string; `street`/`number` are
  **computed** by splitting on `","` (street = first part, number = remainder).
  On write, `street` + `number` are reassembled into `"<street> , <number>"`.
- `emails`, `telephoneNumbers`, `mobileNumbers` are **computed** from
  `comment` by regex (see `05-business-rules.md` §6). They are not stored.
- `CustomerModel.create` returns `MAX(Numero)` after insert (AutoNumber
  column).

## 2.4 Orders storage — MongoDB

Source: `src/models/order_model.py`, `src/database/mongodb.py`.

- Two collections, both shaped by `OrderBack`: `bills` and `cnotes`
  (`BillModel.database_name`, `CnoteModel.database_name`).
- Each order document's `_id` is a Mongo `ObjectId`; it is exposed to the
  frontend as the string `orderId`. The frontend treats `"0"` as "new order".
- `externalId` (int, default 0) and `peppolDeliveryStatus` (int, default -1)
  are added on `create()` and updated by `set_external_id` /
  `set_peppol_status`.
- `get_connection()` opens a **new** `MongoClient` per call and closes it in the
  `finally` block — there is no connection pool (see NFRs).

`OrderModel` operations (`models/order_model.py`):

| Method | Behaviour |
| --- | --- |
| `get_one(order_id)` | `find_one({_id: ObjectId})`; raises `ItemNotFoundError` if absent. |
| `get(condition)` | `find(condition or {})` → list. |
| `create(order)` | sets `externalId=0`, `peppolDeliveryStatus=-1`, `insert_one`, returns inserted id string. |
| `update(order_id, order)` | `update_one` `$set` of the dumped order. |
| `delete(order_id)` | `delete_one`. |
| `contains(order_number)` | `find_one({orderNumber})` truthiness. |
| `set_peppol_status(external_id, status)` | updates by `externalId`. |
| `set_external_id(order_id, external_id)` | updates by `_id`. |

## 2.5 Data models

### 2.5.1 Base model and the `Undefined` sentinel — `constants/all.py`

- `Undefined` is a falsy singleton (`SyncoraUndefined`). `SyncoraModel`
  (abstract Pydantic `BaseModel`) installs a wrap serializer that **drops**
  any field whose value is an `Undefined` instance from the output dict.
- `SyncoraModel.ret_def(val, alt)` returns `val` if it is `Undefined`, else
  `alt` — used by computed fields to distinguish "not provided" from "empty".
- Subclasses implement `from_db`, `to_db`, `to_front`.

### 2.5.2 `OrderBack` — `constants/order_back.py`

Fields (all default to `SyncoraUndefined` unless noted):

| Field | Type / alias | Notes |
| --- | --- | --- |
| `orderId` | str, alias `_id` | `ObjectId` converted to str on validate. |
| `customerId` | int | FK to `Client.Numero`. |
| `customerName` | str | Only set on list responses (computed by controllers). |
| `externalId` | int | Billit order ID; 0 = not registered. |
| `orderNumber` | str | Human invoice/cnote number. Unique within collection (enforced on create/update). |
| `orderDate`, `expiryDate`, `deliveryDate` | str | ISO-ish date strings. |
| `orderTitle` | str | Invoice subject ("Objet"). |
| `orderLines` | `list[_OrderLineBack]` | Default `[]`. |
| `ventilationCode` | str | Billit VAT code ("1","2","4","21",…). |
| `aboutInvoiceNumber` | str | Present ⇒ credit note. |
| `peppolDeliveryStatus` | int | -1/0/1/2. |

Computed properties: `billitSent`, `totalExcl`, `totalIncl`, `totalVAT`,
`ogm`, `is_cnote`, `locked`, `undeletable`, `formatted_order_date`,
`formatted_delivery_date`, `formatted_expiry_date` (see `05-business-rules.md`).

`_OrderLineBack`: `description`, `quantity`, `unitPriceExcl`, `unit`,
`VATPercentage`; computed `total_excl`, `total_incl`, `total_vat` (per-line,
rounded to 2 dp).

### 2.5.3 `CustomerBack` — `constants/customer_back.py`

Fields with Access aliases (see §2.3). Computed: `street`, `number`,
`emails`, `telephoneNumbers`, `mobileNumbers`, `hasVAT`, `hasEmail`.
Validators: `assemble_address_from_front` (build `Adresse` from street+number
on input), `ensure_language_lower` (language lowercased).

### 2.5.4 Billit DTOs — `constants/order_billit.py`, `customer_billit.py`

- `OrderBillit`: maps `OrderBack` → Billit JSON. `OrderType` computed
  (`CreditNote` if `AboutInvoiceNumber` else `Invoice`), `OrderDirection` =
  `Income`. Carries `Customer`, `OrderLines`, totals, `VentilationCode`,
  `OrderPDF` (base64).
- `CustomerBillit`: maps `CustomerBack` → Billit customer. `CountryCode`
  defaults `BE`; builds a single `InvoiceAddress`. `Language` upper-cased.
  At least one of `Name`/`ContactFirstName`/`ContactLastName` required.
- `OrderLinesBillit`: per-line Billit shape; `Description` non-empty enforced.

### 2.5.5 Frontend contract types — `constants/order_front.py`

TypedDicts that document the JSON the frontend sends/expects:
`OrderLineFront`, `OrderFrontShort` (list rows), `OrderFront` (full edit
payload). The actual JSON the frontend sends is built in
`../frontend/src/pages/billing.tsx` / `creditNote.tsx` (see `03-api-specification.md`).

## 2.6 Response envelope

Source: `constants/all.py` (`ResponseMessage`), used across controllers.

```python
class ResponseMessage(TypedDict):
    id: NotRequired[int | str]
    status: str            # "success" | "error" | "warning"
    message: NotRequired[str]
    code: NotRequired[int]
```

- `status` is one of `RESPONSE_SUCCESS`, `RESPONSE_ERROR`, `RESPONSE_WARNING`.
- Mutating endpoints return `{status, id}` on success, `{status, message}` on
  validation warnings/errors, or `{status, message}` forwarding Billit's error
  JSON on Billit failures.

## 2.7 Error model — `utils/generic_error.py`

- `SyncoraError(message, error_code, severity)` with `Severity` enum.
- `ItemNotFoundError` (HTTP 400) raised by `OrderModel.get_one` when an order
  id is missing.
- Negative calculated totals raise `SyncoraError` (codes 903–905); missing
  `externalId`/`peppolDeliveryStatus` for `locked`/`undeletable` raise code
  906. These are **unhandled** at the route layer today (see NFRs `[GAP]`).

## 2.8 Configuration & deployment

- Local run: `uv run python3 src/app.py` (Flask dev server, debug on).
- Container: `docker/Dockerfile` builds `python:3.13` + JDK, runs Gunicorn on
  `:5000`. The `.accdb` file and `.env` are mounted (see root
  `docker-compose.yaml`).
- The frontend container depends on the backend container; both sit on a
  fixed-subnet bridge network (`172.18.10.0/24`). There is no TLS at the
  backend; the frontend container serves port 80.
