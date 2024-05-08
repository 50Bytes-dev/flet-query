from datetime import datetime, timedelta
from threading import Timer
from typing import TYPE_CHECKING, Callable, Generic, Optional

import flet as ft

from .change_notifier import ChangeNotifier
from .retry_resolver import RetryResolver
from .query import Query, QueryKey, QueryOptions
from .type import DispatchAction, RefetchOnMount, TData, TError

if TYPE_CHECKING:
    from .query_client import QueryClient
    from .hooks.use_query import UseQueryOptions

QueryFn = Callable[[], TData]


class Observer(ChangeNotifier, Generic[TData, TError]):
    query_key: QueryKey
    client: "QueryClient"
    fetcher: QueryFn
    query: Query[TData, TError]

    options: QueryOptions[TData, TError]
    resolver: RetryResolver = RetryResolver()
    refetch_timer: Optional[Timer] = None

    def __init__(
        self,
        query_key: QueryKey,
        fetcher: QueryFn,
        client: "QueryClient",
        options: "UseQueryOptions",
    ):
        super().__init__()

        self.query_key = query_key
        self.fetcher = fetcher
        self.client = client

        self.query = client.query_cache.build(
            query_key=query_key,
            query_client=client,
        )
        self.set_options(options)
        self.query.set_cache_duration(self.options.cache_duration)

    async def update_options(
        self,
        options: "UseQueryOptions",
    ):
        refetch_interval_changed = (
            self.options.refetch_interval != options.refetch_interval
        )
        is_enabled_changed = self.options.enabled != options.enabled

        self.set_options(options)

        if is_enabled_changed:
            if options.enabled:
                self.fetch()
            else:
                await self.resolver.cancel()
                if self.refetch_timer:
                    self.refetch_timer.cancel()

        if options.cache_duration is not None:
            self.query.set_cache_duration(options.cache_duration)

        if refetch_interval_changed:
            if options.refetch_interval is not None:
                self.schedule_refetch()
            else:
                if self.refetch_timer:
                    self.refetch_timer.cancel()
                    self.refetch_timer = None

    def fetch(self):
        ft.context.page.run_task(self.fetch_async)

    async def fetch_async(self):
        if not self.options.enabled or self.query.state.is_fetching:
            return

        await self.query.dispatch(DispatchAction.fetch, None)

        async def on_resolve(data: TData):
            await self.query.dispatch(DispatchAction.success, data)

        async def on_error(error):
            await self.query.dispatch(DispatchAction.error, error)

        async def on_cancel():
            await self.query.dispatch(DispatchAction.cancel_fetch, None)

        await self.resolver.resolve(
            fetcher=self.fetcher,
            on_resolve=on_resolve,
            on_error=on_error,
            on_cancel=on_cancel,
        )

    async def on_query_updated(self):
        self.notify_listeners()
        if self.query.state.is_invalidated:
            self.fetch()

    async def destroy(self):
        self.query.unsubscribe(self)
        await self.resolver.cancel()
        if self.refetch_timer:
            self.refetch_timer.cancel()

    def schedule_refetch(self):
        if self.options.refetch_interval is None:
            return

        if self.refetch_timer:
            self.refetch_timer.cancel()

        self.refetch_timer = Timer(
            self.options.refetch_interval / 1000,
            self.fetch,
        )
        self.refetch_timer.run()

    def set_options(
        self,
        options: "UseQueryOptions",
    ):
        self.options = QueryOptions[TData, TError](
            enabled=options.enabled,
            refetch_on_mount=options.refetch_on_mount
            or self.client.default_query_options.refetch_on_mount,
            stale_duration=options.stale_duration
            or self.client.default_query_options.stale_duration,
            cache_duration=options.cache_duration
            or self.client.default_query_options.cache_duration,
            refetch_interval=options.refetch_interval,
            retry_count=options.retry_count,
            retry_delay=options.retry_delay,
        )

    async def initialize(self):
        self.query.subscribe(self)

        if self.options.enabled is False:
            return

        is_refetching = not self.query.state.is_loading
        is_invalidated = self.query.state.is_invalidated

        if is_refetching and not is_invalidated:
            if self.options.refetch_on_mount == RefetchOnMount.always:
                self.fetch()
            elif self.options.refetch_on_mount == RefetchOnMount.stale:
                is_stale = True
                stale_at = None
                if self.query.state.data_updated_at:
                    stale_at = self.query.state.data_updated_at + timedelta(
                        milliseconds=self.options.stale_duration
                    )
                    is_stale = stale_at < datetime.now()
                if is_stale:
                    self.fetch()
            elif self.options.refetch_on_mount == RefetchOnMount.newer:
                pass
        else:
            self.fetch()
