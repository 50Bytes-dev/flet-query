import asyncio
from typing import Awaitable, Callable, Optional

from .type import TData


class RetryResolver:
    is_running: bool = False
    on_cancel: Optional[Callable[[], Awaitable[None]]] = None

    async def resolve(
        self,
        fetcher: Callable[[], Awaitable[TData]],
        on_resolve: Callable[[TData], Awaitable[None]],
        on_error: Callable[[Exception], Awaitable[None]],
        on_cancel: Callable[[], Awaitable[None]],
        retry_count: int = 3,
        retry_delay: int = 1500,
    ):
        self.on_cancel = on_cancel
        if self.is_running:
            return
        self.is_running = True

        attempts = 0
        while attempts != retry_count:
            attempts += 1

            if not self.is_running:
                return

            is_last_attempt = attempts == retry_count
            try:
                value = await fetcher()
                if not self.is_running:
                    return
                await on_resolve(value)
                break
            except Exception as error:
                if is_last_attempt:
                    await on_error(error)
                    break
                await asyncio.sleep(retry_delay / 1000)
        self.reset()

    async def cancel(self):
        self.is_running = False
        if self.on_cancel:
            await self.on_cancel()

    def reset(self):
        self.is_running = False
