import json
import os
from datetime import datetime
from pathlib import Path

_HISTORY_FILE = Path(__file__).parent.parent / "runs_history.json"
_MAX_ENTRIES  = 200


def _load() -> list:
    if not _HISTORY_FILE.exists():
        return []
    try:
        with open(_HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save(entries: list):
    with open(_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(entries[-_MAX_ENTRIES:], f, indent=2, ensure_ascii=False)


def record(flow_name: str, flow_path: str, ok: int, total: int,
           duration_s: float, start_iso: str,
           failed_idx: int = -1, failed_context: dict = None):
    entries = _load()
    entries.append({
        "flow_name":  flow_name or "(sem nome)",
        "flow_path":  flow_path or "",
        "started_at": start_iso,
        "finished_at": datetime.now().isoformat(),
        "duration_s": round(duration_s, 1),
        "total_steps": total,
        "ok_steps":   ok,
        "success":    ok == total,
        "failed_idx": failed_idx,
        "failed_context": failed_context or {},
    })
    _save(entries)


def get_history() -> list:
    return list(reversed(_load()))


def clear_history():
    _save([])
