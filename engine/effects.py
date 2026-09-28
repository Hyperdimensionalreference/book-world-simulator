"""效果结算：选项如何改变持续存在的世界状态。"""

from __future__ import annotations

from typing import Any

from .models import EffectDef, HookDef, WorldPackage
from .state import GameState, PendingHook


def apply_effect(
    state: GameState,
    package: WorldPackage,
    effect: EffectDef,
    source: str = "",
) -> list[str]:
    """应用即时效果，返回给玩家看的反馈行。"""
    notes: list[str] = []

    for sid, delta in effect.stats.items():
        before = state.get_stat(sid)
        state.stats[sid] = before + int(delta)
        try:
            sdef = package.stat(sid)
            label = sdef.name
        except KeyError:
            label = sid
        sign = "+" if delta >= 0 else ""
        notes.append(f"{label} {sign}{delta}（现 {state.stats.get(sid)}）")

    state.clamp_stats(package)

    for key, value in effect.flags.items():
        state.flags[key] = value
        if isinstance(value, str) and value:
            notes.append(f"记下了：{value}")

    for cid, delta in effect.relationships.items():
        before = state.rel(cid)
        state.relationships[cid] = before + int(delta)
        try:
            name = package.character(cid).name
        except KeyError:
            name = cid
        if delta != 0:
            sign = "+" if delta > 0 else ""
            notes.append(f"{name} 对你 {sign}{delta}（现 {state.relationships[cid]}）")

    for text in effect.add_memory:
        actor = ""
        # 记忆里的 actor 可写成 "actor|text" 的简单形式
        if "|" in text:
            actor, text = text.split("|", 1)
        state.add_memory(text, actor=actor, tags=["choice", source])
        notes.append(f"（{text}）")

    if effect.add_note:
        notes.append(effect.add_note)

    if notes:
        state.add_log(" / ".join(notes))
    return notes


def schedule_hooks(
    state: GameState,
    hooks: list[HookDef],
    source_scene: str,
    source_choice: str,
) -> list[str]:
    """把延迟后果挂到时间线上，之后一定回合再回来。"""
    notes: list[str] = []
    for hook in hooks:
        fire_turn = state.turn + max(1, int(hook.delay))
        state.pending.append(
            PendingHook(
                fire_turn=fire_turn,
                hook=hook,
                source_scene=source_scene,
                source_choice=source_choice,
            )
        )
        if hook.type == "message" and hook.text:
            notes.append(f"（有些事不会立刻结束……）")
    return notes


def fire_pending(state: GameState, package: WorldPackage) -> list[str]:
    """结算所有到期的延迟后果。"""
    due = [p for p in state.pending if p.fire_turn <= state.turn]
    state.pending = [p for p in state.pending if p.fire_turn > state.turn]
    lines: list[str] = []

    for item in due:
        hook = item.hook
        header = "【迟来的后果】" if hook.type != "message" else "【后来】"
        if hook.text:
            lines.append(f"{header} {hook.text}")

        apply_effect(
            state,
            package,
            EffectDef(
                stats=dict(hook.stats),
                flags=dict(hook.flags),
                relationships=dict(hook.relationships),
                add_memory=[hook.text] if hook.text else [],
            ),
            source=f"hook:{item.source_choice}",
        )

        if hook.type == "unlock_scene" and hook.scene_id:
            state.flags[f"unlocked:{hook.scene_id}"] = True
            lines.append("（有一件事，现在才轮得到你。）")

        if hook.type == "force_scene" and hook.scene_id:
            state.flags[f"force_next:{hook.scene_id}"] = True

        if hook.actor:
            state.add_memory(hook.text, actor=hook.actor, tags=["delayed", hook.type])

    return lines


def meets_requirements(state: GameState, requirements: dict[str, Any] | None) -> tuple[bool, str]:
    """检查选项是否可用。返回 (ok, 不可读原因)。"""
    if not requirements:
        return True, ""

    for sid, need in (requirements.get("stats") or {}).items():
        cur = state.get_stat(sid)
        if isinstance(need, dict):
            if "min" in need and cur < int(need["min"]):
                return False, f"{sid} 需要 ≥{need['min']}"
            if "max" in need and cur > int(need["max"]):
                return False, f"{sid} 需要 ≤{need['max']}"
        else:
            if cur < int(need):
                return False, f"{sid} 需要 ≥{need}"

    for cid, need in (requirements.get("relationships") or {}).items():
        cur = state.rel(cid)
        if isinstance(need, dict):
            if "min" in need and cur < int(need["min"]):
                return False, f"与某人关系需要 ≥{need['min']}"
            if "max" in need and cur > int(need["max"]):
                return False, f"与某人关系需要 ≤{need['max']}"
        else:
            if cur < int(need):
                return False, f"与某人关系需要 ≥{need}"

    for key, need in (requirements.get("flags") or {}).items():
        cur = state.flags.get(key)
        if isinstance(need, bool):
            if bool(cur) != need:
                return False, "条件不满足"
        elif cur != need:
            return False, "条件不满足"

    return True, ""
