import threading
from collections import Counter, deque
from typing import Any, Deque, Dict

import numpy as np


class PerformanceTracker:
    def __init__(self, window: int = 5000) -> None:
        self._latency: Deque[float] = deque(maxlen=window)
        self._scores: Deque[float] = deque(maxlen=window)
        self._actions: Counter = Counter()
        self._modes: Counter = Counter()
        self._errors = 0
        self._lock = threading.Lock()

    def record(self, latency_ms: float, score: float, action: str, mode: str) -> None:
        with self._lock:
            self._latency.append(float(latency_ms))
            self._scores.append(float(score))
            self._actions[action] += 1
            self._modes[mode] += 1

    def record_error(self) -> None:
        with self._lock:
            self._errors += 1

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            latency = np.array(self._latency, dtype=float)
            scores = np.array(self._scores, dtype=float)
            actions = dict(self._actions)
            modes = dict(self._modes)
            errors = self._errors
        result: Dict[str, Any] = {
            "requests": int(sum(actions.values())),
            "errors": errors,
            "actions": actions,
            "modes": modes,
        }
        if len(latency):
            result["latency_ms"] = {
                "p50": round(float(np.percentile(latency, 50)), 3),
                "p95": round(float(np.percentile(latency, 95)), 3),
                "p99": round(float(np.percentile(latency, 99)), 3),
                "mean": round(float(latency.mean()), 3),
            }
            result["score_mean"] = round(float(scores.mean()), 4)
            result["score_p95"] = round(float(np.percentile(scores, 95)), 4)
        return result
