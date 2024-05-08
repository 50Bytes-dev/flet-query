from threading import Timer
from typing import Optional


class Removable:
    _cache_duration: Optional[int] = None  # seconds
    _garbage_collection_timer: Optional[Timer] = None

    def set_cache_duration(self, cache_duration: Optional[int]) -> None:
        """
        Set the cache duration in seconds.

        Args:
            cache_duration (Optional[int]): The cache duration in seconds.
        """
        self._cache_duration = max(0, cache_duration or 0)
        self.schedule_garbage_collection()

    def schedule_garbage_collection(self) -> None:
        from .query_client import DefaultQueryOptions

        if self._garbage_collection_timer:
            self._garbage_collection_timer.cancel()

        self._garbage_collection_timer = Timer(
            (self._cache_duration or DefaultQueryOptions().cache_duration) / 1000,
            self.on_garbage_collection,
        )

    def on_garbage_collection(self) -> None:
        raise NotImplementedError

    def cancel_garbage_collection(self) -> None:
        if self._garbage_collection_timer:
            self._garbage_collection_timer.cancel()
            self._garbage_collection_timer = None
