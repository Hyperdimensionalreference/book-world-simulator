"""制作阶段的内容复核信号；结构合法不代表文字已经可发布。"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from production.validate import validate_package

PLACEHOLDER = re.compile(
    r"待填|待命名|请依据原文|前置线索\s*[AB]|压力点：|赌注是：|两头都想要"
)


def _issue(severity: str, code: str, location: str, message: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "location": location, "message": message}


def _normalize(text: str) -> str:
    return "".join(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", text)).lower()


def _package_texts(world: dict, scenes: list[dict], endings: list[dict]):
    yield "world.meta.intro", str((world.get("meta") or {}).get("intro") or "")
    for character in world.get("characters") or []:
        cid = character.get("id")
        for key in ("wants", "blocks", "costs", "speech_style"):
            yield f"character.{cid}.{key}", str(character.get(key) or "")
    for event in world.get("canon_events") or []:
        eid = event.get("id")
        yield f"canon.{eid}.description", str(event.get("description") or "")
        for index, rumor in enumerate(event.get("rumors") or []):
            yield f"canon.{eid}.rumor.{index}", str(rumor.get("text") or "")
    for scene in scenes:
        sid = scene.get("id")
        yield f"scene.{sid}.narration", str(scene.get("narration") or "")
        for choice in scene.get("choices") or []:
            cid = choice.get("id")
            yield f"scene.{sid}.choice.{cid}.text", str(choice.get("text") or "")
            yield f"scene.{sid}.choice.{cid}.immediate", str(choice.get("immediate") or "")
            for index, hook in enumerate(choice.get("hooks") or []):
                yield f"scene.{sid}.choice.{cid}.hook.{index}", str(hook.get("text") or "")
    for ending in endings:
        eid = ending.get("id")
        yield f"ending.{eid}.body", str(ending.get("body") or "")
        yield f"ending.{eid}.epithet", str(ending.get("epithet") or "")


def review_package(package_dir: str | Path, source_text: str = "") -> dict[str, Any]:
    """返回可机检的问题；人工仍须复核人物口吻与取舍重量。"""
    root = Path(package_dir)
    issues = [
        _issue("blocker", "package_invalid", "package", problem)
        for problem in validate_package(root)
    ]
    if issues:
        return _report(issues)

    world = json.loads((root / "world.json").read_text(encoding="utf-8"))
    scenes = json.loads((root / "scenes.json").read_text(encoding="utf-8"))
    endings = json.loads((root / "endings.json").read_text(encoding="utf-8"))
    char_ids = {char.get("id") for char in world.get("characters") or []}

    texts = list(_package_texts(world, scenes, endings))
    for location, value in texts:
        if value and PLACEHOLDER.search(value):
            issues.append(_issue("blocker", "placeholder", location, "仍含占位或脚手架说明文字"))

    choice_texts = Counter(
        _normalize(choice.get("text") or "")
        for scene in scenes
        for choice in scene.get("choices") or []
    )
    for choice_text, count in choice_texts.items():
        if choice_text and count >= 3:
            issues.append(_issue("warning", "repeated_choice", "choices", f"同一选项措辞出现 {count} 次"))

    effect_patterns = Counter()
    for scene in scenes:
        if "冲突" not in (scene.get("tags") or []):
            continue
        pattern = []
        for choice in scene.get("choices") or []:
            effect = choice.get("effects") or {}
            pattern.append((
                tuple(sorted((effect.get("stats") or {}).items())),
                tuple(sorted((effect.get("relationships") or {}).values())),
                tuple(str(hook.get("delay") or 0) for hook in choice.get("hooks") or []),
            ))
        if pattern:
            effect_patterns[tuple(pattern)] += 1
    for count in effect_patterns.values():
        if count >= 3:
            issues.append(_issue("warning", "repeated_effect_pattern", "choices", f"相同的选项代价组合出现在 {count} 个冲突场景中"))

    for scene in scenes:
        sid = str(scene.get("id") or "?")
        narration = str(scene.get("narration") or "")
        if len(_normalize(narration)) < 35:
            issues.append(_issue("warning", "thin_scene", f"scene.{sid}", "场景叙述过短，需人工检查压力与代价"))
        if scene.get("npcs") and not any(mark in narration for mark in ("「", "“", '"')):
            issues.append(_issue("warning", "no_dialogue", f"scene.{sid}", "有人在场却没有直接对白"))
        important = bool(set(scene.get("tags") or []) & {"冲突", "定数"})
        for choice in scene.get("choices") or []:
            cid = str(choice.get("id") or "?")
            hooks = choice.get("hooks") or []
            if important and not hooks:
                issues.append(_issue("warning", "no_delayed_consequence", f"scene.{sid}.choice.{cid}", "重要站位缺少延迟回响"))
            for index, hook in enumerate(hooks):
                location = f"scene.{sid}.choice.{cid}.hook.{index}"
                try:
                    delay = int(hook.get("delay", 0))
                except (TypeError, ValueError):
                    delay = 0
                if not 2 <= delay <= 12:
                    issues.append(_issue("blocker", "hook_delay", location, "延迟后果应在 2–12 回合后发生"))
                actor = hook.get("actor")
                if actor and actor not in char_ids:
                    issues.append(_issue("blocker", "hook_actor", location, "后果承接人物不存在"))
                if important and not actor:
                    issues.append(_issue("warning", "anonymous_hook", location, "重要后果没有具体人物承接"))

    normalized_source = _normalize(source_text)
    if len(normalized_source) >= 28:
        source_grams = {normalized_source[i : i + 28] for i in range(len(normalized_source) - 27)}
        for location, value in texts:
            normalized = _normalize(value)
            if len(normalized) >= 28 and any(
                normalized[i : i + 28] in source_grams for i in range(len(normalized) - 27)
            ):
                issues.append(_issue("blocker", "source_overlap", location, "与投入文本有连续 28 字以上重合；请检查是否复述原文"))

    return _report(issues)


def _report(issues: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "status": "review_required" if issues else "manual_review_required",
        "blockers": sum(issue["severity"] == "blocker" for issue in issues),
        "warnings": sum(issue["severity"] == "warning" for issue in issues),
        "issues": issues,
        "note": "机检只能筛查明显问题；人物口吻、选择重量和版权边界仍需人工复核。",
    }
