import asyncio
import threading
from collections.abc import Callable

import requests
from dotenv import dotenv_values
from requests import Response

from constants.order_back import PEPPOL_DELIVERY_STATUS_SENT, PEPPOL_DELIVERY_STATUS_PENDING
from controllers.billit import get_headers


class PeppolStatusPoller:

    _instance = None

    def __init__(self, callback: Callable[[int, int], bool], poll_interval: float = 5.0, max_errors: int = 5, timeout: float = 3600.0):
        if hasattr(self, '_initialized'):
            return
        self._callback = callback
        self._poll_interval = poll_interval
        self._max_errors = max_errors
        self._timeout = timeout
        self._base_url = f"{dotenv_values('.env')['URL']}/orders/"
        self._headers = get_headers()
        self._current_tasks = set()
        self._initialized = True

    def __new__(
        cls,
        callback: Callable[[int, int], bool],
        *,
        poll_interval: float = 5.0,
        max_errors: int = 5,
        timeout: float = 3600.0
    ):
        if cls._instance is None:
            cls._instance = super(PeppolStatusPoller, cls).__new__(cls)
        return cls._instance

    def __call__(self, order_id: int):
        if order_id not in self._current_tasks:
            self._current_tasks.add(order_id)
            thread = threading.Thread(
                target=asyncio.run,
                args=(self._poll_for_peppol_status(order_id),),
                daemon=True,
            )
            thread.start()

    async def _poll_for_peppol_status(self, order_id: int) -> None:
        url = f"{self._base_url}{order_id}"
        headers = get_headers()

        peppol_pending = False
        peppol_delivered = False
        start_time = asyncio.get_running_loop().time()
        no_errors = 0

        while (
            not peppol_delivered
            and (asyncio.get_running_loop().time() - start_time) < self._timeout
            and no_errors < self._max_errors
        ):
            response: Response = requests.get(url, headers=headers)
            if response.status_code not in [200, 201]:
                print(response.text)
                no_errors += 1
                await asyncio.sleep(self._poll_interval)
            else:
                no_errors = no_errors - 1 if no_errors > 0 else 0
                order_data = response.json()
                if order_data.get("CurrentDocumentDeliveryDetails").get("IsDocumentDelivered"):
                    peppol_delivered = True
                    self._callback(order_id, PEPPOL_DELIVERY_STATUS_SENT)
                elif order_data.get("CurrentDocumentDeliveryDetails").get(
                        "DocumentDeliveryStatus") == "Pending" and not peppol_pending:
                    peppol_pending = True
                    self._callback(order_id, PEPPOL_DELIVERY_STATUS_PENDING)
                else:
                    await asyncio.sleep(self._poll_interval)

        self._current_tasks.remove(order_id)
