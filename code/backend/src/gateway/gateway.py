import hashlib
import json
import logging
import os
import statistics
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    aiohttp = None
    AIOHTTP_AVAILABLE = False
import psutil

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False
import flask
from flask import g, jsonify, request


class PerformanceOptimizedGateway:
    """High-performance API Gateway with advanced optimization features"""

    def __init__(self, app: Any) -> None:
        self.app = app
        self.redis_client = None
        self.connection_pool = None
        self.request_cache = {}
        self.performance_metrics = defaultdict(list)
        self.circuit_breakers = {}
        self.request_queue = deque(maxlen=10000)
        self.batch_processor = None
        self.thread_pool = ThreadPoolExecutor(max_workers=20)
        self._setup_redis()
        self._setup_connection_pool()
        self._setup_caching()
        self._setup_circuit_breakers()
        self._setup_request_batching()
        self._setup_performance_monitoring()

    def _setup_redis(self) -> object:
        """Setup Redis connection with connection pooling"""
        try:
            redis_pool = redis.ConnectionPool(
                host=os.environ.get("REDIS_HOST", "localhost"),
                port=int(os.environ.get("REDIS_PORT", 6379)),
                db=int(os.environ.get("REDIS_DB", 0)),
                max_connections=50,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            self.redis_client = redis.Redis(connection_pool=redis_pool)
            self.redis_client.ping()
            self.app.logger.info("Redis connection pool established")
        except Exception as e:
            self.app.logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None

    def _setup_connection_pool(self) -> object:
        """Setup HTTP connection pool for external API calls"""
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True,
        )
        timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=10)
        self.connection_pool = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "Flowlet-Gateway/2.0"},
        )

    def _setup_caching(self) -> object:
        """Setup intelligent caching system"""
        self.cache_config = {
            "default_ttl": 300,
            "max_cache_size": 10000,
            "cache_strategies": {
                "user_profile": 1800,
                "account_balance": 60,
                "transaction_history": 300,
                "exchange_rates": 900,
                "static_data": 3600,
            },
        }

    def _setup_circuit_breakers(self) -> object:
        """Setup circuit breakers for external services"""
        self.circuit_breaker_config = {
            "failure_threshold": 5,
            "recovery_timeout": 60,
            "half_open_max_calls": 3,
        }
        services = ["plaid", "stripe", "fraud_detection", "kyc_service"]
        for service in services:
            self.circuit_breakers[service] = {
                "state": "closed",
                "failure_count": 0,
                "last_failure_time": None,
                "success_count": 0,
            }

    def _setup_request_batching(self) -> object:
        """Setup request batching for bulk operations"""
        self.batch_config = {
            "batch_size": 50,
            "batch_timeout": 100,
            "batch_endpoints": [
                "/api/v1/transactions/batch",
                "/api/v1/accounts/batch",
                "/api/v1/payments/batch",
            ],
        }
        self.batch_processor = threading.Thread(
            target=self._process_batches, daemon=True
        )
        self.batch_processor.start()

    def _setup_performance_monitoring(self) -> object:
        """Setup real-time performance monitoring"""
        self.monitoring_config = {
            "metrics_retention": 3600,
            "alert_thresholds": {
                "response_time_p95": 1000,
                "error_rate": 0.05,
                "cpu_usage": 80,
                "memory_usage": 80,
            },
        }


class CacheManager:
    """Advanced caching manager with intelligent invalidation"""

    def __init__(self, redis_client: Any, config: Any) -> None:
        self.redis_client = redis_client
        self.config = config
        self.local_cache = {}
        self.cache_stats = defaultdict(int)

    def get_cache_key(self, endpoint: Any, params: Any) -> "flask.Response":
        """Generate cache key based on endpoint and parameters"""
        key_data = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: Any, endpoint_type: Any = "default") -> object:
        """Get value from cache with fallback to local cache"""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    self.cache_stats["redis_hits"] += 1
                    return json.loads(value)
            if key in self.local_cache:
                cache_entry = self.local_cache[key]
                if cache_entry["expires"] > time.time():
                    self.cache_stats["local_hits"] += 1
                    return cache_entry["data"]
                else:
                    del self.local_cache[key]
            self.cache_stats["misses"] += 1
            return None
        except Exception as e:
            logging.error(f"Cache get error: {e}")
            return None

    def set(self, key: Any, value: Any, endpoint_type: Any = "default") -> object:
        """Set value in cache with appropriate TTL"""
        try:
            ttl = self.config["cache_strategies"].get(
                endpoint_type, self.config["default_ttl"]
            )
            if self.redis_client:
                self.redis_client.setex(key, ttl, json.dumps(value))
            self.local_cache[key] = {"data": value, "expires": time.time() + ttl}
            if len(self.local_cache) > self.config["max_cache_size"]:
                self._cleanup_local_cache()
        except Exception as e:
            logging.error(f"Cache set error: {e}")

    def invalidate_pattern(self, pattern: Any) -> object:
        """Invalidate cache entries matching pattern"""
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            keys_to_delete = [k for k in self.local_cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.local_cache[key]
        except Exception as e:
            logging.error(f"Cache invalidation error: {e}")

    def _cleanup_local_cache(self) -> object:
        """Remove expired entries from local cache"""
        current_time = time.time()
        expired_keys = [
            k for k, v in self.local_cache.items() if v["expires"] <= current_time
        ]
        for key in expired_keys:
            del self.local_cache[key]


class CircuitBreaker:
    """Circuit breaker implementation for external service calls"""

    def __init__(self, service_name: Any, config: Any) -> None:
        self.service_name = service_name
        self.config = config
        self.state = "closed"
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0

    def call(self, func: Any, *args, **kwargs) -> object:
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
                self.success_count = 0
            else:
                raise Exception(f"Circuit breaker open for {self.service_name}")
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self) -> object:
        """Handle successful call"""
        if self.state == "half_open":
            self.success_count += 1
            if self.success_count >= self.config["half_open_max_calls"]:
                self.state = "closed"
                self.failure_count = 0
        elif self.state == "closed":
            self.failure_count = 0

    def _on_failure(self) -> object:
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.config["failure_threshold"]:
            self.state = "open"

    def _should_attempt_reset(self) -> object:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time >= self.config["recovery_timeout"]


class RequestBatcher:
    """Batch similar requests for improved performance"""

    def __init__(self, config: Any) -> None:
        self.config = config
        self.pending_batches = defaultdict(list)
        self.batch_timers = {}

    def add_request(self, endpoint: Any, request_data: Any, callback: Any) -> object:
        """Add request to batch"""
        if endpoint not in self.config["batch_endpoints"]:
            callback(self._execute_single_request(endpoint, request_data))
            return
        batch_key = self._get_batch_key(endpoint, request_data)
        self.pending_batches[batch_key].append(
            {"data": request_data, "callback": callback, "timestamp": time.time()}
        )
        if len(self.pending_batches[batch_key]) == 1:
            timer = threading.Timer(
                self.config["batch_timeout"] / 1000,
                self._execute_batch,
                args=[batch_key],
            )
            timer.start()
            self.batch_timers[batch_key] = timer
        if len(self.pending_batches[batch_key]) >= self.config["batch_size"]:
            self._execute_batch(batch_key)

    def _get_batch_key(self, endpoint: Any, request_data: Any) -> object:
        """Generate batch key for grouping similar requests"""
        common_params = {
            "user_id": request_data.get("user_id"),
            "account_id": request_data.get("account_id"),
        }
        return f"{endpoint}:{json.dumps(common_params, sort_keys=True)}"

    def _execute_batch(self, batch_key: Any) -> object:
        """Execute batched requests"""
        if batch_key not in self.pending_batches:
            return
        requests = self.pending_batches.pop(batch_key)
        if batch_key in self.batch_timers:
            self.batch_timers[batch_key].cancel()
            del self.batch_timers[batch_key]
        try:
            batch_data = [req["data"] for req in requests]
            results = self._execute_batch_request(batch_key.split(":")[0], batch_data)
            for i, request in enumerate(requests):
                if i < len(results):
                    request["callback"](results[i])
                else:
                    request["callback"]({"error": "Batch processing failed"})
        except Exception as e:
            for request in requests:
                request["callback"]({"error": str(e)})

    def _execute_single_request(self, endpoint: Any, request_data: Any) -> object:
        """Execute single request"""
        return {"status": "success", "data": request_data}

    def _execute_batch_request(self, endpoint: Any, batch_data: Any) -> object:
        """Execute batch request"""
        return [{"status": "success", "data": data} for data in batch_data]


class PerformanceMonitor:
    """Real-time performance monitoring and alerting"""

    def __init__(self, config: Any) -> None:
        self.config = config
        self.metrics = defaultdict(deque)
        self.alerts = []
        self.start_time = time.time()

    def record_request(
        self, endpoint: Any, response_time: Any, status_code: Any
    ) -> object:
        """Record request metrics"""
        current_time = time.time()
        self.metrics["response_times"].append(
            {
                "timestamp": current_time,
                "endpoint": endpoint,
                "response_time": response_time,
                "status_code": status_code,
            }
        )
        self._cleanup_old_metrics()
        self._check_alerts()

    def get_metrics_summary(self) -> "flask.Response":
        """Get current metrics summary"""
        current_time = time.time()
        recent_requests = [
            m
            for m in self.metrics["response_times"]
            if current_time - m["timestamp"] <= 300
        ]
        if not recent_requests:
            return {"status": "no_data"}
        response_times = [r["response_time"] for r in recent_requests]
        error_count = len([r for r in recent_requests if r["status_code"] >= 400])
        process = psutil.Process()
        cpu_percent = process.cpu_percent()
        memory_percent = process.memory_percent()
        return {
            "request_count": len(recent_requests),
            "avg_response_time": statistics.mean(response_times),
            "p95_response_time": (
                statistics.quantiles(response_times, n=20)[18]
                if len(response_times) > 20
                else max(response_times)
            ),
            "error_rate": error_count / len(recent_requests),
            "cpu_usage": cpu_percent,
            "memory_usage": memory_percent,
            "uptime": current_time - self.start_time,
        }

    def _cleanup_old_metrics(self) -> object:
        """Remove metrics older than retention period"""
        current_time = time.time()
        retention_time = current_time - self.config["metrics_retention"]
        while (
            self.metrics["response_times"]
            and self.metrics["response_times"][0]["timestamp"] < retention_time
        ):
            self.metrics["response_times"].popleft()

    def _check_alerts(self) -> object:
        """Check for performance alerts"""
        metrics = self.get_metrics_summary()
        if metrics.get("status") == "no_data":
            return
        alerts = []
        thresholds = self.config["alert_thresholds"]
        if metrics["p95_response_time"] > thresholds["response_time_p95"]:
            alerts.append(
                {
                    "type": "high_response_time",
                    "value": metrics["p95_response_time"],
                    "threshold": thresholds["response_time_p95"],
                }
            )
        if metrics["error_rate"] > thresholds["error_rate"]:
            alerts.append(
                {
                    "type": "high_error_rate",
                    "value": metrics["error_rate"],
                    "threshold": thresholds["error_rate"],
                }
            )
        if metrics["cpu_usage"] > thresholds["cpu_usage"]:
            alerts.append(
                {
                    "type": "high_cpu_usage",
                    "value": metrics["cpu_usage"],
                    "threshold": thresholds["cpu_usage"],
                }
            )
        if metrics["memory_usage"] > thresholds["memory_usage"]:
            alerts.append(
                {
                    "type": "high_memory_usage",
                    "value": metrics["memory_usage"],
                    "threshold": thresholds["memory_usage"],
                }
            )
        for alert in alerts:
            alert["timestamp"] = time.time()
            self.alerts.append(alert)
        current_time = time.time()
        self.alerts = [a for a in self.alerts if current_time - a["timestamp"] <= 3600]


def optimize_performance(
    cache_type: Any = "default", batch_enabled: Any = False
) -> object:
    """Decorator to add performance optimizations to endpoints"""

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                if hasattr(g, "cache_manager"):
                    cache_key = g.cache_manager.get_cache_key(
                        request.endpoint, request.get_json() or {}
                    )
                    cached_result = g.cache_manager.get(cache_key, cache_type)
                    if cached_result:
                        return jsonify(cached_result)
                result = func(*args, **kwargs)
                if hasattr(g, "cache_manager") and result:
                    g.cache_manager.set(cache_key, result.get_json(), cache_type)
                return result
            finally:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                if hasattr(g, "performance_monitor"):
                    g.performance_monitor.record_request(
                        request.endpoint, response_time, 200
                    )

        return wrapper

    return decorator


def create_optimized_gateway(app: Any) -> "flask.Response":
    """Create and configure optimized API gateway"""
    gateway = PerformanceOptimizedGateway(app)

    @app.before_request
    def setup_request_context() -> None:
        g.cache_manager = CacheManager(gateway.redis_client, gateway.cache_config)
        g.performance_monitor = PerformanceMonitor(gateway.monitoring_config)
        g.request_start_time = time.time()

    @app.route("/api/v1/gateway/metrics", methods=["GET"])
    def gateway_metrics() -> object:
        """Get gateway performance metrics"""
        if hasattr(g, "performance_monitor"):
            metrics = g.performance_monitor.get_metrics_summary()
            return jsonify(metrics)
        return (jsonify({"error": "Metrics not available"}), 500)

    @app.route("/api/v1/gateway/cache/clear", methods=["POST"])
    def clear_cache() -> object:
        """Clear cache for specific pattern"""
        pattern = request.json.get("pattern", "*")
        if hasattr(g, "cache_manager"):
            g.cache_manager.invalidate_pattern(pattern)
            return jsonify({"status": "cache_cleared", "pattern": pattern})
        return (jsonify({"error": "Cache manager not available"}), 500)

    return gateway
