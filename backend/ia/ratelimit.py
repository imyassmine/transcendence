import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_calls: int, period_s: float = 60.0) -> None:
        self.max_calls = max_calls
        self.period_s = period_s
        self._calls: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        q = self._calls[key]
        while q and now - q[0] > self.period_s:
            q.popleft()
        if len(q) >= self.max_calls:
            return False
        q.append(now)
        return True

    def retry_after(self, key: str) -> int:
        q = self._calls.get(key)
        if not q or len(q) < self.max_calls:
            return 0
        return max(1, int(self.period_s - (time.monotonic() - q[0])) + 1)
