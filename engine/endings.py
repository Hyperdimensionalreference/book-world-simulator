"""结局判定：结束时回答「我成为了什么样的人」。"""

from __future__ import annotations

from typing import Any

from .models import EndingDef, WorldPackage
from .state import GameState


def _stat_at_least(state: GameState, sid: str, value: int) -> bool:
    return state.get_stat(sid) >= value


def _stat_at_most(state: GameState, sid: str, value: int) -> bool:
    return state.get_stat(sid) <= value


def _rel_at_least(state: GameState, cid: str, value: int) -> bool:
    return state.rel(cid) >= value


def _flag_true(state: GameState, key: str) -> bool:
    return bool(state.flags.get(key))


def _flag_eq(state: GameState, key: str, value: Any) -> bool:
    return state.flags.get(key) == value


def conditions_met(cond: dict[str, Any], state: GameState) -> bool:
    if not cond:
        return True

    for sid, need in (cond.get("stats_min") or {}).items():
        if not _stat_at_least(state, sid, int(need)):
            return False
    for sid, need in (cond.get("stats_max") or {}).items():
        if not _stat_at_most(state, sid, int(need)):
            return False
    for cid, need in (cond.get("rel_min") or {}).items():
        if not _rel_at_least(state, cid, int(need)):
            return False
    for cid, need in (cond.get("rel_max") or {}).items():
        if state.rel(cid) > int(need):
            return False

    for key in cond.get("flags_true") or []:
        if not _flag_true(state, str(key)):
            return False
    for key in cond.get("flags_false") or []:
        if _flag_true(state, str(key)):
            return False

    for key, value in (cond.get("flags_eq") or {}).items():
        if not _flag_eq(state, key, value):
            return False

    for cid, need in (cond.get("chosen") or {}).items():
        if state.chosen.get(cid) != need:
            return False

    # 至少要有这么多条记忆（活着被记住）
    min_mem = cond.get("memory_min")
    if min_mem is not None:
        living = [m for m in state.memory if m.tags and m.tags != ["start"]]
        if len(living) < int(min_mem):
            return False

    return True


def evaluate_ending(package: WorldPackage, state: GameState) -> EndingDef:
    candidates = sorted(package.endings, key=lambda e: e.priority)
    for ending in candidates:
        if conditions_met(ending.conditions, state):
            return ending

    # 兜底
    return EndingDef(
        id="fallback",
        title="过完了这一季",
        priority=9999,
        body="该来的都来了。你也在场。至于你成了谁——时间还长，但这一段已经写完了。",
        epithet="一个没有留下名字的过路人",
    )
