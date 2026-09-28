"""游玩时的持久世界状态。

这里记住玩家做过的事、别人的看法、以及还没到期的延迟后果。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import HookDef, PlayerDef, WorldPackage


@dataclass
class PendingHook:
    fire_turn: int
    hook: HookDef
    source_scene: str
    source_choice: str

    def to_dict(self) -> dict[str, Any]:
        h = self.hook
        return {
            "fire_turn": self.fire_turn,
            "type": h.type,
            "text": h.text,
            "stats": h.stats,
            "flags": h.flags,
            "relationships": h.relationships,
            "scene_id": h.scene_id,
            "actor": h.actor,
            "source_scene": self.source_scene,
            "source_choice": self.source_choice,
        }


@dataclass
class MemoryItem:
    turn: int
    text: str
    actor: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class GameState:
    package_id: str
    player_id: str
    player_name: str
    turn: int = 0
    stats: dict[str, int] = field(default_factory=dict)
    flags: dict[str, Any] = field(default_factory=dict)
    relationships: dict[str, int] = field(default_factory=dict)
    memory: list[MemoryItem] = field(default_factory=list)
    pending: list[PendingHook] = field(default_factory=list)
    seen_scenes: set[str] = field(default_factory=set)
    chosen: dict[str, str] = field(default_factory=dict)
    visited_places: set[str] = field(default_factory=set)
    log: list[str] = field(default_factory=list)
    rumors_heard: list[str] = field(default_factory=list)
    finished: bool = False
    ending_id: str = ""

    @classmethod
    def new(cls, package: WorldPackage, player: PlayerDef) -> "GameState":
        stats = {s.id: s.start for s in package.stats}
        stats.update(player.start_stats)
        relationships = dict(player.start_relationships)
        state = cls(
            package_id=str(package.meta.get("id") or "world"),
            player_id=player.id,
            player_name=player.name,
            turn=0,
            stats=stats,
            flags=dict(player.start_flags),
            relationships=relationships,
            memory=[
                MemoryItem(turn=0, text=t, actor="origin", tags=["start"])
                for t in player.start_memory
            ],
        )
        return state

    def clamp_stats(self, package: WorldPackage) -> None:
        for sdef in package.stats:
            if sdef.id in self.stats:
                self.stats[sdef.id] = max(sdef.min, min(sdef.max, self.stats[sdef.id]))

    def add_memory(self, text: str, actor: str = "", tags: list[str] | None = None) -> None:
        self.memory.append(
            MemoryItem(turn=self.turn, text=text, actor=actor, tags=list(tags or []))
        )

    def add_log(self, text: str) -> None:
        self.log.append(f"[{self.turn}] {text}")

    def get_stat(self, sid: str, default: int = 0) -> int:
        return int(self.stats.get(sid, default))

    def rel(self, cid: str, default: int = 0) -> int:
        return int(self.relationships.get(cid, default))

    def flag(self, key: str, default: Any = False) -> Any:
        return self.flags.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "player_id": self.player_id,
            "player_name": self.player_name,
            "turn": self.turn,
            "stats": self.stats,
            "flags": self.flags,
            "relationships": self.relationships,
            "memory": [m.__dict__ for m in self.memory],
            "pending": [p.to_dict() for p in self.pending],
            "seen_scenes": sorted(self.seen_scenes),
            "chosen": self.chosen,
            "visited_places": sorted(self.visited_places),
            "log": self.log,
            "rumors_heard": self.rumors_heard,
            "finished": self.finished,
            "ending_id": self.ending_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        mem = [
            MemoryItem(
                turn=int(m.get("turn", 0)),
                text=str(m.get("text") or ""),
                actor=str(m.get("actor") or ""),
                tags=list(m.get("tags") or []),
            )
            for m in (data.get("memory") or [])
        ]
        pending = []
        for p in data.get("pending") or []:
            pending.append(
                PendingHook(
                    fire_turn=int(p.get("fire_turn", 0)),
                    hook=HookDef(
                        delay=0,
                        type=str(p.get("type") or "message"),
                        text=str(p.get("text") or ""),
                        stats=dict(p.get("stats") or {}),
                        flags=dict(p.get("flags") or {}),
                        relationships=dict(p.get("relationships") or {}),
                        scene_id=str(p.get("scene_id") or ""),
                        actor=str(p.get("actor") or ""),
                    ),
                    source_scene=str(p.get("source_scene") or ""),
                    source_choice=str(p.get("source_choice") or ""),
                )
            )
        st = cls(
            package_id=str(data.get("package_id") or "world"),
            player_id=str(data.get("player_id") or ""),
            player_name=str(data.get("player_name") or ""),
            turn=int(data.get("turn") or 0),
            stats=dict(data.get("stats") or {}),
            flags=dict(data.get("flags") or {}),
            relationships=dict(data.get("relationships") or {}),
            memory=mem,
            pending=pending,
            seen_scenes=set(data.get("seen_scenes") or []),
            chosen=dict(data.get("chosen") or {}),
            visited_places=set(data.get("visited_places") or []),
            log=list(data.get("log") or []),
            rumors_heard=list(data.get("rumors_heard") or []),
            finished=bool(data.get("finished", False)),
            ending_id=str(data.get("ending_id") or ""),
        )
        return st
