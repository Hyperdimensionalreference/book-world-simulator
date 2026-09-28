# -*- coding: utf-8 -*-
"""书架：多本书并行游玩状态，一键切换且继承进度。"""

from __future__ import annotations

from typing import Any

from .save_store import list_saves, read_save, write_save


def book_slot(package_id: str) -> str:
    safe = "".join(c for c in str(package_id) if c.isalnum() or c in "_-")
    return f"book_{safe}"


def shelf_status(package_ids: list[str]) -> list[dict[str, Any]]:
    """每个世界的最近进度摘要。"""
    saves = list_saves()
    by_pkg: dict[str, dict[str, Any]] = {}
    for s in saves:
        pid = str(s.get("package_id") or "")
        if not pid:
            continue
        # 优先 book_ 槽，其次最新
        slot = str(s.get("slot") or "")
        prefer = slot.startswith("book_")
        cur = by_pkg.get(pid)
        if cur is None or (prefer and not cur.get("_prefer")) or (
            prefer == cur.get("_prefer") and str(s.get("updated_at") or "") > str(cur.get("updated_at") or "")
        ):
            item = dict(s)
            item["_prefer"] = prefer
            by_pkg[pid] = item

    out = []
    for pid in package_ids:
        hit = by_pkg.get(pid)
        out.append(
            {
                "package_id": pid,
                "slot": hit.get("slot") if hit else None,
                "has_save": bool(hit),
                "turn": hit.get("turn") if hit else None,
                "finished": bool(hit.get("finished")) if hit else False,
                "ending_id": hit.get("ending_id") if hit else None,
                "player": hit.get("player") if hit else None,
                "updated_at": hit.get("updated_at") if hit else None,
                "preview": hit.get("preview") if hit else "",
                "title": hit.get("title") if hit else None,
            }
        )
    return out


def persist_book_session(package_id: str, payload: dict[str, Any]) -> str:
    return write_save(book_slot(package_id), payload, auto=True)


def load_book_session(package_id: str) -> dict[str, Any] | None:
    data = read_save(book_slot(package_id))
    if data:
        return data
    # 回退：任意含该 package_id 的最新存档
    saves = list_saves()
    for s in saves:
        if str(s.get("package_id") or "") == str(package_id) and s.get("slot"):
            return read_save(str(s["slot"]))
    return None
