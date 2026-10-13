import json
import threading
from collections import OrderedDict, deque
from datetime import datetime, timedelta, timezone
from typing import Any, Deque, Dict, Iterable, List, Optional, Protocol

import pandas as pd

from ..core.logging import get_logger

logger = get_logger(__name__)

HISTORY_COLUMNS = [
    "timestamp",
    "amount",
    "merchant_category",
    "device_fingerprint",
    "location_country",
    "currency",
    "transaction_id",
]


def _empty_history() -> pd.DataFrame:
    frame = pd.DataFrame(columns=HISTORY_COLUMNS)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame["amount"] = frame["amount"].astype(float)
    return frame


def normalize_history(history: Any) -> pd.DataFrame:
    if history is None:
        return _empty_history()
    if isinstance(history, pd.DataFrame):
        frame = history.copy()
    elif isinstance(history, Iterable) and not isinstance(history, (str, bytes, dict)):
        records = list(history)
        if not records:
            return _empty_history()
        frame = pd.DataFrame(records)
    else:
        return _empty_history()
    if frame.empty or "timestamp" not in frame.columns or "amount" not in frame.columns:
        return _empty_history()
    for column in HISTORY_COLUMNS:
        if column not in frame.columns:
            frame[column] = None
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce")
    frame = frame.dropna(subset=["timestamp", "amount"])
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    return frame[HISTORY_COLUMNS]


class HistoryStore(Protocol):
    def append(self, user_id: str, record: Dict[str, Any]) -> None: ...

    def get(self, user_id: str) -> pd.DataFrame: ...

    def count(self, user_id: str) -> int: ...

    def clear(self, user_id: Optional[str] = None) -> None: ...


def _record_from_transaction(record: Dict[str, Any]) -> Dict[str, Any]:
    timestamp = record.get("timestamp")
    if not isinstance(timestamp, datetime):
        timestamp = datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return {
        "timestamp": timestamp,
        "amount": float(record.get("amount", 0.0)),
        "merchant_category": record.get("merchant_category"),
        "device_fingerprint": record.get("device_fingerprint"),
        "location_country": record.get("location_country"),
        "currency": record.get("currency"),
        "transaction_id": record.get("transaction_id"),
    }


class InMemoryHistoryStore:
    def __init__(
        self,
        max_per_user: int = 500,
        window_days: int = 90,
        max_users: int = 100000,
    ) -> None:
        self.max_per_user = max_per_user
        self.window = timedelta(days=window_days)
        self.max_users = max_users
        self._data: "OrderedDict[str, Deque[Dict[str, Any]]]" = OrderedDict()
        self._lock = threading.RLock()

    def append(self, user_id: str, record: Dict[str, Any]) -> None:
        item = _record_from_transaction(record)
        with self._lock:
            bucket = self._data.get(user_id)
            if bucket is None:
                bucket = deque(maxlen=self.max_per_user)
                self._data[user_id] = bucket
                while len(self._data) > self.max_users:
                    self._data.popitem(last=False)
            else:
                self._data.move_to_end(user_id)
            bucket.append(item)

    def get(self, user_id: str) -> pd.DataFrame:
        with self._lock:
            bucket = self._data.get(user_id)
            records: List[Dict[str, Any]] = list(bucket) if bucket else []
        if not records:
            return _empty_history()
        cutoff = datetime.now(timezone.utc) - self.window
        records = [item for item in records if item["timestamp"] >= cutoff]
        return normalize_history(records)

    def count(self, user_id: str) -> int:
        with self._lock:
            bucket = self._data.get(user_id)
            return len(bucket) if bucket else 0

    def clear(self, user_id: Optional[str] = None) -> None:
        with self._lock:
            if user_id is None:
                self._data.clear()
            else:
                self._data.pop(user_id, None)


class RedisHistoryStore:
    def __init__(
        self,
        client: Any,
        max_per_user: int = 500,
        window_days: int = 90,
        prefix: str = "flowlet:ml:history:",
        fallback: Optional[InMemoryHistoryStore] = None,
    ) -> None:
        self.client = client
        self.max_per_user = max_per_user
        self.window_days = window_days
        self.prefix = prefix
        self.fallback = fallback or InMemoryHistoryStore(max_per_user, window_days)

    def _key(self, user_id: str) -> str:
        return f"{self.prefix}{user_id}"

    def append(self, user_id: str, record: Dict[str, Any]) -> None:
        item = _record_from_transaction(record)
        payload = json.dumps({**item, "timestamp": item["timestamp"].isoformat()})
        try:
            key = self._key(user_id)
            pipe = self.client.pipeline()
            pipe.rpush(key, payload)
            pipe.ltrim(key, -self.max_per_user, -1)
            pipe.expire(key, self.window_days * 86400)
            pipe.execute()
        except Exception as exc:
            logger.warning("Redis history append failed: %s", exc)
            self.fallback.append(user_id, record)

    def get(self, user_id: str) -> pd.DataFrame:
        try:
            raw = self.client.lrange(self._key(user_id), 0, -1)
            records = [json.loads(item) for item in raw]
            frame = normalize_history(records)
            if frame.empty:
                return self.fallback.get(user_id)
            cutoff = datetime.now(timezone.utc) - timedelta(days=self.window_days)
            return frame[frame["timestamp"] >= cutoff].reset_index(drop=True)
        except Exception as exc:
            logger.warning("Redis history read failed: %s", exc)
            return self.fallback.get(user_id)

    def count(self, user_id: str) -> int:
        try:
            return int(self.client.llen(self._key(user_id)))
        except Exception:
            return self.fallback.count(user_id)

    def clear(self, user_id: Optional[str] = None) -> None:
        self.fallback.clear(user_id)
        try:
            if user_id is None:
                for key in self.client.scan_iter(f"{self.prefix}*"):
                    self.client.delete(key)
            else:
                self.client.delete(self._key(user_id))
        except Exception as exc:
            logger.warning("Redis history clear failed: %s", exc)


def build_history_store(settings: Any) -> HistoryStore:
    memory = InMemoryHistoryStore(
        settings.max_history_per_user, settings.history_window_days
    )
    if not settings.redis_url:
        return memory
    try:
        import redis

        client = redis.Redis.from_url(settings.redis_url, socket_timeout=0.25)
        client.ping()
        return RedisHistoryStore(
            client,
            settings.max_history_per_user,
            settings.history_window_days,
            fallback=memory,
        )
    except Exception as exc:
        logger.warning("Redis unavailable for history store, using memory: %s", exc)
        return memory
