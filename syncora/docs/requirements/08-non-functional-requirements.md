# 08 — Non-Functional Requirements

## 8.1 Security

| ID | Requirement | Status |
| --- | --- | --- |
| NFR-SEC-1 | The API shall not be exposed unauthenticated on a public network. | **[GAP]** There is no auth on `/api/*`; security relies entirely on the docker-compose private bridge network (`172.18.10.0/24`) and the frontend proxy. |
| NFR-SEC-2 | Billit credentials (`API_SECRET`) shall be kept in `.env` and never logged. | Mostly; `print(response.text)` on Billit errors could leak bodies, and `dotenv_values` is called inline. |
| NFR-SEC-3 | The `.env` file shall not be committed. | Covered by the root `.gitignore`; the committed `syncora/.env` in this checkout is a local secret file — **[GAP]** it contains live sandbox credentials and should be rotated/removed from the working tree. |
| NFR-SEC-4 | Customer PII (comment-derived emails/phones) shall only be returned to the trusted frontend. | OK given NFR-SEC-1. |

## 8.2 Reliability & error handling

| ID | Requirement | Status |
| --- | --- | --- |
| NFR-REL-1 | Unhandled `SyncoraError` (negative totals 903–905, missing `externalId`/`peppolDeliveryStatus` 906, customer name missing 1000) shall produce a controlled JSON error, not a 500. | **[GAP]** No `@app.errorhandler`; these surface as HTML 500. |
| NFR-REL-2 | `ItemNotFoundError` (HTTP 400) from `get_one` shall be returned as a structured error. | **[GAP]** unhandled. |
| NFR-REL-3 | Billit HTTP failures shall be forwarded to the caller as `error` envelopes, not crash. | OK (`send_billit`/`send_peppol` catch status). |
| NFR-REL-4 | The Peppol poller shall not block request handling (daemon thread). | OK. |
| NFR-REL-5 | A missing referenced invoice in `cnotes.pre_peppol_checks` shall not raise `IndexError`. | **[GAP]** (`controllers/cnotes.py:165`). |

## 8.3 Performance & concurrency

| ID | Requirement | Status |
| --- | --- | --- |
| NFR-PERF-1 | Customer reads/writes shall be serialised through a single lock (MS Access constraint). | OK (`SmartAccessConnector.lock`). Throughput is bounded by the Access DB. |
| NFR-PERF-2 | MongoDB access shall reuse a connection pool rather than opening a client per request. | **[GAP]** `mongodb.get_connection()` creates+closes a `MongoClient` per call. |
| NFR-PERF-3 | `.env` lookups shall be cached rather than re-read on every Billit call. | **[GAP]** `dotenv_values(".env")[...]` repeated. |
| NFR-PERF-4 | Billit calls use `requests` with **no timeout** (`# noqa: S113`). | **[GAP]** a hung Billit can block a worker indefinitely. Add explicit timeouts. |
| NFR-PERF-5 | Listing bills/cnotes shall scale to the full collection (no pagination/filter). | **[ASSUMPTION]** acceptable for a single small practice; `Model.get()` returns all docs. |

## 8.4 Data integrity

| ID | Requirement | Status |
| --- | --- | --- |
| NFR-DI-1 | `orderNumber` uniqueness within a collection shall be enforced at the DB level. | **[GAP]** only enforced in controller code; add a Mongo unique index. |
| NFR-DI-2 | Orders shall always have `externalId` and `peppolDeliveryStatus` set on creation. | OK (`OrderModel.create` sets defaults). |
| NFR-DI-3 | The `.accdb` connection shall auto-refresh when the file changes on disk. | OK (`SmartAccessConnector` mtime check). |

## 8.5 Observability

| ID | Requirement | Status |
| --- | --- | --- |
| NFR-OBS-1 | The backend shall log Billit failures and poller errors. | Partial — uses `print(...)` only; no logging framework. **[GAP]** no structured logging. |
| NFR-OBS-2 | The backend shall not leak full responses to stdout in production. | **[GAP]** `print(response.text)` and `print(order_back.to_front())` exist. |

## 8.6 Maintainability & tooling

| ID | Requirement | Status |
| --- | --- | --- |
| NFR-MAINT-1 | Code shall pass `prek run --all-files` (Black, Ruff, pyupgrade, isort). | Configured (`prek.toml`). |
| NFR-MAINT-2 | Tests shall run under pytest with `pythonpath = ["src"]`. | Configured (`pyproject.toml`). **[GAP]** the `tests/` tree currently contains only compiled `.pyc` artifacts; the `.py` sources are absent, so the suite cannot run from the repo as-is. |
| NFR-MAINT-3 | The Python runtime version shall be consistent across `pyproject.toml`, `README.md`, and `Dockerfile`. | **[GAP]** `pyproject`/README say ≥3.14, Dockerfile pins 3.13. |
| NFR-MAINT-4 | Dead/duplicated code (controller-level `detect_*` helpers, `is_old_db_comment`) shall be removed or wired in. | **[GAP]**. |

## 8.7 Operability

- Local dev: `uv run python3 src/app.py` (Flask debug).
- Container: Gunicorn on `:5000` (single worker by default in `Dockerfile`
  CMD; no `--workers`/`--threads` specified). The Access lock and the
  per-request Mongo client mean horizontal scaling to multiple backend
  containers is **not** supported as-is (Access DB file is a mounted single
  copy; Mongo would be shared). **[GAP]** document single-instance constraint.
- The Access DB file is mounted read/write from a NAS path
  (`docker-compose.yaml`); concurrent writes from multiple backend replicas
  would corrupt it.
