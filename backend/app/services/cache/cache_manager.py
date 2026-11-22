import time
import threading
from typing import Dict, Any, Optional

class CacheItem:
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.expires_at = time.time() + ttl_seconds

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

class CacheManager:
    """Tenant-scoped caching manager with TTL policies and automatic invalidation on repository edits."""
    def __init__(self):
        self._lock = threading.Lock()
        self._store: Dict[str, CacheItem] = {}
        self.hits = 0
        self.misses = 0

    def _build_key(self, tenant_id: str, repo_id: str, key_suffix: str) -> str:
        return f"tenant:{tenant_id}:repo:{repo_id}:{key_suffix}"

    def get(self, tenant_id: str, repo_id: str, key_suffix: str) -> Optional[Any]:
        full_key = self._build_key(tenant_id, repo_id, key_suffix)
        with self._lock:
            item = self._store.get(full_key)
            if item is None:
                self.misses += 1
                return None
            if item.is_expired:
                del self._store[full_key]
                self.misses += 1
                return None
            self.hits += 1
            return item.value

    def set(self, tenant_id: str, repo_id: str, key_suffix: str, value: Any, ttl_seconds: int = 300) -> None:
        full_key = self._build_key(tenant_id, repo_id, key_suffix)
        with self._lock:
            self._store[full_key] = CacheItem(value, ttl_seconds)

    def invalidate_repo(self, tenant_id: str, repo_id: str) -> int:
        """Invalidates all cached data associated with a repository when files are modified."""
        prefix = f"tenant:{tenant_id}:repo:{repo_id}:"
        invalidated = 0
        with self._lock:
            keys_to_delete = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._store[k]
                invalidated += 1
        return invalidated

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self.hits = 0
            self.misses = 0

cache_manager = CacheManager()

