from typing import Any, Optional

try:
    from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

    PROMETHEUS_AVAILABLE = True
except Exception:
    PROMETHEUS_AVAILABLE = False


class PrometheusExporter:
    def __init__(self, registry: Optional[Any] = None) -> None:
        self.enabled = PROMETHEUS_AVAILABLE
        if not self.enabled:
            return
        self.registry = registry or CollectorRegistry()
        self.decisions = Counter(
            "flowlet_ml_fraud_decisions_total",
            "Fraud decisions by action",
            ["action", "mode"],
            registry=self.registry,
        )
        self.latency = Histogram(
            "flowlet_ml_fraud_latency_seconds",
            "Fraud scoring latency",
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
            registry=self.registry,
        )
        self.model_ready = Gauge(
            "flowlet_ml_model_ready",
            "Whether a trained model is active",
            registry=self.registry,
        )
        self.errors = Counter(
            "flowlet_ml_fraud_errors_total",
            "Fraud scoring errors",
            registry=self.registry,
        )

    def observe(self, action: str, mode: str, latency_ms: float) -> None:
        if not self.enabled:
            return
        self.decisions.labels(action=action, mode=mode).inc()
        self.latency.observe(latency_ms / 1000.0)

    def set_ready(self, ready: bool) -> None:
        if self.enabled:
            self.model_ready.set(1 if ready else 0)

    def observe_error(self) -> None:
        if self.enabled:
            self.errors.inc()

    def render(self) -> bytes:
        if not self.enabled:
            return b""
        from prometheus_client import generate_latest

        return generate_latest(self.registry)
