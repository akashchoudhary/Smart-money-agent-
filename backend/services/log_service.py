"""
Simple in-memory log ring buffer for data source tracking.
Each engine appends an entry (real vs mock, which provider, any error).
Exposed via GET /logs.
"""
import threading
from collections import deque
from datetime import datetime
from typing import Any, Dict, List

_log: deque = deque(maxlen=300)
_lock = threading.Lock()

SOURCE_REAL  = "real"
SOURCE_MOCK  = "mock"
SOURCE_ERROR = "error"


def add_log(engine: str, ticker: str, source: str, detail: str = "") -> None:
    entry: Dict[str, Any] = {
        "ts":     datetime.utcnow().strftime("%H:%M:%S"),
        "engine": engine,
        "ticker": ticker,
        "source": source,   # "real" | "mock" | "error"
        "detail": detail,
    }
    with _lock:
        _log.appendleft(entry)


def get_logs(limit: int = 100) -> List[Dict[str, Any]]:
    with _lock:
        return list(_log)[:limit]
