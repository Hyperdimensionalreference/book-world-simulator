"""世界数据包的结构定义与加载。

数据包与引擎分离：换书只换数据，不改这里的类型。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class StatDef:
    id: str
    name: str
    start: int
    min: int = 0
    max: int = 100
    description: str = ""


@dataclass
class CharacterDef:
    id: str
    name: str
    age: int
    role: str
    faction: str = ""
    speech_style: str = ""
    speech_examples: list[str] = field(default_factory=list)
    wants: str = ""
    blocks: str = ""
    costs: str = ""
    summary: str = ""


@dataclass
class PlaceDef:
    id: str
    name: str
    description: str = ""


@dataclass
class RumorDef:
    turn: int
    text: str
    source: str = ""
    canon_event: str = ""


@dataclass
class CanonEventDef:
    id: str
    turn: int
    title: str
    description: str
    rumors: list[RumorDef] = field(default_factory=list)
    fixed: bool = True


@dataclass
class EffectDef:
    stats: dict[str, int] = field(default_factory=dict)
    flags: dict[str, Any] = field(default_factory=dict)
    relationships: dict[str, int] = field(default_factory=dict)
    add_memory: list[str] = field(default_factory=list)
    add_note: str = ""


@dataclass
class HookDef:
    """延迟后果：若干回合后再回来的东西。"""

    delay: int
    type: str  # message | flag | stats | relationships | unlock_scene | force_scene
    text: str = ""
    stats: dict[str, int] = field(default_factory=dict)
    flags: dict[str, Any] = field(default_factory=dict)
    relationships: dict[str, int] = field(default_factory=dict)
    scene_id: str = ""
    actor: str = ""  # 谁记得这件事（用于回放/结局）


@dataclass
class ChoiceDef:
    id: str
    text: str
    requirements: dict[str, Any] = field(default_factory=dict)
    effects: EffectDef = field(default_factory=EffectDef)
    immediate: str = ""
    hooks: list[HookDef] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class SceneDef:
    id: str
    title: str
    turn: int | None
    place: str = ""
    npcs: list[str] = field(default_factory=list)
    trigger: dict[str, Any] = field(default_factory=dict)
    narration: str = ""
    choices: list[ChoiceDef] = field(default_factory=list)
    on_enter: EffectDef = field(default_factory=EffectDef)
    mandatory: bool = False
    once: bool = True
    tags: list[str] = field(default_factory=list)


@dataclass
class EndingDef:
    id: str
    title: str
    priority: int
    conditions: dict[str, Any] = field(default_factory=dict)
    body: str = ""
    epithet: str = ""  # 「你成为了什么样的人」


@dataclass
class PlayerDef:
    id: str
    name: str
    age: int
    bio: str = ""
    start_stats: dict[str, int] = field(default_factory=dict)
    start_relationships: dict[str, int] = field(default_factory=dict)
    start_flags: dict[str, Any] = field(default_factory=dict)
    start_memory: list[str] = field(default_factory=list)


@dataclass
class CalendarDef:
    name: str
    turns: list[dict[str, Any]]  # {index, label, note}


@dataclass
class WorldPackage:
    meta: dict[str, Any]
    calendar: CalendarDef
    stats: list[StatDef]
    characters: list[CharacterDef]
    places: list[PlaceDef]
    canon_events: list[CanonEventDef]
    players: list[PlayerDef]
    scenes: list[SceneDef]
    endings: list[EndingDef]
    resources_note: str = ""

    def stat(self, sid: str) -> StatDef:
        for s in self.stats:
            if s.id == sid:
                return s
        raise KeyError(f"unknown stat: {sid}")

    def character(self, cid: str) -> CharacterDef:
        for c in self.characters:
            if c.id == cid:
                return c
        raise KeyError(f"unknown character: {cid}")

    def scene(self, sid: str) -> SceneDef:
        for s in self.scenes:
            if s.id == sid:
                return s
        raise KeyError(f"unknown scene: {sid}")

    def turn_count(self) -> int:
        return len(self.calendar.turns)

    def turn_label(self, index: int) -> str:
        if 0 <= index < len(self.calendar.turns):
            return str(self.calendar.turns[index].get("label", f"第{index}日"))
        return f"第{index}日"


def _effect_from_dict(data: dict[str, Any] | None) -> EffectDef:
    data = data or {}
    return EffectDef(
        stats=dict(data.get("stats") or {}),
        flags=dict(data.get("flags") or {}),
        relationships=dict(data.get("relationships") or {}),
        add_memory=list(data.get("add_memory") or []),
        add_note=str(data.get("add_note") or ""),
    )


def _hook_from_dict(data: dict[str, Any]) -> HookDef:
    return HookDef(
        delay=int(data.get("delay", 1)),
        type=str(data.get("type", "message")),
        text=str(data.get("text") or ""),
        stats=dict(data.get("stats") or {}),
        flags=dict(data.get("flags") or {}),
        relationships=dict(data.get("relationships") or {}),
        scene_id=str(data.get("scene_id") or ""),
        actor=str(data.get("actor") or ""),
    )


def _choice_from_dict(data: dict[str, Any]) -> ChoiceDef:
    return ChoiceDef(
        id=str(data["id"]),
        text=str(data.get("text") or ""),
        requirements=dict(data.get("requirements") or {}),
        effects=_effect_from_dict(data.get("effects")),
        immediate=str(data.get("immediate") or ""),
        hooks=[_hook_from_dict(h) for h in (data.get("hooks") or [])],
        tags=list(data.get("tags") or []),
    )


def _scene_from_dict(data: dict[str, Any]) -> SceneDef:
    turn = data.get("turn")
    return SceneDef(
        id=str(data["id"]),
        title=str(data.get("title") or data["id"]),
        turn=None if turn is None else int(turn),
        place=str(data.get("place") or ""),
        npcs=list(data.get("npcs") or []),
        trigger=dict(data.get("trigger") or {}),
        narration=str(data.get("narration") or ""),
        choices=[_choice_from_dict(c) for c in (data.get("choices") or [])],
        on_enter=_effect_from_dict(data.get("on_enter")),
        mandatory=bool(data.get("mandatory", False)),
        once=bool(data.get("once", True)),
        tags=list(data.get("tags") or []),
    )


def load_package(package_dir: str | Path) -> WorldPackage:
    """从数据包目录加载可游玩世界。

    目录内需包含 world.json；scenes/endings 可内嵌在 world.json，
    也可拆成 scenes.json / endings.json。
    """
    root = Path(package_dir)
    world_path = root / "world.json"
    if not world_path.exists():
        raise FileNotFoundError(f"world.json not found in {root}")

    raw = json.loads(world_path.read_text(encoding="utf-8"))

    scenes_raw = raw.get("scenes")
    if scenes_raw is None:
        scenes_path = root / "scenes.json"
        if scenes_path.exists():
            scenes_raw = json.loads(scenes_path.read_text(encoding="utf-8"))
        else:
            scenes_raw = []

    endings_raw = raw.get("endings")
    if endings_raw is None or endings_raw == []:
        endings_path = root / "endings.json"
        if endings_path.exists():
            endings_raw = json.loads(endings_path.read_text(encoding="utf-8"))
        else:
            endings_raw = endings_raw or []

    calendar_raw = raw.get("calendar") or {}
    calendar = CalendarDef(
        name=str(calendar_raw.get("name") or "时序"),
        turns=list(calendar_raw.get("turns") or []),
    )

    stats = [
        StatDef(
            id=str(s["id"]),
            name=str(s.get("name") or s["id"]),
            start=int(s.get("start", 0)),
            min=int(s.get("min", 0)),
            max=int(s.get("max", 100)),
            description=str(s.get("description") or ""),
        )
        for s in (raw.get("stats") or [])
    ]

    characters = [
        CharacterDef(
            id=str(c["id"]),
            name=str(c.get("name") or c["id"]),
            age=int(c.get("age", 0)),
            role=str(c.get("role") or ""),
            faction=str(c.get("faction") or ""),
            speech_style=str(c.get("speech_style") or ""),
            speech_examples=list(c.get("speech_examples") or []),
            wants=str(c.get("wants") or ""),
            blocks=str(c.get("blocks") or ""),
            costs=str(c.get("costs") or ""),
            summary=str(c.get("summary") or ""),
        )
        for c in (raw.get("characters") or [])
    ]

    places = [
        PlaceDef(
            id=str(p["id"]),
            name=str(p.get("name") or p["id"]),
            description=str(p.get("description") or ""),
        )
        for p in (raw.get("places") or [])
    ]

    canon_events: list[CanonEventDef] = []
    for e in raw.get("canon_events") or []:
        rumors = [
            RumorDef(
                turn=int(r.get("turn", 0)),
                text=str(r.get("text") or ""),
                source=str(r.get("source") or ""),
                canon_event=str(r.get("canon_event") or e.get("id") or ""),
            )
            for r in (e.get("rumors") or [])
        ]
        canon_events.append(
            CanonEventDef(
                id=str(e["id"]),
                turn=int(e.get("turn", 0)),
                title=str(e.get("title") or e["id"]),
                description=str(e.get("description") or ""),
                rumors=rumors,
                fixed=bool(e.get("fixed", True)),
            )
        )

    players = [
        PlayerDef(
            id=str(p["id"]),
            name=str(p.get("name") or p["id"]),
            age=int(p.get("age", 0)),
            bio=str(p.get("bio") or ""),
            start_stats=dict(p.get("start_stats") or {}),
            start_relationships=dict(p.get("start_relationships") or {}),
            start_flags=dict(p.get("start_flags") or {}),
            start_memory=list(p.get("start_memory") or []),
        )
        for p in (raw.get("players") or [])
    ]

    endings = [
        EndingDef(
            id=str(e["id"]),
            title=str(e.get("title") or e["id"]),
            priority=int(e.get("priority", 100)),
            conditions=dict(e.get("conditions") or {}),
            body=str(e.get("body") or ""),
            epithet=str(e.get("epithet") or ""),
        )
        for e in endings_raw
    ]

    return WorldPackage(
        meta=dict(raw.get("meta") or {}),
        calendar=calendar,
        stats=stats,
        characters=characters,
        places=places,
        canon_events=canon_events,
        players=players,
        scenes=[_scene_from_dict(s) for s in scenes_raw],
        endings=endings,
        resources_note=str(raw.get("resources_note") or ""),
    )
