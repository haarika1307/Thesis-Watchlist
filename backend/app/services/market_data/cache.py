import time
from typing import Any, Optional, Dict, Tuple

class TTLCache:
    """Thread-safe in-memory cache with Time-To-Live support."""
    def __init__(self):
        self._cache: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._cache[key] = (value, time.time() + ttl_seconds)

    def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        self._cache.clear()

cache = TTLCache()
