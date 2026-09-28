# -*- coding: utf-8 -*-
"""从结构提取「脚手架」出可玩数据包。

原则：
- 任意符合 extract_schema 的输入，都必须能得到能玩、能结档、能分叉的第一版
- 脚手架是「保底可玩」；人工/LLM 长肉是在此之上的加厚（杏花沟那种）
- 引擎零改动，只换 package
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


# ---------- 校验 extract ----------

def validate_extract(extract: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    meta = extract.get("meta") or {}
    if not meta.get("source_id"):
        errs.append("meta.source_id 缺失")
    if not meta.get("source_title"):
        errs.append("meta.source_title 缺失")

    wf = extract.get("world_frame") or {}
    for k in ("scale", "setting", "time_unit", "threat_style"):
        if not wf.get(k):
            errs.append(f"world_frame.{k} 缺失")

    conflicts = extract.get("conflict_sources") or []
    if len(conflicts) < 4:
        errs.append(f"conflict_sources 至少 4 个，现有 {len(conflicts)}")
    for c in conflicts:
        for k in ("id", "name", "type", "description", "stakes"):
            if not c.get(k):
                errs.append(f"conflict {c.get('id')} 缺 {k}")

    chars = extract.get("characters") or []
    if len(chars) < 5:
        errs.append(f"characters 至少 5 人，现有 {len(chars)}")
    for ch in chars:
        for k in ("id", "name", "role", "wants", "blocks", "costs", "speech_style"):
            if not ch.get(k):
                errs.append(f"character {ch.get('id')} 缺 {k}")

    canons = extract.get("canon_events") or []
    if len(canons) < 4:
        errs.append(f"canon_events 至少 4 个，现有 {len(canons)}")
    turns = []
    for e in canons:
        for k in ("id", "title", "description"):
            if not e.get(k):
                errs.append(f"canon {e.get('id')} 缺 {k}")
        fs = e.get("foreshadow") or []
        if len(fs) < 2:
            errs.append(f"canon {e.get('id')} 前置线索不足（需≥2）")
        if e.get("turn") is None:
            errs.append(f"canon {e.get('id')} 缺 turn")
        else:
            turns.append(int(e["turn"]))
    if turns != sorted(turns):
        errs.append("canon_events 的 turn 应递增")

    if not extract.get("play_space_note"):
        errs.append("play_space_note 缺失")

    # 小世界必须有的冲突类型覆盖（不要求全有，但要能自证密度）
    types = {c.get("type") for c in conflicts}
    required_soft = {"social_debt", "reputation", "exit_or_stay", "family_face", "material"}
    if len(types & required_soft) < 2:
        errs.append("小世界张力不足：conflict_sources 类型里应包含面子/人情/去留/财产等日常压力")

    return errs


# ---------- 日历 ----------

def build_calendar(extract: dict[str, Any]) -> dict[str, Any]:
    """按定数 turn 展开节拍；中间插过渡回合。"""
    canons = sorted(extract.get("canon_events") or [], key=lambda e: int(e.get("turn", 0)))
    max_turn = int(canons[-1]["turn"]) if canons else 8
    # 将 extract 的 turn 映射到 0..max_turn+1 的连续回合（含收尾）
    turns = []
    for i in range(max_turn + 2):
        label = f"第{i}幕"
        note = ""
        for e in canons:
            if int(e["turn"]) == i:
                label = str(e.get("title") or f"第{i}幕")
                note = "定数日"
                break
        else:
            # 普通幕
            label = f"间隙{i}"
            note = "日常"
        turns.append({"index": i, "label": label, "note": note})

    # 定数 turn 重新对齐到 extract 原 turn（若 extract turn 从 1 开始则 +0）
    # 为可玩性：把第一幕留给开局，最后多一幕回望
    # 将 canon 的 extract turn 视为绝对回合；脚手架沿用
    if canons and int(canons[0]["turn"]) == 0:
        pass
    return {"name": str(extract.get("meta", {}).get("source_title") or "世界") + " · 时序", "turns": turns}


# ---------- 脚手架场景 ----------

def _slug(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", text)[:32] or "x"


def scaffold_package(extract: dict[str, Any]) -> dict[str, Any]:
    """返回 {world, scenes, endings}"""
    meta = extract.get("meta") or {}
    wf = extract.get("world_frame") or {}
    chars = extract.get("characters") or []
    canons = sorted(extract.get("canon_events") or [], key=lambda e: int(e.get("turn", 0)))
    conflicts = extract.get("conflict_sources") or []
    players = extract.get("player_suggestions") or []

    # 人物
    world_chars = []
    for c in chars:
        world_chars.append(
            {
                "id": c["id"],
                "name": c.get("name") or c["id"],
                "age": int(c.get("age", 35)),
                "role": c.get("role", ""),
                "faction": c.get("faction", ""),
                "speech_style": c.get("speech_style", ""),
                "speech_examples": c.get("speech_examples") or [],
                "wants": c.get("wants", ""),
                "blocks": c.get("blocks", ""),
                "costs": c.get("costs", ""),
                "summary": c.get("summary") or c.get("role", ""),
            }
        )

    # 地点：从 world_frame 与冲突推断
    places = [
        {"id": "hub", "name": "中心", "description": wf.get("setting", "")},
        {"id": "work", "name": "劳作处", "description": "生计与规矩所在"},
        {"id": "street", "name": "消息场", "description": "风声最快的地方"},
        {"id": "home", "name": "私域", "description": "家里，账和心事最重"},
        {"id": "edge", "name": "边缘", "description": "离开与归来的交界"},
    ]

    # 玩家
    if players:
        p0 = players[0]
    else:
        p0 = {
            "id": "player",
            "name": "无名者",
            "age": 28,
            "bio": "你是这个世界里的普通人，不是被写定的主角。",
            "wants": "站稳、被记住、少欠一点",
            "blocks": "资源少、信息慢、身份低",
        }

    start_rel = dict(p0.get("start_relationships") or {})
    if not start_rel:
        for c in chars[:6]:
            if c["id"] != p0.get("id"):
                start_rel[c["id"]] = 10

    player_def = {
        "id": p0.get("id", "player"),
        "name": p0.get("name", "无名者"),
        "age": int(p0.get("age", 28)),
        "bio": p0.get("bio") or extract.get("play_space_note", ""),
        "start_stats": {},
        "start_relationships": start_rel,
        "start_flags": {},
        "start_memory": [extract.get("play_space_note", "")],
    }

    stats = [
        {"id": "money", "name": "钱", "start": 120, "min": 0, "max": 9999, "description": "可动用现钱"},
        {"id": "face", "name": "面子", "start": 50, "min": 0, "max": 100, "description": "说话分量"},
        {"id": "guts", "name": "硬气", "start": 40, "min": 0, "max": 100, "description": "心气"},
        {"id": "warmth", "name": "温度", "start": 40, "min": 0, "max": 100, "description": "是否上心"},
        {"id": "craft", "name": "手艺", "start": 35, "min": 0, "max": 100, "description": "立身本事"},
        {"id": "health", "name": "身子", "start": 75, "min": 0, "max": 100, "description": "体力"},
        {"id": "favor_out", "name": "欠你", "start": 0, "min": 0, "max": 20, "description": "人情债"},
        {"id": "favor_in", "name": "你欠", "start": 1, "min": 0, "max": 20, "description": "人情债"},
    ]

    calendar = build_calendar(extract)

    # 定数事件 + 风声
    canon_out = []
    for e in canons:
        rumors = []
        fs_list = e.get("foreshadow") or []
        turn_e = int(e.get("turn", 0))
        n = max(1, len(fs_list))
        for i, fs in enumerate(fs_list):
            # 全部严格早于定数日
            if turn_e <= 1:
                rt = 0
            else:
                rt = max(0, turn_e - 1 - (n - 1 - i))
            rumors.append({"turn": rt, "text": fs, "source": "风声", "canon_event": e["id"]})
        canon_out.append(
            {
                "id": e["id"],
                "turn": int(e.get("turn", 0)),
                "title": e.get("title", e["id"]),
                "description": e.get("description", ""),
                "fixed": True,
                "rumors": rumors,
            }
        )

    scenes: list[dict[str, Any]] = []

    # 1) 开局
    scenes.append(
        {
            "id": "s_open",
            "title": "开场",
            "turn": 0,
            "place": "home",
            "npcs": [c["id"] for c in chars[:3]],
            "trigger": {"type": "turn"},
            "mandatory": True,
            "tags": ["开局"],
            "narration": (
                f"{wf.get('setting', '')}\n\n"
                f"{player_def['bio']}\n\n"
                "书上写定的事会按期来。你能改的是处境、关系、代价，以及你成为谁。"
            ),
            "choices": [
                {
                    "id": "c_open_focus",
                    "text": "先顾眼前最急的一头。",
                    "effects": {
                        "stats": {"guts": 3},
                        "add_memory": ["你选择先顾眼前"],
                        "add_note": "你从具体难处下手",
                    },
                    "hooks": [],
                },
                {
                    "id": "c_open_listen",
                    "text": "先听风声，弄清谁想要什么。",
                    "effects": {
                        "stats": {"craft": 3, "warmth": 2},
                        "add_memory": ["你先听了风声"],
                        "add_note": "你把耳朵竖起来了",
                    },
                    "hooks": [{"delay": 2, "type": "message", "text": "你比别人早半步知道门道。", "stats": {"craft": 2}}],
                },
                {
                    "id": "c_open_hard",
                    "text": "把最难看的事先扛起来。",
                    "effects": {
                        "stats": {"guts": 5, "health": -3, "favor_in": 1},
                        "add_memory": ["你先扛了难看的事"],
                        "add_note": "你把担子放上了肩",
                    },
                    "hooks": [],
                },
            ],
        }
    )

    # 2) 每个冲突一场「取舍戏」
    npc_ids = [c["id"] for c in chars]
    for idx, conf in enumerate(conflicts):
        turn = 1 + (idx % max(1, int(canons[0]["turn"]) if canons else 4))
        if canons:
            # 塞进定数前的空隙
            span = int(canons[0]["turn"])
            turn = 1 + (idx % max(1, span))
        scenes.append(
            {
                "id": f"s_conf_{conf['id']}",
                "title": str(conf.get("name") or conf["id"]),
                "turn": turn,
                "place": ["hub", "work", "street", "home", "edge"][idx % 5],
                "npcs": [npc_ids[idx % len(npc_ids)], npc_ids[(idx + 1) % len(npc_ids)]],
                "trigger": {"type": "window", "start": turn, "end": turn + 2},
                "tags": ["冲突", conf.get("type", "other")],
                "narration": (
                    f"压力点：{conf.get('name')}\n\n"
                    f"{conf.get('description')}\n\n"
                    f"赌注是：{conf.get('stakes')}。\n\n"
                    f"{chars[idx % len(chars)].get('name', '有人')}在旁边，"
                    f"开口是：「{chars[idx % len(chars)].get('speech_examples') or [chars[idx % len(chars)].get('wants', '总得有个说法。')][0]}」\n"
                    "两头都想要，或者两头都不想失去。"
                ),
                "choices": [
                    {
                        "id": "c_face_on",
                        "text": "正面接住，把脸面和道理做足。",
                        "effects": {
                            "stats": {"face": 5, "guts": 3, "money": -15},
                            "relationships": {npc_ids[idx % len(npc_ids)]: 6},
                            "add_memory": [f"你在「{conf.get('name')}」上正面接住"],
                            "add_note": "你把体面买回来了",
                        },
                        "hooks": [
                            {
                                "delay": 3,
                                "type": "message",
                                "text": f"后来在{conf.get('name')}的事上，有人念你一句「做事实」。",
                                "stats": {"face": 2},
                                "actor": npc_ids[idx % len(npc_ids)],
                            }
                        ],
                    },
                    {
                        "id": "c_side_deal",
                        "text": "私下把事办成，先顾里子。",
                        "effects": {
                            "stats": {"money": 20, "face": -3, "craft": 3},
                            "relationships": {npc_ids[(idx + 1) % len(npc_ids)]: 4},
                            "add_memory": [f"你在「{conf.get('name')}」上先顾里子"],
                            "add_note": "你把里子保住了",
                        },
                        "hooks": [
                            {
                                "delay": 3,
                                "type": "message",
                                "text": "有人背后说你会打算。会打算，也是名声的一种。",
                                "stats": {"face": -1, "craft": 2},
                            }
                        ],
                    },
                    {
                        "id": "c_help_other",
                        "text": "把时间让给更难的人。",
                        "effects": {
                            "stats": {"warmth": 6, "favor_out": 1, "health": -4},
                            "relationships": {npc_ids[idx % len(npc_ids)]: 10},
                            "add_memory": [f"你在「{conf.get('name')}」上让了更难的人"],
                            "add_note": "你把难处往后挪了半步",
                        },
                        "hooks": [
                            {
                                "delay": 4,
                                "type": "message",
                                "text": "那人后来记得。记得这种东西，来得慢，落得重。",
                                "stats": {"warmth": 3},
                                "actor": npc_ids[idx % len(npc_ids)],
                                "relationships": {npc_ids[idx % len(npc_ids)]: 5},
                            }
                        ],
                    },
                ],
            }
        )

    # 3) 每个定数：预感日 + 当日必进
    for e in canons:
        turn = int(e.get("turn", 0))
        # 预感日（若有更早的空隙）
        if turn > 0:
            scenes.append(
                {
                    "id": f"s_rumor_{e['id']}",
                    "title": f"风声 · {e.get('title')}",
                    "turn": max(1, turn - 1),
                    "place": "street",
                    "npcs": [npc_ids[0], npc_ids[min(1, len(npc_ids) - 1)]],
                    "trigger": {"type": "window", "start": max(1, turn - 2), "end": turn - 1},
                    "tags": ["预感"],
                    "narration": (
                        "有话在传：\n"
                        + "\n".join(f"· {x}" for x in (e.get("foreshadow") or [])[:3])
                        + "\n\n你可以准备，也可以当没听见。"
                    ),
                    "choices": [
                        {
                            "id": "c_prepare",
                            "text": "顺着风声做些准备。",
                            "effects": {
                                "stats": {"craft": 4, "guts": 2, "money": -10},
                                "flags": {f"prepared:{e['id']}": True},
                                "add_memory": [f"你为「{e.get('title')}」做了准备"],
                                "add_note": "预感落到了手上",
                            },
                            "hooks": [
                                {
                                    "delay": 2,
                                    "type": "message",
                                    "text": "真到那日，你比别人少一分慌。",
                                    "stats": {"guts": 3, "craft": 2},
                                }
                            ],
                        },
                        {
                            "id": "c_ignore_rumor",
                            "text": "不听闲话，过自己的。",
                            "effects": {
                                "stats": {"guts": 2, "warmth": -2},
                                "flags": {f"ignored:{e['id']}": True},
                                "add_memory": ["你没把风声当回事"],
                                "add_note": "耳朵关上了一扇",
                            },
                            "hooks": [
                                {
                                    "delay": 2,
                                    "type": "message",
                                    "text": "事到临头，你才发现自己准备得太晚。",
                                    "stats": {"guts": -2, "face": -2},
                                }
                            ],
                        },
                    ],
                }
            )

        scenes.append(
            {
                "id": f"s_canon_{e['id']}",
                "title": str(e.get("title") or e["id"]),
                "turn": turn,
                "place": "hub",
                "npcs": [npc_ids[0], npc_ids[min(2, len(npc_ids) - 1)]],
                "trigger": {"type": "turn"},
                "mandatory": True,
                "tags": ["定数"],
                "narration": (
                    f"【定数】{e.get('title')}\n\n{e.get('description')}\n\n"
                    "这件事按书上写定的方向发生。你不能改写它。你只能选择以什么身份、什么处境、和谁一起面对。"
                ),
                "choices": [
                    {
                        "id": "c_stand_visible",
                        "text": "站到人前去，承担这一日。",
                        "effects": {
                            "stats": {"guts": 6, "face": 4, "health": -5},
                            "flags": {f"faced:{e['id']}": True},
                            "add_memory": [f"你在「{e.get('title')}」那日站在了人前"],
                            "add_note": "你没有躲",
                        },
                        "hooks": [
                            {
                                "delay": 2,
                                "type": "message",
                                "text": "有人记住了你在场。名是这样一点点长出来的。",
                                "stats": {"face": 3},
                            }
                        ],
                    },
                    {
                        "id": "c_stand_beside",
                        "text": "站在要紧的人身边。",
                        "effects": {
                            "stats": {"warmth": 6, "guts": 3},
                            "relationships": {npc_ids[0]: 8},
                            "flags": {f"beside:{e['id']}": True},
                            "add_memory": [f"你在「{e.get('title')}」那日守着要紧的人"],
                            "add_note": "你守住了具体的人",
                        },
                        "hooks": [
                            {
                                "delay": 3,
                                "type": "message",
                                "text": "那人后来把这份在场还了回来，也许很迟。",
                                "relationships": {npc_ids[0]: 6},
                                "actor": npc_ids[0],
                            }
                        ],
                    },
                    {
                        "id": "c_stand_low",
                        "text": "压低身子，先保住自己。",
                        "effects": {
                            "stats": {"guts": -3, "health": 3},
                            "flags": {f"hid:{e['id']}": True},
                            "add_memory": [f"你在「{e.get('title')}」那日低了头"],
                            "add_note": "你把影子留给了自己",
                        },
                        "hooks": [
                            {
                                "delay": 2,
                                "type": "message",
                                "text": "躲过去了。也远了。",
                                "stats": {"warmth": -2, "face": -2},
                            }
                        ],
                    },
                ],
            }
        )

    # 4) 收尾
    last = (int(canons[-1]["turn"]) if canons else 6) + 1
    scenes.append(
        {
            "id": "s_final",
            "title": "回望",
            "turn": last,
            "place": "edge",
            "npcs": [npc_ids[0]],
            "trigger": {"type": "turn"},
            "mandatory": True,
            "tags": ["回望"],
            "narration": "该来的定数都来了。你欠过谁、帮过谁、怕过什么、放不下什么——这些是你的。\n\n这就够下一段用了。",
            "choices": [
                {
                    "id": "c_final_yes",
                    "text": "把自己这一段，在心里过一遍。",
                    "effects": {"stats": {"guts": 2, "warmth": 2}, "add_memory": ["你认真回望了自己的这一段"], "add_note": "你看清了自己"},
                    "hooks": [],
                }
            ],
        }
    )

    # 结局
    endings = [
        {
            "id": "end_guardian",
            "title": "守住具体的人",
            "priority": 15,
            "conditions": {"stats_min": {"warmth": 65}, "rel_min": {npc_ids[0]: 40}},
            "epithet": "一个让身边人感到「有人上心」的人",
            "body": "你没有改写大势。\n可你让一些具体的人，没那么孤单。\n这世界会记住你的方式，不在功劳簿上，在人的嘴边。",
        },
        {
            "id": "end_pillar",
            "title": "站稳的人",
            "priority": 25,
            "conditions": {"stats_min": {"face": 60, "guts": 50}, "memory_min": 6},
            "epithet": "一个被当成靠山的人",
            "body": "风雨里你没塌。有人开始在你身上放一点指望。\n这不是英雄故事，是过日子的底盘。",
        },
        {
            "id": "end_craft",
            "title": "手里有活路",
            "priority": 35,
            "conditions": {"stats_min": {"craft": 65}},
            "epithet": "一个把本事攥在手里的人",
            "body": "本事是假不了的。明天也有活干，这比空话硬。",
        },
        {
            "id": "end_honest_debt",
            "title": "把账理清",
            "priority": 40,
            "conditions": {"stats_max": {"favor_in": 1}, "stats_min": {"guts": 45}},
            "epithet": "一个不被债压着走路的人",
            "body": "账清了，心里才安生。你把脊梁直起来了。",
        },
        {
            "id": "end_survivor",
            "title": "过完了这一段",
            "priority": 80,
            "conditions": {},
            "epithet": "一个在已知的岁月里认真活过的人",
            "body": "历史不转弯。但你的活法是你自己的。\n你站在过具体的位置，做过具体的选择。",
        },
        {
            "id": "end_cold",
            "title": "渐渐冷掉",
            "priority": 90,
            "conditions": {"stats_max": {"warmth": 25}},
            "epithet": "一个把自己护得太窄的人",
            "body": "你保全了许多东西。只是有些门，后来不再为你开了。",
        },
    ]

    world = {
        "meta": {
            "id": meta.get("source_id", "world"),
            "title": meta.get("source_title", "书中世界"),
            "version": "0.1.0-scaffold",
            "source_note": meta.get("extraction_note", "由结构脚手架生成；原书内容不进入数据包。"),
            "intro": f"{wf.get('setting', '')}\n\n{player_def['bio']}",
            "extract_source": {
                "source_id": meta.get("source_id"),
                "source_title": meta.get("source_title"),
                "source_type": meta.get("source_type"),
                "conflict_sources": [c["id"] for c in conflicts],
                "canon_events": [e["id"] for e in canons],
                "generator": "scaffold",
            },
            "play_space_note": extract.get("play_space_note", ""),
        },
        "resources_note": extract.get("play_space_note", ""),
        "world_rules": [
            "定数不改写，选择改变处境",
            "人情通过具体的人回来",
            "小世界靠日常压力驱动",
        ],
        "calendar": calendar,
        "stats": stats,
        "places": places,
        "characters": world_chars,
        "canon_events": canon_out,
        "players": [player_def],
    }

    return {"world": world, "scenes": scenes, "endings": endings}


def write_package(extract_path: str | Path, out_dir: str | Path) -> Path:
    extract = json.loads(Path(extract_path).read_text(encoding="utf-8"))
    errs = validate_extract(extract)
    if errs:
        raise ValueError("extract 不合法：\n  - " + "\n  - ".join(errs))

    bundle = scaffold_package(extract)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "world.json").write_text(json.dumps(bundle["world"], ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "scenes.json").write_text(json.dumps(bundle["scenes"], ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "endings.json").write_text(json.dumps(bundle["endings"], ensure_ascii=False, indent=2), encoding="utf-8")

    from production.validate import validate_package

    problems = validate_package(out)
    if problems:
        raise ValueError("脚手架打包后校验失败：\n  - " + "\n  - ".join(problems))
    return out


if __name__ == "__main__":
    import sys

    src = sys.argv[1] if len(sys.argv) > 1 else "data/samples/xinghuagou/extract/world_extract.json"
    dst = sys.argv[2] if len(sys.argv) > 2 else "data/samples/_scaffold_out/package"
    path = write_package(src, dst)
    print("scaffolded", path)
