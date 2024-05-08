from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Optional

from .query_cache import QueryCache
from .type import DispatchAction, RefetchOnMount, TData

if TYPE_CHECKING:
    from .query import QueryKey


@dataclass
class DefaultQueryOptions:
    """All durations are in milliseconds."""

    refetch_on_mount: RefetchOnMount = RefetchOnMount.stale
    stale_duration: int = 0
    cache_duration: int = 300000
    refetch_interval: Optional[int] = None
    retry_count: int = 3
    retry_delay: int = 1500


class QueryClient:
    query_cache: QueryCache = QueryCache()
    default_query_options: DefaultQueryOptions = DefaultQueryOptions()

    def __init__(
        self,
        default_query_options: Optional[DefaultQueryOptions] = None,
    ):
        self.default_query_options = default_query_options or DefaultQueryOptions()

    async def set_query_data(
        self,
        query_key: "QueryKey",
        updater: Callable[[Optional[TData]], TData],
    ):
        query = self.query_cache.get(query_key)
        if query:
            await query.dispatch(
                DispatchAction.success,
                updater(query.state.data),
            )

    def get_query_data(
        self,
        query_key: "QueryKey",
    ):
        query = self.query_cache.get(query_key)
        if query:
            return query.state.data

    async def invalidate_queries(
        self,
        key: "QueryKey",
        exact: bool = False,
    ):
        for query_key, query in self.query_cache.queries.items():
            if exact:
                if query_key == key:
                    await query.dispatch(
                        DispatchAction.invalidate,
                        None,
                    )
            else:
                is_partial_match = (
                    len(query_key) >= len(key) and query_key[: len(key)] == key
                )
                if is_partial_match:
                    await query.dispatch(
                        DispatchAction.invalidate,
                        None,
                    )

    @property
    def is_fetching(self):
        return len(
            [
                query
                for query in self.query_cache.queries.values()
                if query.state.is_fetching
            ]
        )
