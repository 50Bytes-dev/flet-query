from enum import Enum
from typing import Any, Dict, List, TypeVar

TData = TypeVar("TData")
TError = TypeVar("TError")


class DispatchAction(str, Enum):
    fetch = "fetch"
    error = "error"
    success = "success"
    cancel_fetch = "cancel_fetch"
    invalidate = "invalidate"


class QueryStatus(str, Enum):
    loading = "loading"
    success = "success"
    error = "error"


class RefetchOnMount(str, Enum):
    always = "always"
    stale = "stale"
    newer = "newer"
