# -*- coding: utf-8 -*-
"""创造模式：上帝视角的大方向干预。

原则：
- 可改：关系温度、名望处境、软旗标、后续可选内容权重、叙事语气
- 不可改：定数事件是否发生 / 发生时间（「有时候上帝也挽救不了一个人」）
- 每次干预留下痕迹，供结局与成就回看
"""

from __future__ import annotations

from typing import Any

from .effects import apply_effect
from .models import EffectDef, WorldPackage
from .state import GameState


PROTECTED_STAT_MAX_DELTA = 15
PROTECTED_REL_MAX_DELTA = 25


def god_limits() -> dict[str, Any]:
    return {
        "can_change": [
            "关系温度（有限幅度）",
            "面子/硬气/温度等处境",
            "人物对你的态度旗标",
            "后续剧情的「可能」与语气",
            "你自己的走向备注",
        ],
        "cannot_change": [
            "定数事件是否发生",
            "定数发生的时间点",
            "原书已写死的大事件结果",
            "把他人的命运直接改成幸福结局",
        ],
        "max_stat_delta": PROTECTED_STAT_MAX_DELTA,
        "max_rel_delta": PROTECTED_REL_MAX_DELTA,
    }


def apply_god_intervention(
    package: WorldPackage,
    state: GameState,
    *,
    kind: str,
    target: str = "",
    stat: str = "",
    delta: int = 0,
    note: str = "",
    directive: str = "",
) -> dict[str, Any]:
    """应用一次上帝干预。返回 {ok, message, effect_lines, blocked}。"""
    lines: list[str] = []
    blocked: list[str] = []
    kind = str(kind or "").strip()
    note = (note or "").strip()[:400]
    directive = (directive or "").strip()[:400]

    if kind == "canon":
        blocked.append("定数不可改写——你可以选择如何面对，但历史不转弯。")
        state.add_memory(f"上帝试图改写定数被拒：{note or directive}", actor="god", tags=["god", "blocked"])
        state.flags["god_try_block_canon"] = True
        return {
            "ok": False,
            "message": "上帝也改不了写定的事。",
            "effect_lines": [],
            "blocked": blocked,
        }

    effect = EffectDef()

    if kind == "relation":
        if not target:
            return {"ok": False, "message": "需要指定人物", "effect_lines": [], "blocked": ["缺少 target"]}
        try:
            package.character(target)
        except KeyError:
            return {"ok": False, "message": "人物不存在", "effect_lines": [], "blocked": ["未知人物"]}
        d = int(delta)
        if abs(d) > PROTECTED_REL_MAX_DELTA:
            d = PROTECTED_REL_MAX_DELTA if d > 0 else -PROTECTED_REL_MAX_DELTA
            blocked.append(f"关系变化被限制在 ±{PROTECTED_REL_MAX_DELTA}")
        effect.relationships[target] = d
        effect.add_memory = [f"god|把与某人的温度拧了 {d:+d}"]

    elif kind == "stat":
        if not stat:
            return {"ok": False, "message": "需要指定数值", "effect_lines": [], "blocked": ["缺少 stat"]}
        d = int(delta)
        if abs(d) > PROTECTED_STAT_MAX_DELTA:
            d = PROTECTED_STAT_MAX_DELTA if d > 0 else -PROTECTED_STAT_MAX_DELTA
            blocked.append(f"数值变化被限制在 ±{PROTECTED_STAT_MAX_DELTA}")
        effect.stats[stat] = d

    elif kind == "directive":
        # 大方向指令：写旗标 + 记忆；后续可被场景/hook 读到
        if not (directive or note):
            return {"ok": False, "message": "请写下大方向", "effect_lines": [], "blocked": ["缺少 directive"]}
        effect.flags["god_directive"] = directive or note
        effect.flags["god_directive_turn"] = state.turn
        effect.add_memory = [f"god|上帝手谕：{(directive or note)[:120]}"]

    elif kind == "attitude":
        # 人物态度软调整
        if not target:
            return {"ok": False, "message": "需要指定人物", "effect_lines": [], "blocked": ["缺少 target"]}
        key = f"god_attitude:{target}"
        effect.flags[key] = note or directive or "偏向玩家"
        effect.flags["god_touch_turn"] = state.turn

    else:
        return {"ok": False, "message": "未知干预类型", "effect_lines": [], "blocked": ["未知 kind"]}

    if note:
        effect.add_note = note
    lines = apply_effect(state, package, effect, source="god")
    state.flags["god_mode_used"] = True
    state.add_memory(
        f"创造模式干预（{kind}）：{note or directive or target}",
        actor="god",
        tags=["god", kind],
    )
    state.add_log(f"god:{kind}")

    return {
        "ok": True,
        "message": "干预已写入命运的粗线。",
        "effect_lines": lines,
        "blocked": blocked,
    }
