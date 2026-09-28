# -*- coding: utf-8 -*-
"""成就：回答「我做过什么」——与结局互补，跨周目累积。"""

from __future__ import annotations

from typing import Any

from .state import GameState

ACHIEVEMENTS: list[dict[str, Any]] = [
    {
        "id": "first_step",
        "title": "踏入书中",
        "desc": "完成第一局游玩",
        "icon": "书",
    },
    {
        "id": "full_season",
        "title": "活完一季",
        "desc": "一路走到回望与结局",
        "icon": "季",
    },
    {
        "id": "many_endings",
        "title": "活过两种人",
        "desc": "见证 2 个不同结局",
        "icon": "影",
    },
    {
        "id": "many_endings5",
        "title": "活过五种人",
        "desc": "见证 5 个不同结局",
        "icon": "像",
    },
    {
        "id": "sister_light",
        "title": "妹妹的光",
        "desc": "拒绝高价彩礼，把人当人",
        "icon": "光",
    },
    {
        "id": "li_remembered",
        "title": "沟口记得你",
        "desc": "病床前守过一个临终之人",
        "icon": "灯",
    },
    {
        "id": "ledger_clear",
        "title": "账本抬起头",
        "desc": "年关把账尽量清了",
        "icon": "账",
    },
    {
        "id": "warm_hand",
        "title": "心热的人",
        "desc": "温度达到 70 以上",
        "icon": "暖",
    },
    {
        "id": "hard_spine",
        "title": "硬骨头",
        "desc": "硬气达到 80 以上",
        "icon": "骨",
    },
    {
        "id": "face_won",
        "title": "有头有脸",
        "desc": "面子达到 85 以上",
        "icon": "面",
    },
    {
        "id": "skilled",
        "title": "手里有活路",
        "desc": "手艺达到 70 以上",
        "icon": "艺",
    },
    {
        "id": "network",
        "title": "人情网",
        "desc": "有一人关系达到 80",
        "icon": "网",
    },
    {
        "id": "foreshadow",
        "title": "听见风声",
        "desc": "听取至少 5 条风声/线索",
        "icon": "风",
    },
    {
        "id": "delayed_payback",
        "title": "迟来的事",
        "desc": "经历至少 3 次延迟后果",
        "icon": "债",
    },
    {
        "id": "two_books",
        "title": "两本书，一台机器",
        "desc": "游玩 2 个不同的书中世界",
        "icon": "机",
    },
    {
        "id": "ingest_book",
        "title": "投书人",
        "desc": "用投书入口生成过世界",
        "icon": "投",
    },
    {
        "id": "god_mode",
        "title": "粗线的上帝",
        "desc": "用创造模式拧动过命运（且看见限度）",
        "icon": "帝",
    },
    {
        "id": "god_blocked",
        "title": "上帝也救不了",
        "desc": "试图改写定数而被拦下",
        "icon": "限",
    },
]


def check_achievements(
    state: GameState,
    unlocked: set[str] | None = None,
    meta: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """根据一局终局状态与跨局元数据，返回本局新解锁的成就。"""
    unlocked = unlocked or set()
    meta = meta or {}
    newly: list[dict[str, Any]] = []

    def unlock(aid: str) -> None:
        if aid in unlocked:
            return
        ach = next((a for a in ACHIEVEMENTS if a["id"] == aid), None)
        if ach:
            newly.append(ach)
            unlocked.add(aid)

    # 本局条件
    if state.finished:
        unlock("first_step")
        unlock("full_season")

    if state.get_stat("warmth") >= 70:
        unlock("warm_hand")
    if state.get_stat("guts") >= 80:
        unlock("hard_spine")
    if state.get_stat("face") >= 85:
        unlock("face_won")
    if state.get_stat("craft") >= 70:
        unlock("skilled")

    if any(v >= 80 for v in state.relationships.values()):
        unlock("network")

    if state.flags.get("refused_bride_price"):
        unlock("sister_light")
    if state.flags.get("tended_li_bedside"):
        unlock("li_remembered")
    if state.flags.get("settled_debts"):
        unlock("ledger_clear")

    if len(state.rumors_heard) >= 5:
        unlock("foreshadow")

    delayed = sum(1 for m in state.memory if "delayed" in (m.tags or []))
    if delayed >= 3:
        unlock("delayed_payback")

    # 跨局
    endings = set(meta.get("endings") or [])
    if state.ending_id:
        endings.add(state.ending_id)
    if len(endings) >= 2:
        unlock("many_endings")
    if len(endings) >= 5:
        unlock("many_endings5")

    books = set(meta.get("books") or [])
    if state.package_id:
        books.add(state.package_id)
    if len(books) >= 2:
        unlock("two_books")

    if meta.get("ingested"):
        unlock("ingest_book")
    if state.flags.get("god_mode_used"):
        unlock("god_mode")
    if state.flags.get("god_try_block_canon"):
        unlock("god_blocked")

    return newly
