from agentops.api.log_config import logger
from .environment import (
    CACHE_NAMESPACE,
    CACHE_SOCKET_CONNECT_TIMEOUT_SECONDS,
    CACHE_SOCKET_TIMEOUT_SECONDS,
    REDIS_URL,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_USER,
    REDIS_PASSWORD,
    REQUIRE_SHARED_CACHE,
)


_redis_configured = bool(REDIS_URL or (REDIS_HOST and REDIS_PORT))


if _redis_configured:
    from redis import Redis

    logger.info("Using Redis cache for production.")
    _redis_options = {
        'decode_responses': True,
        'socket_connect_timeout': CACHE_SOCKET_CONNECT_TIMEOUT_SECONDS,
        'socket_timeout': CACHE_SOCKET_TIMEOUT_SECONDS,
        'health_check_interval': 30,
    }
    if REDIS_URL:
        _backend = Redis.from_url(REDIS_URL, **_redis_options)
    else:
        _redis_options.update({'host': REDIS_HOST, 'port': REDIS_PORT})
        if REDIS_USER and REDIS_PASSWORD:
            _redis_options['username'] = REDIS_USER
            _redis_options['password'] = REDIS_PASSWORD
        _backend = Redis(**_redis_options)

    try:
        _backend.ping()
    except Exception as exc:
        raise RuntimeError("Configured Redis shared cache is unavailable") from exc

else:
    import os
    import sqlite3
    from collections import defaultdict
    import time

    class BaseDevCache:
        """
        Base class for local development cache.

        Includes noops for methods we don't need in local development.
        """

        def zadd(self, key: str, mapping: dict) -> None:
            logger.warning("[agentops.common.cache] zadd() is not implemented in development")

        def zremrangebyscore(self, key: str, min: int, max: int) -> None:
            logger.warning("[agentops.common.cache] zremrangebyscore() is not implemented in development")

        def zcount(self, key: str, min: int, max: int) -> int:
            logger.warning("[agentops.common.cache] zcount() is not implemented in development")
            return 0

    class SimpleCache(BaseDevCache):
        """In-memory cache for local development."""

        def __init__(self):
            self.store = defaultdict(lambda: None)
            self.expiry = {}

        def get(self, key: str) -> str | None:
            if key in self.expiry and time.time() > self.expiry[key]:
                del self.store[key]
                del self.expiry[key]
                return None
            return self.store[key]

        def setex(self, key: str, expiry: int, value: str) -> None:
            self.store[key] = value
            self.expiry[key] = time.time() + expiry

        def expire(self, key: str, expiry: int) -> None:
            if key in self.store:
                self.expiry[key] = time.time() + expiry

        def delete(self, key: str) -> None:
            if key in self.store:
                del self.store[key]
            if key in self.expiry:
                del self.expiry[key]

        def incr(self, key: str) -> int:
            value = int(self.get(key) or 0) + 1
            self.store[key] = str(value)
            return value

    class SQLiteCache(BaseDevCache):
        """SQLite-backed cache for local development."""

        def __init__(self):
            self.db_path = os.path.join(os.getcwd(), "cache.db")
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    expiry INTEGER
                )
            """)
            self.conn.commit()

        def get(self, key: str) -> str | None:
            cursor = self.conn.execute("SELECT value, expiry FROM cache WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                value, expiry = row
                if expiry is not None and time.time() > expiry:
                    self.delete(key)
                    return None
                return value
            return None

        def setex(self, key: str, expiry: int, value: str) -> None:
            expiry_time = int(time.time() + expiry)
            self.conn.execute(
                """
                INSERT OR REPLACE INTO cache (key, value, expiry)
                VALUES (?, ?, ?)
            """,
                (key, value, expiry_time),
            )
            self.conn.commit()

        def expire(self, key: str, expiry: int) -> None:
            expiry_time = int(time.time() + expiry)
            self.conn.execute(
                """
                UPDATE cache SET expiry = ? WHERE key = ?
            """,
                (expiry_time, key),
            )
            self.conn.commit()

        def delete(self, key: str) -> None:
            self.conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            self.conn.commit()

        def incr(self, key: str) -> int:
            current = int(self.get(key) or 0) + 1
            self.setex(key, 365 * 24 * 60 * 60, str(current))
            return current

    if REQUIRE_SHARED_CACHE:
        raise RuntimeError("REQUIRE_SHARED_CACHE=true but no Redis connection is configured")
    if os.path.exists("/.dockerenv"):
        logger.info("Using in-memory cache for local development.")
        _backend = SimpleCache()
    elif os.environ.get('GITHUB_ACTIONS') == 'true':
        logger.info("Using in-memory cache for GitHub Actions.")
        _backend = SimpleCache()
    else:
        logger.info("Using SQLite cache for local development.")
        _backend = SQLiteCache()


def _key(key: str) -> str:
    """Keep every application key inside one deployment-specific namespace."""
    return f"{CACHE_NAMESPACE}:{key}" if CACHE_NAMESPACE else key


def get(key: str) -> str | None:
    """Get a value from the cache by key."""
    return _backend.get(_key(key))


def setex(key: str, expiry: int, value: str) -> None:
    """Set a value in the cache with an expiry time."""
    _backend.setex(_key(key), expiry, value)


def expire(key: str, expiry: int) -> None:
    """Set the expiry time for a key in the cache."""
    _backend.expire(_key(key), expiry)


def delete(key: str) -> None:
    """Delete a key from the cache."""
    _backend.delete(_key(key))


def incr(key: str) -> int:
    """Atomically increment a namespaced integer key."""
    return int(_backend.incr(_key(key)))


def set_if_absent(key: str, expiry: int, value: str) -> bool:
    """Acquire a short-lived namespaced lock when the key does not exist."""
    namespaced_key = _key(key)
    set_method = getattr(_backend, "set", None)
    if set_method is not None:
        return bool(set_method(namespaced_key, value, ex=expiry, nx=True))

    # Development caches are single-process. Production requires Redis, whose
    # SET NX EX path above is atomic across API workers.
    if _backend.get(namespaced_key) is not None:
        return False
    _backend.setex(namespaced_key, expiry, value)
    return True


def delete_if_value(key: str, value: str) -> bool:
    """Release a lock only when it is still owned by the supplied token."""
    namespaced_key = _key(key)
    eval_method = getattr(_backend, "eval", None)
    if eval_method is not None:
        deleted = eval_method(
            """
            if redis.call('get', KEYS[1]) == ARGV[1] then
                return redis.call('del', KEYS[1])
            end
            return 0
            """,
            1,
            namespaced_key,
            value,
        )
        return bool(deleted)

    if _backend.get(namespaced_key) != value:
        return False
    _backend.delete(namespaced_key)
    return True


def zadd(key: str, mapping: dict) -> None:
    """Add elements to a sorted set."""
    _backend.zadd(_key(key), mapping)


def zremrangebyscore(key: str, min: int, max: int) -> None:
    """Remove elements from a sorted set by score."""
    _backend.zremrangebyscore(_key(key), min, max)


def zcount(key: str, min: int, max: int) -> int:
    """Count elements in a sorted set by score."""
    return _backend.zcount(_key(key), min, max)


def ping() -> bool:
    """Return whether the configured cache backend is responding."""
    ping_method = getattr(_backend, 'ping', None)
    return True if ping_method is None else bool(ping_method())


def raw_backend():
    """Expose the initialized backend for Redis-native queue and locking features."""
    return _backend
