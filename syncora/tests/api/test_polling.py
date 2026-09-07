"""TC-POLL-1..11 : Peppol status polling (FR-POLL-1..6).

The real ``PeppolStatusPoller`` is used with its singleton reset and short
intervals. The polling coroutine is driven directly with ``asyncio.run`` so
there is no real threading/timing; Billit GET is mocked with ``billit_fake``.
"""

import asyncio
import threading
from typing import TYPE_CHECKING

import pytest

from constants.order_back import (
    PEPPOL_DELIVERY_STATUS_PENDING,
    PEPPOL_DELIVERY_STATUS_SENT,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    import mongomock
    import responses

    from utils.peppol_poller import PeppolStatusPoller

ORDER_URL = "https://billit.test.local/v1/orders/42"


def _details(*, delivered: bool = False, status: str = "Error") -> dict[str, object]:
    return {
        "CurrentDocumentDeliveryDetails": {
            "IsDocumentDelivered": delivered,
            "DocumentDeliveryStatus": status,
        }
    }


def _run(
    poller_cls: type, callback: Callable[[int, int], bool], **kwargs: object
) -> object:
    return poller_cls(callback, **kwargs)  # type: ignore[arg-type]


def _poll_for(p: object, order_id: int = 42) -> None:
    """Drive the coroutine directly. ``__call__`` normally adds the id to
    ``_current_tasks`` first; we mimic that so the final ``remove`` succeeds."""
    p._current_tasks.add(order_id)  # type: ignore[attr-defined]
    asyncio.run(p._poll_for_peppol_status(order_id))  # type: ignore[attr-defined]


# --- Status transitions (TC-POLL-1..3) ----------------------------------- #
def test_poll_delivered_sets_sent_and_stops(
    poller: type[PeppolStatusPoller], billit_fake: responses.RequestsMock
) -> None:
    # TC-POLL-1
    calls: list[tuple[int, int]] = []
    billit_fake.add(
        billit_fake.GET, ORDER_URL, json=_details(delivered=True), status=200
    )
    p = _run(
        poller,
        lambda oid, st: calls.append((oid, st)),
        poll_interval=0.0,
        max_errors=5,
        timeout=10.0,
    )
    _poll_for(p)
    assert calls == [(42, PEPPOL_DELIVERY_STATUS_SENT)]
    assert len(billit_fake.calls) == 1


def test_poll_pending_then_delivered(
    poller: type[PeppolStatusPoller], billit_fake: responses.RequestsMock
) -> None:
    # TC-POLL-2
    calls: list[tuple[int, int]] = []
    billit_fake.add(
        billit_fake.GET, ORDER_URL, json=_details(status="Pending"), status=200
    )
    billit_fake.add(
        billit_fake.GET, ORDER_URL, json=_details(delivered=True), status=200
    )
    p = _run(
        poller,
        lambda oid, st: calls.append((oid, st)),
        poll_interval=0.0,
        max_errors=5,
        timeout=10.0,
    )
    _poll_for(p)
    assert calls == [
        (42, PEPPOL_DELIVERY_STATUS_PENDING),
        (42, PEPPOL_DELIVERY_STATUS_SENT),
    ]


def test_poll_pending_reported_twice_sets_pending_once(
    poller: type[PeppolStatusPoller], billit_fake: responses.RequestsMock
) -> None:
    # TC-POLL-3
    calls: list[tuple[int, int]] = []
    for _ in range(2):
        billit_fake.add(
            billit_fake.GET, ORDER_URL, json=_details(status="Pending"), status=200
        )
    billit_fake.add(
        billit_fake.GET, ORDER_URL, json=_details(delivered=True), status=200
    )
    p = _run(
        poller,
        lambda oid, st: calls.append((oid, st)),
        poll_interval=0.0,
        max_errors=5,
        timeout=10.0,
    )
    _poll_for(p)
    pending_count = sum(1 for _, st in calls if st == PEPPOL_DELIVERY_STATUS_PENDING)
    assert pending_count == 1


# --- Error / timeout behaviour (TC-POLL-4..5, 7) ------------------------ #
def test_poll_five_errors_stops_without_advancing(
    poller: type[PeppolStatusPoller], billit_fake: responses.RequestsMock
) -> None:
    # TC-POLL-4
    calls: list[tuple[int, int]] = []
    for _ in range(6):
        billit_fake.add(billit_fake.GET, ORDER_URL, json={}, status=500)
    p = _run(
        poller,
        lambda oid, st: calls.append((oid, st)),
        poll_interval=0.0,
        max_errors=5,
        timeout=10.0,
    )
    _poll_for(p)
    assert calls == []
    assert len(billit_fake.calls) == 5


def test_poll_timeout_reached_without_delivery(
    poller: type[PeppolStatusPoller], billit_fake: responses.RequestsMock
) -> None:
    # TC-POLL-5 : a non-delivering, non-pending response then a timeout
    calls: list[tuple[int, int]] = []
    billit_fake.add(
        billit_fake.GET, ORDER_URL, json=_details(status="Error"), status=200
    )
    p = _run(
        poller,
        lambda oid, st: calls.append((oid, st)),
        poll_interval=0.01,
        max_errors=5,
        timeout=0.005,
    )
    _poll_for(p)
    assert calls == []
    assert len(billit_fake.calls) == 1


def test_poll_error_count_decays_on_success(
    poller: type[PeppolStatusPoller], billit_fake: responses.RequestsMock
) -> None:
    # TC-POLL-7 : a success between errors decays the counter (no reset-to-0
    # abruptly), so interleaved errors do not trip the max_errors threshold.
    calls: list[tuple[int, int]] = []
    billit_fake.add(billit_fake.GET, ORDER_URL, json={}, status=500)
    billit_fake.add(
        billit_fake.GET, ORDER_URL, json=_details(status="Error"), status=200
    )
    billit_fake.add(billit_fake.GET, ORDER_URL, json={}, status=500)
    billit_fake.add(
        billit_fake.GET, ORDER_URL, json=_details(delivered=True), status=200
    )
    p = _run(
        poller,
        lambda oid, st: calls.append((oid, st)),
        poll_interval=0.0,
        max_errors=2,
        timeout=10.0,
    )
    _poll_for(p)
    assert calls == [(42, PEPPOL_DELIVERY_STATUS_SENT)]
    assert len(billit_fake.calls) == 4


# --- Concurrency / singleton (TC-POLL-6, 11) --------------------------- #
@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_poll_only_one_background_task_per_id(
    poller: type[PeppolStatusPoller], monkeypatch: pytest.MonkeyPatch
) -> None:
    # TC-POLL-6 : a second call for the same id is a no-op
    starts: list[object] = []
    monkeypatch.setattr(threading.Thread, "start", lambda self: starts.append(self))
    p = _run(poller, lambda *_a: None, poll_interval=0.0, max_errors=5, timeout=10.0)
    p(42)
    p(42)
    assert len(starts) == 1
    assert 42 in p._current_tasks


def test_poller_is_a_process_singleton(poller: type[PeppolStatusPoller]) -> None:
    # TC-POLL-11
    a = _run(poller, lambda *_a: None, poll_interval=0.0)
    b = _run(poller, lambda *_a: None, poll_interval=99.0)
    assert a is b


@pytest.mark.gap
def test_poller_singleton_ignores_later_constructor_args(
    poller: type[PeppolStatusPoller],
) -> None:
    # TC-GAP-14 : the singleton keeps the first instance's args
    first = _run(poller, lambda *_a: None, poll_interval=1.0)
    second = _run(poller, lambda *_a: None, poll_interval=99.0)
    assert second is first
    assert first._poll_interval == 1.0


# --- Persistence via callback (TC-POLL-10) ----------------------------- #
def test_poll_persists_status_via_callback(
    poller: type[PeppolStatusPoller],
    billit_fake: responses.RequestsMock,
    mongo: mongomock.Database,
) -> None:
    # TC-POLL-10 : the callback updates the fake Mongo doc
    from models.bills import BillModel

    bill_id = (
        mongo["bills"]
        .insert_one(
            {"orderNumber": "2026-001", "externalId": 42, "peppolDeliveryStatus": 0}
        )
        .inserted_id
    )
    billit_fake.add(
        billit_fake.GET, ORDER_URL, json=_details(delivered=True), status=200
    )
    p = _run(
        poller,
        BillModel.set_peppol_status,
        poll_interval=0.0,
        max_errors=5,
        timeout=10.0,
    )
    _poll_for(p)
    assert (
        mongo["bills"].find_one({"_id": bill_id})["peppolDeliveryStatus"]
        == PEPPOL_DELIVERY_STATUS_SENT
    )


# TC-POLL-8 / TC-POLL-9 (get_one triggers/skips poll) are covered in
# tests/api/test_bills.py::test_get_bill_triggers_poll_* and
# test_get_bill_does_not_poll_when_not_sent_or_sent.
