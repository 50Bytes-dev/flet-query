from ..query_client import QueryClient


_query_client = QueryClient()


def use_query_client():
    return _query_client


def set_query_client(client: QueryClient):
    global _query_client
    _query_client = client
