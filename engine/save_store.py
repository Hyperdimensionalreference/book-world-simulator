# -*- coding: utf-8 -*-
"""存档槽位：多槽 + 自动存档 + 成就元数据。落在 data/saves/，重启不丢。"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SAVES = ROOT / "data" / "saves"
META_PATH = SAVES / "_meta.json"


def _ensure() -> None:
    SAVES.mkdir(parents=True, exist_ok=True)


def load_meta() -> dict[str, Any]:
    _ensure()
    if META_PATH.exists():
        try:
            return json.loads(META_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {
        "unlocked": [],
        "endings": [],
        "books": [],
        "ingested": False,
        "settings": {},
    }


def save_meta(meta: dict[str, Any]) -> None:
    _ensure()
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def list_saves() -> list[dict[str, Any]]:
    _ensure()
    out = []
    for p in sorted(SAVES.glob("slot_*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        snap = data.get("state") or {}
        out.append(
            {
                "slot": p.stem.replace("slot_", ""),
                "title": data.get("package_title") or snap.get("package_id"),
                "package_id": snap.get("package_id") or data.get("package_id"),
                "player": snap.get("player_name"),
                "turn": snap.get("turn"),
                "finished": bool(snap.get("finished")),
                "ending_id": snap.get("ending_id"),
                "updated_at": data.get("updated_at"),
                "auto": data.get("auto", False),
                "preview": _preview(data),
            }
        )
    out.sort(key=lambda x: str(x.get("updated_at") or ""), reverse=True)
    return out


def _preview(data: dict[str, Any]) -> str:
    mem = (data.get("state") or {}).get("memory") or []
    if mem:
        return str(mem[-1].get("text") or "")[:48]
    return ""


def write_save(slot: str, payload: dict[str, Any], auto: bool = False) -> str:
    _ensure()
    slot = "".join(c for c in slot if c.isalnum() or c in "_-") or "main"
    payload = dict(payload)
    payload["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    payload["auto"] = auto
    path = SAVES / f"slot_{slot}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return slot


def read_save(slot: str) -> dict[str, Any] | None:
    _ensure()
    slot = "".join(c for c in slot if c.isalnum() or c in "_-")
    path = SAVES / f"slot_{slot}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def delete_save(slot: str) -> bool:
    _ensure()
    slot = "".join(c for c in slot if c.isalnum() or c in "_-")
    path = SAVES / f"slot_{slot}.json"
    if path.exists():
        path.unlink()
        return True
    return False
