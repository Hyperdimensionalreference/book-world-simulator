"""无界面会话 API：给前端/测试用，复用同一套引擎逻辑。"""

from __future__ import annotations

from typing import Any

from .effects import apply_effect, fire_pending, meets_requirements, schedule_hooks
from .endings import evaluate_ending
from .models import SceneDef, WorldPackage, load_package
from .state import GameState


class GameSession:
    """一局游戏的会话对象。不打印，只返回结构化视图。"""

    def __init__(
        self,
        package: WorldPackage | str,
        player_id: str | None = None,
    ) -> None:
        if not isinstance(package, WorldPackage):
            package = load_package(package)
        self.package = package
        player = package.players[0]
        if player_id:
            player = next(p for p in package.players if p.id == player_id)
        self.player = player
        self.state = GameState.new(package, player)
        self._phase = "intro"  # intro | turn | choose_scene | choose_choice | ended
        self._current_scene: SceneDef | None = None
        self._messages: list[str] = []
        self._feedback: list[str] = []
        self._last_rumors: list[dict[str, str]] = []
        self._last_canons: list[dict[str, str]] = []
        self._ending: dict[str, Any] | None = None
        self._begin_turn()

    # ---------- 内部 ----------

    def _begin_turn(self) -> None:
        st = self.state
        if st.finished or st.turn >= self.package.turn_count():
            self._finish()
            return

        self._messages = []
        self._current_scene = None
        self._last_rumors = []
        self._last_canons = []

        for e in self.package.canon_events:
            for r in e.rumors:
                if r.turn == st.turn:
                    self._last_rumors.append(
                        {"text": r.text, "source": r.source, "canon": r.canon_event}
                    )
                    if r.text not in st.rumors_heard:
                        st.rumors_heard.append(r.text)

        late = fire_pending(st, self.package)
        for line in late:
            self._messages.append(line)

        for e in self.package.canon_events:
            if e.turn == st.turn:
                self._last_canons.append(
                    {"id": e.id, "title": e.title, "description": e.description}
                )
                st.add_memory(f"定数发生：{e.title}", actor="canon", tags=["canon"])
                st.flags[f"canon:{e.id}"] = True

        forced_key = st.flag("force_next")
        forced = None
        if forced_key:
            try:
                forced = self.package.scene(str(forced_key))
            except KeyError:
                forced = None
            st.flags.pop("force_next", None)

        scenes = self._available_scenes()
        mandatory = [s for s in scenes if s.mandatory]

        if forced is not None:
            self._enter_scene(forced)
            return

        if mandatory:
            self._enter_scene(mandatory[0])
            return

        if not scenes:
            self._messages.append("今天风平浪静。日子照过。")
            self._phase = "choose_scene"
            return

        self._phase = "choose_scene"

    def _available_scenes(self) -> list[SceneDef]:
        out = []
        for s in self.package.scenes:
            if s.once and s.id in self.state.seen_scenes:
                continue
            if self._scene_available(s):
                out.append(s)
        return out

    def _scene_available(self, scene: SceneDef) -> bool:
        st = self.state
        trig = scene.trigger or {}
        ttype = trig.get("type", "turn")

        if ttype == "turn":
            if scene.turn is None or scene.turn != st.turn:
                return False
        elif ttype == "window":
            start = int(trig.get("start", 0))
            end = int(trig.get("end", 10**9))
            if not (start <= st.turn <= end):
                return False
        elif ttype == "after_turn":
            if st.turn < int(trig.get("start", 0)):
                return False
        elif ttype == "flag":
            key = trig.get("flag")
            if not key or not st.flags.get(key):
                return False
        elif ttype == "unlocked":
            if not st.flags.get(f"unlocked:{scene.id}"):
                return False
        elif ttype == "always":
            pass
        else:
            return False

        if trig.get("flag") and ttype != "flag":
            if not st.flags.get(trig.get("flag")):
                return False
        if trig.get("not_flag") and st.flags.get(trig.get("not_flag")):
            return False
        if "min_turn" in trig and st.turn < int(trig["min_turn"]):
            return False
        if "max_turn" in trig and st.turn > int(trig["max_turn"]):
            return False

        ok, _ = meets_requirements(st, trig.get("requirements"))
        return ok

    def _enter_scene(self, scene: SceneDef) -> None:
        self._current_scene = scene
        self._phase = "choose_choice"
        st = self.state
        if scene.place:
            st.visited_places.add(scene.place)
        if scene.on_enter:
            apply_effect(st, self.package, scene.on_enter, source=f"enter:{scene.id}")
        if not scene.choices:
            st.seen_scenes.add(scene.id)
            self._current_scene = None
            self._advance_after_action()

    def _finish(self) -> None:
        st = self.state
        # 收尾强制结清所有延迟后果，别让债消失
        if st.pending:
            st.turn = max(st.turn, max(p.fire_turn for p in st.pending))
        late = fire_pending(st, self.package)
        self._messages.extend(late)
        ending = evaluate_ending(self.package, st)
        st.ending_id = ending.id
        st.finished = True
        self._phase = "ended"
        self._ending = {
            "id": ending.id,
            "title": ending.title,
            "body": ending.body,
            "epithet": ending.epithet,
        }

    def _advance_after_action(self) -> None:
        # 同回合内还有必选/可选则继续，否则进下一回合
        st = self.state
        scenes = self._available_scenes()
        mandatory = [s for s in scenes if s.mandatory]
        if mandatory:
            self._enter_scene(mandatory[0])
            return
        # 若还有可选且本回合尚未做过「日常选择」，停在 choose_scene
        # 简化：一次行动后若无强制，则推进时间（与 CLI 一致：每天一件事）
        st.turn += 1
        if st.turn >= self.package.turn_count():
            self._finish()
            return
        self._begin_turn()

    # ---------- 对外 ----------

    def snapshot(self) -> dict[str, Any]:
        st = self.state
        pkg = self.package
        place_name = ""
        if self._current_scene and self._current_scene.place:
            for p in pkg.places:
                if p.id == self._current_scene.place:
                    place_name = p.name
                    break

        scene_view = None
        if self._current_scene is not None:
            sc = self._current_scene
            choices = []
            for c in sc.choices:
                ok, reason = meets_requirements(st, c.requirements)
                choices.append(
                    {
                        "id": c.id,
                        "text": c.text,
                        "available": ok,
                        "reason": reason,
                        "immediate": c.immediate,
                    }
                )
            npcs = []
            for cid in sc.npcs:
                try:
                    ch = pkg.character(cid)
                    npcs.append({"id": ch.id, "name": ch.name, "role": ch.role, "style": ch.speech_style})
                except KeyError:
                    pass
            scene_view = {
                "id": sc.id,
                "title": sc.title,
                "place": place_name,
                "place_id": sc.place,
                "npcs": npcs,
                "narration": sc.narration,
                "choices": choices,
                "tags": sc.tags,
                "mandatory": sc.mandatory,
            }

        open_scenes = []
        if self._phase == "choose_scene":
            for sc in self._available_scenes():
                open_scenes.append(
                    {
                        "id": sc.id,
                        "title": sc.title,
                        "tags": sc.tags,
                        "place": sc.place,
                        "mandatory": sc.mandatory,
                    }
                )

        rel = []
        for cid, val in sorted(st.relationships.items(), key=lambda x: -x[1]):
            try:
                name = pkg.character(cid).name
            except KeyError:
                continue
            rel.append({"id": cid, "name": name, "value": val})

        stats = []
        for sdef in pkg.stats:
            stats.append(
                {
                    "id": sdef.id,
                    "name": sdef.name,
                    "value": st.get_stat(sdef.id),
                    "min": sdef.min,
                    "max": sdef.max,
                    "description": sdef.description,
                }
            )

        memories = [
            {"turn": m.turn, "text": m.text, "actor": m.actor, "tags": m.tags}
            for m in st.memory[-12:]
        ]

        pending = [p.to_dict() for p in st.pending[:8]]

        return {
            "phase": self._phase,
            "turn": st.turn,
            "turn_label": (
                "这一季过完了"
                if st.finished
                else pkg.turn_label(st.turn)
            ),
            "turn_note": (
                ""
                if st.finished or st.turn >= len(pkg.calendar.turns)
                else str(pkg.calendar.turns[st.turn].get("note") or "")
            ),
            "player": {
                "id": st.player_id,
                "name": st.player_name,
                "bio": self.player.bio,
            },
            "stats": stats,
            "relationships": rel,
            "messages": list(self._feedback) + list(self._messages),
            "feedback": list(self._feedback),
            "rumors": list(self._last_rumors),
            "canons": list(self._last_canons),
            "scene": scene_view,
            "open_scenes": open_scenes,
            "memory": memories,
            "pending": pending,
            "finished": st.finished,
            "ending": getattr(self, "_ending", None),
            "calendar": [
                {"index": t.get("index"), "label": t.get("label"), "note": t.get("note")}
                for t in pkg.calendar.turns
            ],
            "canon_timeline": [
                {"id": e.id, "turn": e.turn, "title": e.title, "done": bool(st.flags.get(f"canon:{e.id}"))}
                for e in pkg.canon_events
            ],
        }

    def choose(self, choice_id: str | None = None, scene_id: str | None = None) -> dict[str, Any]:
        st = self.state
        self._messages = []

        if st.finished:
            return self.snapshot()

        if self._phase == "choose_choice" and self._current_scene is not None:
            scene = self._current_scene
            if scene_id and scene.id != scene_id:
                # 允许前端乱序，仍以当前场景为准
                pass
            choice = next((c for c in scene.choices if c.id == choice_id), None)
            if choice is None:
                return self.snapshot()
            ok, reason = meets_requirements(st, choice.requirements)
            if not ok:
                self._messages.append(f"还做不到：{reason}")
                return self.snapshot()

            st.chosen[scene.id] = choice.id
            st.seen_scenes.add(scene.id)
            self._feedback = []
            if choice.immediate:
                self._feedback.append(choice.immediate)
            if choice.effects:
                for line in apply_effect(st, self.package, choice.effects, source=choice.id):
                    self._feedback.append(line)
            if choice.hooks:
                for line in schedule_hooks(st, choice.hooks, scene.id, choice.id):
                    self._feedback.append(line)
            self._current_scene = None
            self._advance_after_action()
            return self.snapshot()

        if self._phase == "choose_scene":
            if choice_id == "rest" or choice_id is None:
                self._feedback = ["你歇了一天。时间过去了。有些事不会因为你不看就不在。"]
                self.state.add_log("歇着")
                self._advance_after_action()
                return self.snapshot()
            scene = next((s for s in self._available_scenes() if s.id == choice_id), None)
            if scene is None:
                return self.snapshot()
            self._enter_scene(scene)
            return self.snapshot()

        return self.snapshot()


def open_session(package_dir: str, player_id: str | None = None) -> GameSession:
    return GameSession(load_package(package_dir), player_id=player_id)


def session_to_save(sess: GameSession) -> dict[str, Any]:
    """导出可持久化的存档载荷（不含 package 本体，只记路径与状态）。"""
    return {
        "package_id": sess.package.meta.get("id"),
        "package_title": sess.package.meta.get("title"),
        "player_id": sess.player.id,
        "state": sess.state.to_dict(),
        "phase": sess._phase,
        "current_scene_id": sess._current_scene.id if sess._current_scene else None,
        "feedback": list(sess._feedback),
        "messages": list(sess._messages),
        "ending": sess._ending,
    }


def session_from_save(payload: dict[str, Any], package_dir: str) -> GameSession:
    """从存档恢复会话。package_dir 必须与存档世界的 id 匹配。"""
    pkg = load_package(package_dir)
    player_id = payload.get("player_id")
    sess = GameSession(pkg, player_id=player_id)
    state = GameState.from_dict(payload.get("state") or {})
    # 校验归属
    if payload.get("package_id") and state.package_id != payload.get("package_id"):
        state.package_id = str(payload.get("package_id"))
    sess.state = state
    sess._phase = payload.get("phase") or (
        "ended" if state.finished else "choose_scene"
    )
    sess._current_scene = None
    scene_id = payload.get("current_scene_id")
    if sess._phase == "choose_choice":
        try:
            sess._current_scene = pkg.scene(scene_id) if scene_id else None
        except KeyError:
            sess._current_scene = None
        if sess._current_scene is None and not scene_id:
            mandatory = [scene for scene in sess._available_scenes() if scene.mandatory]
            if len(mandatory) == 1:
                sess._current_scene = mandatory[0]
        if sess._current_scene is None:
            # Older saves did not record the scene. Return to scene selection
            # instead of leaving the player unable to make a choice.
            sess._phase = "choose_scene"
    sess._feedback = list(payload.get("feedback") or [])
    sess._messages = list(payload.get("messages") or [])
    end = payload.get("ending")
    sess._ending = end if end else None
    if state.finished and not sess._ending:
        ending = evaluate_ending(sess.package, state)
        sess._ending = {
            "id": ending.id,
            "title": ending.title,
            "body": ending.body,
            "epithet": ending.epithet,
        }
    return sess
