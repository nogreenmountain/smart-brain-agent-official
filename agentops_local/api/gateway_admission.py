"""Bounded FIFO admission for one gateway process; no database or model calls."""
from __future__ import annotations

import asyncio
from collections import deque
from contextlib import asynccontextmanager


class AdmissionRejected(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class AdmissionQueue:
    def __init__(self, max_active: int, max_waiting: int, timeout: float):
        if max_active < 1 or max_waiting < 0 or timeout <= 0:
            raise ValueError('Invalid gateway admission limits')
        self.max_active, self.max_waiting, self.timeout = max_active, max_waiting, timeout
        self.active = 0
        self._waiters: deque[asyncio.Future] = deque()

    @property
    def waiting(self) -> int:
        return len(self._waiters)

    def _release(self):
        self.active -= 1
        while self._waiters:
            waiter = self._waiters.popleft()
            if not waiter.done():
                self.active += 1
                waiter.set_result(None)
                break

    async def _acquire(self, disconnected=None):
        if self.active < self.max_active and not self._waiters:
            self.active += 1
            return
        if self.waiting >= self.max_waiting:
            raise AdmissionRejected('gateway_queue_full')
        waiter = asyncio.get_running_loop().create_future()
        self._waiters.append(waiter)
        async def wait():
            if disconnected is None:
                await asyncio.shield(waiter)
                return
            while not waiter.done():
                if await disconnected():
                    raise AdmissionRejected('gateway_client_disconnected')
                try:
                    await asyncio.wait_for(asyncio.shield(waiter), .05)
                except TimeoutError:
                    pass
        try:
            await asyncio.wait_for(wait(), self.timeout)
        except BaseException as error:
            if waiter.done() and not waiter.cancelled():
                self._release()
            else:
                self._waiters.remove(waiter)
                waiter.cancel()
            if isinstance(error, TimeoutError):
                raise AdmissionRejected('gateway_queue_timeout') from None
            raise

    @asynccontextmanager
    async def slot(self, disconnected=None):
        await self._acquire(disconnected)
        try:
            yield
        finally:
            self._release()
