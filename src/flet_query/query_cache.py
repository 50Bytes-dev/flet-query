from typing import TYPE_CHECKING, Any, Callable, Dict, Generic, Optional

from .query import Query, QueryKey
from .type import TData, TError
from .change_notifier import ChangeNotifier

if TYPE_CHECKING:
    from .query_client import QueryClient

QueriesMap = Dict[QueryKey, Query[TData, TError]]

QueryCacheListener = Callable[[], None]


class QueryCache(Generic[TData, TError], ChangeNotifier[QueryCacheListener]):
    queries: QueriesMap = {}

    def get(
        self,
        key: QueryKey,
    ) -> Optional[Query[TData, TError]]:
        return self.queries.get(key)

    def add(
        self,
        query_key: QueryKey,
        query: Query[TData, TError],
    ) -> None:
        self.queries[query_key] = query
        self.notify_listeners()

    def remove(
        self,
        query_key: QueryKey,
    ) -> None:
        del self.queries[query_key]
        self.notify_listeners()

    def build(
        self,
        query_key: QueryKey,
        query_client: "QueryClient",
    ):
        query = Query(query_client, query_key)
        self.add(query_key, query)
        return query

    def on_query_updated(self):
        self.notify_listeners()
