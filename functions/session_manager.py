"""對話狀態管理 — 使用記憶體快取（部署時可改接飛書多維表格）。"""

import json
import time
from typing import Any


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, dict] = {}

    def _key(self, open_id: str) -> str:
        return f"session:{open_id}"

    def get(self, open_id: str) -> dict:
        return self._sessions.get(self._key(open_id), {})

    def set(self, open_id: str, data: dict):
        self._sessions[self._key(open_id)] = data

    def update(self, open_id: str, **kwargs):
        key = self._key(open_id)
        if key not in self._sessions:
            self._sessions[key] = {}
        self._sessions[key].update(kwargs)

    def delete(self, open_id: str):
        self._sessions.pop(self._key(open_id), None)

    def get_field(self, open_id: str, field: str, default: Any = None) -> Any:
        return self.get(open_id).get(field, default)

    def set_field(self, open_id: str, field: str, value: Any):
        self.update(open_id, **{field: value})


_instances: dict[str, SessionStore] = {}


def get_session(instance_id: str = "default") -> SessionStore:
    if instance_id not in _instances:
        _instances[instance_id] = SessionStore()
    return _instances[instance_id]


def cleanup_expired(max_age: int = 3600):
    now = time.time()
    for key, data in list(_instances.get("default", {})._sessions.items()):
        updated = data.get("_updated", 0)
        if now - updated > max_age:
            del _instances["default"]._sessions[key]
