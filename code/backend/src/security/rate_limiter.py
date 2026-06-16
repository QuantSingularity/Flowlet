import hashlib
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Any

from flask import current_app, jsonify, request

"\nAdvanced rate limiter for financial applications\n"


class RateLimiter:
    """Advanced rate limiting with multiple strategies"""

    def __init__(self, redis_client: Any = None) -> None:
        self.redis_client = redis_client
        self.memory_store = {}

    def limit(self, rate_limit_string: str) -> object:
        """Decorator for rate limiting using string format like '5 per minute'"""

        def decorator(f: Any) -> object:
            @wraps(f)
            def decorated_function(*args: Any, **kwargs: Any) -> object:
                try:
                    # Bypass rate limiting in testing mode
                    try:
                        if current_app.config.get(
                            "TESTING"
                        ) or not current_app.config.get("RATELIMIT_ENABLED", True):
                            return f(*args, **kwargs)
                    except RuntimeError:
                        pass

                    parts = rate_limit_string.lower().split()
                    count = int(parts[0])
                    period = parts[2] if len(parts) > 2 else parts[1]
                    if period in ("minute", "minutes"):
                        window_seconds = 60
                        window_type = "minute"
                    elif period in ("hour", "hours"):
                        window_seconds = 3600
                        window_type = "hour"
                    elif period in ("day", "days"):
                        window_seconds = 86400
                        window_type = "day"
                    else:
                        window_seconds = 60
                        window_type = "minute"

                    client_id = self._get_client_id()
                    key = self._get_key(client_id, window_type)

                    if self.redis_client:
                        allowed, current, _ = self._check_redis_limit(
                            key, count, window_seconds
                        )
                    else:
                        allowed, current, _ = self._check_memory_limit(
                            key, count, window_seconds
                        )

                    if not allowed:
                        response = jsonify(
                            {
                                "error": "Rate Limit Exceeded",
                                "message": "Too many requests. Please try again later.",
                                "code": "RATE_LIMIT_EXCEEDED",
                                "retry_after": window_seconds,
                            }
                        )
                        response.status_code = 429
                        response.headers["Retry-After"] = str(window_seconds)
                        return response
                except Exception:
                    pass  # Fail open on rate limiter errors
                return f(*args, **kwargs)

            return decorated_function

        return decorator

    def _get_client_id(self) -> object:
        """Get unique client identifier"""
        ip = request.remote_addr
        user_agent = request.headers.get("User-Agent", "")
        client_string = f"{ip}:{user_agent}"
        return hashlib.sha256(client_string.encode()).hexdigest()[:16]

    def _get_key(self, identifier: Any, window_type: Any) -> object:
        """Generate Redis key for rate limiting"""
        timestamp = int(time.time())
        if window_type == "minute":
            window = timestamp // 60
        elif window_type == "hour":
            window = timestamp // 3600
        elif window_type == "day":
            window = timestamp // 86400
        else:
            window = timestamp // 60
        return f"rate_limit:{identifier}:{window_type}:{window}"

    def _check_redis_limit(self, key: Any, limit: Any, window_seconds: Any) -> object:
        """Check rate limit using Redis"""
        try:
            current_count = self.redis_client.get(key)
            if current_count is None:
                self.redis_client.setex(key, window_seconds, 1)
                return (True, 1, limit)
            current_count = int(current_count)
            if current_count >= limit:
                return (False, current_count, limit)
            self.redis_client.incr(key)
            return (True, current_count + 1, limit)
        except Exception as e:
            current_app.logger.error(f"Redis rate limiting error: {str(e)}")
            return (True, 0, limit)

    def _check_memory_limit(self, key: Any, limit: Any, window_seconds: Any) -> object:
        """Check rate limit using memory store (fallback)"""
        now = time.time()
        self.memory_store = {
            k: v
            for k, v in self.memory_store.items()
            if now - v["timestamp"] < window_seconds
        }
        if key not in self.memory_store:
            self.memory_store[key] = {"count": 1, "timestamp": now}
            return (True, 1, limit)
        entry = self.memory_store[key]
        if entry["count"] >= limit:
            return (False, entry["count"], limit)
        entry["count"] += 1
        return (True, entry["count"], limit)

    def check_rate_limit(self, identifier: Any, limits: Any) -> None:
        """
        Check multiple rate limits

        Args:
            identifier: Unique identifier for the client
            limits: Dict with rate limits, e.g., {'minute': 10, 'hour': 100}

        Returns:
            Tuple: (allowed, current_counts, limits_info)
        """
        current_counts = {}
        limits_info = {}
        for window_type, limit in limits.items():
            key = self._get_key(identifier, window_type)
            if window_type == "minute":
                window_seconds = 60
            elif window_type == "hour":
                window_seconds = 3600
            elif window_type == "day":
                window_seconds = 86400
            else:
                window_seconds = 60
            if self.redis_client:
                allowed, current, max_limit = self._check_redis_limit(
                    key, limit, window_seconds
                )
            else:
                allowed, current, max_limit = self._check_memory_limit(
                    key, limit, window_seconds
                )
            current_counts[window_type] = current
            limits_info[window_type] = max_limit
            if not allowed:
                return (False, current_counts, limits_info)
        return (True, current_counts, limits_info)

    def rate_limit(self, **limits) -> object:
        """
        Decorator for rate limiting endpoints

        Usage:
            @rate_limit(minute=10, hour=100)
            def my_endpoint() -> object:
                pass
        """

        def decorator(f):

            @wraps(f)
            def decorated_function(*args, **kwargs):
                client_id = self._get_client_id()
                allowed, current_counts, limits_info = self.check_rate_limit(
                    client_id, limits
                )
                if not allowed:
                    current_app.audit_logger.log_security_event(
                        f"Rate limit exceeded for client {client_id}",
                        ip_address=request.remote_addr,
                        severity="HIGH",
                    )
                    retry_after = 60
                    response = jsonify(
                        {
                            "error": "Rate Limit Exceeded",
                            "message": "Too many requests. Please try again later.",
                            "code": "RATE_LIMIT_EXCEEDED",
                            "retry_after": retry_after,
                            "current_limits": current_counts,
                            "max_limits": limits_info,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                    response.status_code = 429
                    response.headers["Retry-After"] = str(retry_after)
                    response.headers["X-RateLimit-Limit"] = str(
                        max(limits_info.values())
                    )
                    response.headers["X-RateLimit-Remaining"] = "0"
                    response.headers["X-RateLimit-Reset"] = str(
                        int(time.time()) + retry_after
                    )
                    return response
                response = f(*args, **kwargs)
                if hasattr(response, "headers"):
                    max_limit = max(limits_info.values())
                    current_max = max(current_counts.values())
                    response.headers["X-RateLimit-Limit"] = str(max_limit)
                    response.headers["X-RateLimit-Remaining"] = str(
                        max_limit - current_max
                    )
                    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 3600)
                return response

            return decorated_function

        return decorator

    def _parse_limit_string(self, limit_string: str) -> tuple:
        """
        Parse a rate limit string like '100 per hour' or '10 per minute'.
        Returns: Tuple of (count, period_in_seconds)
        """
        parts = limit_string.lower().strip().split()
        count = int(parts[0])
        period_word = parts[-1].rstrip("s")
        period_map = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}
        period_seconds = period_map.get(period_word, 60)
        return count, period_seconds

    def is_allowed(
        self, limit_string: str, client_id: str, endpoint: str = ""
    ) -> tuple:
        """
        Check whether a request from client_id is within the rate limit.
        Returns: Tuple of (allowed: bool, info: dict with remaining/retry_after)
        """
        count, window_seconds = self._parse_limit_string(limit_string)
        key = f"{client_id}:{endpoint}:{window_seconds}"
        allowed, current, _limit = self._check_memory_limit(key, count, window_seconds)
        remaining = max(0, count - current)
        retry_after = window_seconds if not allowed else 0
        return allowed, {
            "limit": count,
            "remaining": remaining,
            "reset_at": time.time() + window_seconds,
            "retry_after": retry_after,
        }


def auth_rate_limit(f):
    """Rate limit for authentication endpoints"""
    limiter = RateLimiter()
    return limiter.rate_limit(minute=5, hour=20)(f)


def transaction_rate_limit(f):
    """Rate limit for transaction endpoints"""
    limiter = RateLimiter()
    return limiter.rate_limit(minute=10, hour=100, day=500)(f)


def api_rate_limit(f):
    """Standard rate limit for API endpoints"""
    limiter = RateLimiter()
    return limiter.rate_limit(minute=60, hour=1000)(f)


def admin_rate_limit(f):
    """Rate limit for admin endpoints"""
    limiter = RateLimiter()
    return limiter.rate_limit(minute=30, hour=200)(f)
