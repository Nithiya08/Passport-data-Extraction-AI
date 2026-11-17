import hashlib
import time
import threading
from typing import List, Optional, Dict, Any
from app.schemas import ExtractionResult


class InMemoryDocumentCache:
    """Thread-safe, in-memory LRU cache with TTL for passport extraction results.

    Guarantees:
    - Zero disk persistence (strictly in-memory RAM only).
    - Content-addressable SHA-256 document hashing.
    - Automatic LRU eviction and TTL cleanup.
    """

    def __init__(self, max_entries: int = 50, default_ttl_seconds: int = 86400):
        self.max_entries = max_entries
        self.default_ttl_seconds = default_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    @staticmethod
    def compute_hash(image_buffers: List[bytes]) -> str:
        """Compute deterministic SHA-256 digest for a list of document page buffers."""
        hasher = hashlib.sha256()
        for buf in image_buffers:
            hasher.update(hashlib.sha256(buf).digest())
        return hasher.hexdigest()

    def get(self, cache_key: str) -> Optional[ExtractionResult]:
        now = time.time()
        with self._lock:
            entry = self._cache.get(cache_key)
            if not entry:
                self.misses += 1
                return None

            # Check expiration
            if now > entry["expires_at"]:
                del self._cache[cache_key]
                self.misses += 1
                return None

            # Update access timestamp for LRU
            entry["last_accessed"] = now
            self.hits += 1

            # Return a copy marked as cached
            cached_copy = entry["result"].model_copy(deep=True)
            cached_copy.is_cached = True
            return cached_copy

    def set(self, cache_key: str, result: ExtractionResult, ttl: Optional[int] = None) -> None:
        now = time.time()
        ttl_seconds = ttl if ttl is not None else self.default_ttl_seconds
        with self._lock:
            # Check capacity and evict least recently used if full
            if len(self._cache) >= self.max_entries and cache_key not in self._cache:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["last_accessed"])
                del self._cache[oldest_key]

            # Store clean result with is_cached=False
            stored_result = result.model_copy(deep=True)
            stored_result.is_cached = False

            self._cache[cache_key] = {
                "result": stored_result,
                "expires_at": now + ttl_seconds,
                "last_accessed": now,
            }

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_cached": len(self._cache),
                "max_entries": self.max_entries,
                "hits": self.hits,
                "misses": self.misses,
            }


# Global singleton cache instance
document_cache = InMemoryDocumentCache()

