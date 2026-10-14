"""Small in-memory sliding-window rate limiter (one process, good enough for the demo box)."""
from __future__ import annotations

import time
from collections import defaultdict, deque


class Limiter:
    def __init__(self, limit: int, window_s: float):
        self.limit, self.window = limit, window_s
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        q = self.hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True

    def retry_after(self, key: str) -> int:
        q = self.hits.get(key)
        if not q:
            return 0
        return max(1, int(self.window - (time.monotonic() - q[0])))
