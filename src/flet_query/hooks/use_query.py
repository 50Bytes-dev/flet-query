from dataclasses import dataclass, replace
from datetime import datetime
from typing import Awaitable, Callable, Optional, Any

import flet as ft

from .use_query_client import use_query_client
from ..observer import Observer
from ..query import QueryKey
from ..type import QueryStatus, RefetchOnMount


@dataclass
class UseQueryResult:
    data: Optional[Any]
    data_updated_at: Optional[datetime]
    error: Optional[Exception]
    error_updated_at: Optional[datetime]
    is_error: bool
    is_loading: bool
    is_fetching: bool
    is_success: bool
    status: QueryStatus
    refetch: Callable[[], Any]


@dataclass
class UseQueryOptions:
    """All durations are in milliseconds."""

    enabled: bool
    refetch_on_mount: Optional[RefetchOnMount] = None
    stale_duration: Optional[int] = None
    cache_duration: Optional[int] = None
    refetch_interval: Optional[int] = None
    retry_count: int = 3
    retry_delay: int = 1500


def use_query(
    query_key: QueryKey,
    fetcher: Callable[[], Any],
    enabled: bool = True,
    refetch_on_mount: Optional[RefetchOnMount] = None,
    stale_duration: Optional[int] = None,
    cache_duration: Optional[int] = None,
    refetch_interval: Optional[int] = None,
    retry_count: int = 3,
    retry_delay: int = 1500,
):
    options = UseQueryOptions(
        enabled=enabled,
        refetch_on_mount=refetch_on_mount,
        stale_duration=stale_duration,
        cache_duration=cache_duration,
        refetch_interval=refetch_interval,
        retry_count=retry_count,
        retry_delay=retry_delay,
    )

    client = use_query_client()

    observer = Observer(
        query_key=query_key,
        fetcher=fetcher,
        client=client,
        options=options,
    )

    result = UseQueryResult(
        data=observer.query.state.data,
        data_updated_at=observer.query.state.data_updated_at,
        error=observer.query.state.error,
        error_updated_at=observer.query.state.error_updated_at,
        is_error=observer.query.state.is_error,
        is_loading=observer.query.state.is_loading,
        is_fetching=observer.query.state.is_fetching,
        is_success=observer.query.state.is_success,
        status=observer.query.state.status,
        refetch=observer.fetch,
    )

    def on_state_changed():
        result.data = observer.query.state.data
        result.data_updated_at = observer.query.state.data_updated_at
        result.error = observer.query.state.error
        result.error_updated_at = observer.query.state.error_updated_at
        result.is_error = observer.query.state.is_error
        result.is_loading = observer.query.state.is_loading
        result.is_fetching = observer.query.state.is_fetching
        result.is_success = observer.query.state.is_success
        result.status = observer.query.state.status
        ft.context.page.update()

    observer.subscribe(on_state_changed)

    ft.context.page.run_task(observer.initialize)

    return result
