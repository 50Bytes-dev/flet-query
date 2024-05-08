from functools import partial
from typing import Callable, Generic, Set, TypeVar


Listener = Callable[..., None]
TListener = TypeVar("TListener", bound=Listener)


class ChangeNotifier(Generic[TListener]):
    listeners: Set[TListener]

    def __init__(self) -> None:
        self.listeners: Set[TListener] = set()

    def subscribe(self, listener: TListener) -> Callable[[], None]:
        self.listeners.add(listener)
        self.on_subscribe()

        def unsubscribe() -> None:
            self.listeners.remove(listener)
            self.on_unsubscribe()

        return unsubscribe

    def notify_listeners(self, *args, **kwargs) -> None:
        for listener in self.listeners:
            listener(*args, **kwargs)

    def has_listeners(self) -> bool:
        return len(self.listeners) > 0

    def on_subscribe(self) -> None:
        pass

    def on_unsubscribe(self) -> None:
        pass
