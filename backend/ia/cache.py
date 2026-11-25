import time
from typing import Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    def __init__(self, ttl_s: float = 7 * 24 * 3600, max_items: int = 10_000) -> None:
        self.ttl_s = ttl_s
        self.max_items = max_items
        self._data: dict[str, tuple[float, T]] = {}

    def get(self, key: str) -> T | None:
        item = self._data.get(key)
        if item is None:
            return None
        expires, value = item
        if time.monotonic() > expires:
            del self._data[key]
            return None
        return value

    def set(self, key: str, value: T) -> None:
        if len(self._data) >= self.max_items:
            oldest = min(self._data, key=lambda k: self._data[k][0])
            del self._data[oldest]
        self._data[key] = (time.monotonic() + self.ttl_s, value)

    def __len__(self) -> int:
        return len(self._data)
