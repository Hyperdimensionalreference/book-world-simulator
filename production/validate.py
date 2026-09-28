"""数据包校验与打包。

目的：在制作阶段拦住「假选择」「空引用」「定数没线索」这类失败，
而不是等玩家玩到一半才发现。
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


def validate_package(package_dir: str | Path) -> list[str]:
    root = Path(package_dir)
    problems: list[str] = []

    world_path = root / "world.json"
    if not world_path.exists():
        return [f"缺少 world.json: {root}"]

    try:
        world = json.loads(world_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"world.json 解析失败: {e}"]

    scenes_path = root / "scenes.json"
    endings_path = root / "endings.json"
    scenes = world.get("scenes")
    if scenes is None:
        if scenes_path.exists():
            scenes = json.loads(scenes_path.read_text(encoding="utf-8"))
        else:
            scenes = []
            problems.append("缺少 scenes.json 且 world.json 未内嵌 scenes")
    endings = world.get("endings")
    if endings is None or endings == []:
        if endings_path.exists():
            endings = json.loads(endings_path.read_text(encoding="utf-8"))
        else:
            endings = endings or []

    # --- 基础引用 ---
    stat_ids = {s.get("id") for s in (world.get("stats") or [])}
    char_ids = {c.get("id") for c in (world.get("characters") or [])}
    place_ids = {p.get("id") for p in (world.get("places") or [])}
    scene_ids = {s.get("id") for s in scenes}
    turns = {t.get("index") for t in (world.get("calendar") or {}).get("turns") or []}

    if not (world.get("players") or []):
        problems.append("没有可扮演身份 players")
    if not scenes:
        problems.append("没有 scenes")

    for s in scenes:
        sid = s.get("id")
        if not sid:
            problems.append("存在无 id 的 scene")
            continue
        if s.get("place") and s["place"] not in place_ids:
            problems.append(f"scene {sid} 地点不存在: {s.get('place')}")
        for cid in s.get("npcs") or []:
            if cid not in char_ids:
                problems.append(f"scene {sid} 人物不存在: {cid}")
        turn = s.get("turn")
        if turn is not None and turns and turn not in turns:
            problems.append(f"scene {sid} 的 turn={turn} 不在日历中")
        if s.get("trigger", {}).get("type") == "turn" and turn is None:
            problems.append(f"scene {sid} trigger=turn 但缺少 turn")

        if not s.get("choices"):
            # 允许纯叙述场景，但给个提示不记入错误
            pass

        effect_keys: list[tuple[str, str, Any]] = []
        for c in s.get("choices") or []:
            cid = c.get("id")
            eff = c.get("effects") or {}
            for k in (eff.get("stats") or {}):
                if k not in stat_ids:
                    problems.append(f"scene {sid}/{cid} 效果引用未知 stat: {k}")
            for k in (eff.get("relationships") or {}):
                if k not in char_ids:
                    problems.append(f"scene {sid}/{cid} 效果引用未知人物: {k}")
            for h in c.get("hooks") or []:
                for k in (h.get("stats") or {}):
                    if k not in stat_ids:
                        problems.append(f"scene {sid}/{cid} hook 引用未知 stat: {k}")
                for k in (h.get("relationships") or {}):
                    if k not in char_ids:
                        problems.append(f"scene {sid}/{cid} hook 引用未知人物: {k}")
                if h.get("scene_id") and h["scene_id"] not in scene_ids:
                    problems.append(f"scene {sid}/{cid} hook 目标场景不存在: {h.get('scene_id')}")
            # 假选择检测：效果指纹
            fp = json.dumps(
                {
                    "stats": eff.get("stats"),
                    "flags": eff.get("flags"),
                    "relationships": eff.get("relationships"),
                },
                sort_keys=True,
                ensure_ascii=False,
            )
            effect_keys.append((cid or "?", fp, c.get("text")))

        # 同一场景内完全相同的效果
        seen: dict[str, str] = {}
        for cid, fp, text in effect_keys:
            if fp in seen and fp != "{}":
                problems.append(
                    f"scene {sid} 疑似假选择：{seen[fp]} 与 {cid} 效果完全相同（「{text}」）"
                )
            seen[fp] = cid

    # --- 定数必须有前置线索 ---
    for e in world.get("canon_events") or []:
        eturn = e.get("turn")
        rumors = e.get("rumors") or []
        if not rumors:
            problems.append(f"canon {e.get('id')} 没有任何风声/物价/人际前置线索")
        else:
            for r in rumors:
                rt = r.get("turn", 0)
                if eturn is not None and rt >= eturn:
                    problems.append(
                        f"canon {e.get('id')} 的线索 turn={rt} 未早于事件 turn={eturn}"
                    )

    # --- 结局 ---
    if not endings:
        problems.append("没有 endings（结束时无法回答「我成为了谁」）")
    for e in endings:
        cond = e.get("conditions") or {}
        for k in (cond.get("stats_min") or {}):
            if k not in stat_ids:
                problems.append(f"ending {e.get('id')} 条件引用未知 stat: {k}")
        for k in (cond.get("rel_min") or {}):
            if k not in char_ids:
                problems.append(f"ending {e.get('id')} 条件引用未知人物: {k}")
        if not e.get("epithet"):
            problems.append(f"ending {e.get('id')} 缺少 epithet（「你是谁」一句话）")

    # --- 玩家起始关系 ---
    for p in world.get("players") or []:
        for k in (p.get("start_relationships") or {}):
            if k not in char_ids:
                problems.append(f"player {p.get('id')} 起始关系未知人物: {k}")
        for k in (p.get("start_stats") or {}):
            if k not in stat_ids:
                problems.append(f"player {p.get('id')} 起始属性未知: {k}")

    return problems


def build_package(
    extract_path: str | Path,
    out_dir: str | Path,
    scenes: list[dict[str, Any]],
    endings: list[dict[str, Any]],
    extra_world: dict[str, Any] | None = None,
) -> Path:
    """从提取结果 + 场景/结局，生成可玩数据包目录。

    extract 负责「世界骨架」；scenes/endings 负责「可玩血肉」。
    引擎只读 out_dir。
    """
    extract = json.loads(Path(extract_path).read_text(encoding="utf-8"))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # extract → world 骨架的映射（保持引擎无关字段）
    characters = []
    for c in extract.get("characters") or []:
        characters.append(
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "age": c.get("age", 30),
                "role": c.get("role", ""),
                "speech_style": c.get("speech_style", ""),
                "speech_examples": c.get("speech_examples", []),
                "wants": c.get("wants", ""),
                "blocks": c.get("blocks", ""),
                "costs": c.get("costs", ""),
                "summary": c.get("summary", ""),
            }
        )

    world: dict[str, Any] = {
        "meta": {
            "id": extract.get("meta", {}).get("source_id", "world"),
            "title": extract.get("meta", {}).get("source_title", "书中世界"),
            "version": "0.1.0",
            "source_note": extract.get("meta", {}).get("extraction_note", ""),
            "intro": (
                "这是一个从书籍结构长出来的可玩世界。\n"
                "原书已确定的大事会按时发生。你能改变的是处境、关系、代价、名声和结局。"
            ),
        },
        "calendar": extra_world.get("calendar") if extra_world else None,
        "stats": (extra_world or {}).get("stats", []),
        "places": (extra_world or {}).get("places", []),
        "characters": characters,
        "canon_events": (extra_world or {}).get("canon_events", []),
        "players": (extra_world or {}).get("players", []),
        "resources_note": extract.get("play_space_note", ""),
    }

    # 若提供了完整 world 覆盖，优先用覆盖里的骨架字段
    if extra_world:
        for key in (
            "meta",
            "calendar",
            "stats",
            "places",
            "canon_events",
            "players",
            "resources_note",
        ):
            if key in extra_world and extra_world[key] is not None:
                world[key] = extra_world[key]

    (out / "world.json").write_text(
        json.dumps(world, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "scenes.json").write_text(
        json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "endings.json").write_text(
        json.dumps(endings, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    problems = validate_package(out)
    if problems:
        raise ValueError("打包后校验失败:\n  - " + "\n  - ".join(problems))
    return out


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "data/samples/xinghuagou/package"
    probs = validate_package(target)
    if probs:
        print("FAIL")
        for p in probs:
            print(" -", p)
        sys.exit(1)
    print("OK")
