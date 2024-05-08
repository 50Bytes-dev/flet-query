from dataclasses import dataclass, replace
from datetime import datetime
from typing import TYPE_CHECKING, Any, Generic, List, Optional, TypeVar, Tuple

from .type import DispatchAction, QueryStatus, RefetchOnMount, TData, TError
from .removable import Removable

if TYPE_CHECKING:
    from .observer import Observer
    from .query_client import QueryClient

QueryKey = Tuple[Any, ...]


@dataclass
class QueryOptions(Generic[TData, TError]):
    """All durations are in milliseconds."""

    enabled: bool
    refetch_on_mount: RefetchOnMount
    stale_duration: int
    cache_duration: int
    refetch_interval: Optional[int]
    retry_count: int = 3
    retry_delay: int = 1500


@dataclass
class QueryState(Generic[TData, TError]):
    data: Optional[TData] = None
    error: Optional[TError] = None
    data_updated_at: Optional[datetime] = None
    error_updated_at: Optional[datetime] = None
    is_fetching: bool = False
    status: QueryStatus = QueryStatus.loading
    is_invalidated: bool = False

    @property
    def is_loading(self) -> bool:
        return self.status == QueryStatus.loading

    @property
    def is_success(self) -> bool:
        return self.status == QueryStatus.success

    @property
    def is_error(self) -> bool:
        return self.status == QueryStatus.error


class Query(Removable, Generic[TData, TError]):
    client: "QueryClient"
    key: QueryKey

    state: QueryState[TData, TError] = QueryState()
    observers: List["Observer"] = []

    def __init__(
        self,
        client: "QueryClient",
        key: QueryKey,
    ):
        self.client = client
        self.key = key

    def _reducer(
        self,
        state: QueryState[TData, TError],
        action: DispatchAction,
        data: Optional[TData],
    ):
        if action == DispatchAction.fetch:
            return replace(
                state,
                is_fetching=True,
                status=(
                    QueryStatus.loading
                    if state.data_updated_at is None
                    else state.status
                ),
            )
        elif action == DispatchAction.cancel_fetch:
            return replace(
                state,
                is_fetching=False,
            )
        elif action == DispatchAction.error:
            return replace(
                state,
                is_fetching=False,
                error=data,
                error_updated_at=datetime.now(),
                status=QueryStatus.error,
            )
        elif action == DispatchAction.success:
            return replace(
                state,
                is_fetching=False,
                is_invalidated=False,
                error=None,
                data=data,
                data_updated_at=datetime.now(),
                status=QueryStatus.success,
            )
        elif action == DispatchAction.invalidate:
            return replace(
                state,
                is_invalidated=True,
            )
        else:
            return state

    async def dispatch(
        self,
        action: DispatchAction,
        data: Optional[TData],
    ):
        self.state = self._reducer(self.state, action, data)
        await self.notify_observers()
        self.client.query_cache.on_query_updated()

        if action in [DispatchAction.success, DispatchAction.error]:
            for observer in self.observers:
                observer.schedule_refetch()

    def subscribe(self, observer: "Observer"):
        self.observers.append(observer)
        self.cancel_garbage_collection()

    def unsubscribe(self, observer: "Observer"):
        self.observers.remove(observer)
        self.schedule_garbage_collection()

    async def notify_observers(self):
        for observer in self.observers:
            await observer.on_query_updated()

    def on_garbage_collection(self):
        super().on_garbage_collection()
        self.client.query_cache.remove(self.key)
