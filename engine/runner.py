"""主循环：推进时间、放出线索、跑场景、结算延迟后果、判定结局。

游玩过程不调用任何模型——全部读本地数据包。
"""

from __future__ import annotations

from typing import Callable, TextIO
import sys

from .effects import apply_effect, fire_pending, meets_requirements, schedule_hooks
from .endings import evaluate_ending
from .models import SceneDef, WorldPackage, load_package
from .state import GameState


PrintFn = Callable[[str], None]


class GameRunner:
    def __init__(
        self,
        package: WorldPackage,
        state: GameState,
        out: PrintFn | None = None,
        inp: Callable[[str], str] | None = None,
    ) -> None:
        self.package = package
        self.state = state
        self.out = out or (lambda s: print(s))
        self.inp = inp or input

    # ---------- 表现 ----------

    def say(self, text: str = "") -> None:
        self.out(text)

    def rule(self) -> None:
        self.say("─" * 36)

    def show_status(self) -> None:
        st = self.state
        label = self.package.turn_label(st.turn)
        self.rule()
        self.say(f"〔{label}〕 {st.player_name}")
        parts = []
        for sdef in self.package.stats:
            parts.append(f"{sdef.name}:{st.get_stat(sdef.id)}")
        self.say("  " + "  ".join(parts))
        if st.relationships:
            rel_bits = []
            for cid, val in sorted(st.relationships.items(), key=lambda x: -x[1])[:5]:
                try:
                    name = self.package.character(cid).name
                except KeyError:
                    name = cid
                rel_bits.append(f"{name}{val:+d}")
            self.say("  关系 " + " · ".join(rel_bits))
        self.rule()

    # ---------- 时间与线索 ----------

    def current_canon(self):
        return [e for e in self.package.canon_events if e.turn == self.state.turn]

    def current_rumors(self):
        out = []
        for e in self.package.canon_events:
            for r in e.rumors:
                if r.turn == self.state.turn:
                    out.append(r)
        return out

    def show_rumors(self) -> None:
        rumors = self.current_rumors()
        if not rumors:
            return
        self.say("【风声】")
        for r in rumors:
            src = f"（{r.source}）" if r.source else ""
            self.say(f"  · {r.text}{src}")
            if r.text not in self.state.rumors_heard:
                self.state.rumors_heard.append(r.text)
        self.say()

    def show_canon(self) -> None:
        events = self.current_canon()
        if not events:
            return
        for e in events:
            self.rule()
            self.say(f"【定数】{e.title}")
            self.say(e.description)
            self.say("（书里写定的事，照常发生。你左右不了它，但你站在哪里，由你。）")
            self.rule()
            self.state.add_memory(f"定数发生：{e.title}", actor="canon", tags=["canon"])
            self.state.flags[f"canon:{e.id}"] = True

    # ---------- 场景 ----------

    def scene_available(self, scene: SceneDef) -> bool:
        st = self.state
        if scene.once and scene.id in st.seen_scenes:
            return False

        trig = scene.trigger or {}
        ttype = trig.get("type", "turn")

        if ttype == "turn":
            if scene.turn is None:
                return False
            if scene.turn != st.turn:
                return False
        elif ttype == "window":
            start = int(trig.get("start", 0))
            end = int(trig.get("end", 10**9))
            if not (start <= st.turn <= end):
                return False
            if st.turn != start and scene.once and scene.id in st.seen_scenes:
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

        req_ok, _ = meets_requirements(st, trig.get("requirements"))
        return req_ok

    def available_scenes(self) -> list[SceneDef]:
        return [s for s in self.package.scenes if self.scene_available(s)]

    def force_next_scene(self) -> SceneDef | None:
        key = self.state.flag("force_next")
        if not key:
            return None
        try:
            return self.package.scene(str(key))
        except KeyError:
            return None

    def run_scene(self, scene: SceneDef) -> None:
        st = self.state
        self.rule()
        self.say(f"◆ {scene.title}")
        if scene.place:
            try:
                place = next(p for p in self.package.places if p.id == scene.place)
                self.say(f"  地点：{place.name}")
                st.visited_places.add(scene.place)
            except StopIteration:
                pass
        if scene.npcs:
            names = []
            for cid in scene.npcs:
                try:
                    names.append(self.package.character(cid).name)
                except KeyError:
                    names.append(cid)
            self.say(f"  在场：{'、'.join(names)}")
        self.rule()
        self.say(scene.narration)
        self.say()

        if scene.on_enter:
            apply_effect(st, self.package, scene.on_enter, source=f"enter:{scene.id}")

        # 强制场景也要有选择；没有选择就直接结束场景
        if not scene.choices:
            st.seen_scenes.add(scene.id)
            return

        usable = []
        for choice in scene.choices:
            ok, reason = meets_requirements(st, choice.requirements)
            usable.append((choice, ok, reason))

        self.say("你要——")
        for i, (choice, ok, reason) in enumerate(usable, 1):
            mark = "" if ok else f" 〔不可：{reason}〕"
            self.say(f"  {i}. {choice.text}{mark}")
        self.say()

        while True:
            raw = self.inp("选择编号 > ").strip()
            if raw.lower() in {"q", "quit", "exit"}:
                st.finished = True
                return
            try:
                idx = int(raw)
            except ValueError:
                self.say("请输入编号。")
                continue
            if not (1 <= idx <= len(usable)):
                self.say("没有这个选项。")
                continue
            choice, ok, reason = usable[idx - 1]
            if not ok:
                self.say(f"还做不到：{reason}")
                continue
            break

        st.chosen[scene.id] = choice.id
        st.seen_scenes.add(scene.id)

        if choice.immediate:
            self.say()
            self.say(choice.immediate)

        if choice.effects:
            self.say()
            for line in apply_effect(st, self.package, choice.effects, source=choice.id):
                self.say(f"  · {line}")

        if choice.hooks:
            for line in schedule_hooks(st, choice.hooks, scene.id, choice.id):
                self.say(f"  {line}")

        # 人物记住这件事
        for cid in scene.npcs:
            if choice.effects and cid in (choice.effects.relationships or {}):
                pass
            note = choice.effects.add_note if choice.effects else ""
            if note:
                st.add_memory(note, actor=cid, tags=["witness", choice.id])

        self.say()

    # ---------- 回合推进 ----------

    def play_turn(self) -> None:
        st = self.state
        self.show_status()
        self.show_rumors()

        # 延迟后果先回来
        late = fire_pending(st, self.package)
        if late:
            self.say("【回来的事】")
            for line in late:
                self.say(line)
            self.say()

        # 定数照常发生
        self.show_canon()

        forced = self.force_next_scene()
        if forced:
            st.flags.pop("force_next", None)
            self.run_scene(forced)
            return

        scenes = self.available_scenes()
        if not scenes:
            self.say("（今天风平浪静。日子照过。）")
            self.say()
            return

        # 若有必选项，优先
        mandatory = [s for s in scenes if s.mandatory]
        if mandatory:
            self.say("今天躲不开的事：")
            self.run_scene(mandatory[0])
            # 必选后，若还有时间，继续给可选
            rest = [s for s in self.available_scenes() if not s.mandatory]
            if rest:
                self.pick_and_run(rest, free_label="你还可以抽空做一件事")
            return

        self.pick_and_run(scenes, free_label="今天你只能顾上一件事")

    def pick_and_run(self, scenes: list[SceneDef], free_label: str) -> None:
        self.say(f"{free_label}：")
        for i, sc in enumerate(scenes, 1):
            tags = f"（{'/'.join(sc.tags)}）" if sc.tags else ""
            self.say(f"  {i}. {sc.title}{tags}")
        self.say(f"  0. 什么都不做，歇着")

        while True:
            raw = self.inp("去哪 / 做什么 > ").strip()
            if raw.lower() in {"q", "quit", "exit"}:
                self.state.finished = True
                return
            try:
                idx = int(raw)
            except ValueError:
                self.say("请输入编号。")
                continue
            if idx == 0:
                self.say()
                self.say("你在家坐着。时间过去了。有些事不会因为你不看就不在。")
                self.state.add_log("歇着")
                self.say()
                return
            if 1 <= idx <= len(scenes):
                self.run_scene(scenes[idx - 1])
                return
            self.say("没有这个选项。")

    def advance_time(self) -> None:
        self.state.turn += 1

    def run(self) -> GameState:
        st = self.state
        self.say()
        self.say("=" * 36)
        self.say(f"  {self.package.meta.get('title', '书中世界')}")
        self.say("=" * 36)
        self.say()
        self.say(self.package.meta.get("intro", ""))
        self.say()
        self.say("—— 你是 " + st.player_name + " ——")
        try:
            player = next(p for p in self.package.players if p.id == st.player_id)
            self.say(player.bio)
        except StopIteration:
            pass
        self.say()
        self.say("大事件会来。你改不了日历上写定的事。")
        self.say("但你和谁站在一起、付出什么、被人怎样记住——这些是你的。")
        self.say()

        total = self.package.turn_count()
        while not st.finished and st.turn < total:
            self.play_turn()
            if st.finished:
                break
            self.advance_time()

        if st.finished and st.turn >= total:
            st.finished = True

        return self.finish()

    def finish(self) -> GameState:
        st = self.state
        # 收尾时再结一次延迟后果（别让最后的债消失）
        late = fire_pending(st, self.package)
        if late:
            self.say("【最后回来的事】")
            for line in late:
                self.say(line)
            self.say()

        ending = evaluate_ending(self.package, st)
        st.ending_id = ending.id
        st.finished = True

        self.rule()
        self.say("【回望】")
        self.say(ending.title)
        self.say()
        self.say(ending.body)
        self.say()
        self.say(f"  ✦ {ending.epithet}")
        self.rule()

        # 轨迹摘要
        self.say("你留下的话与痕迹：")
        remembered = [m for m in st.memory if m.tags and m.tags != ["start"]]
        if not remembered:
            self.say("  （好像没被人记住什么。这也是一种结局。）")
        else:
            for m in remembered[-8:]:
                who = f"（{m.actor}）" if m.actor else ""
                self.say(f"  · {m.text}{who}")
        self.say()
        self.say(f"最终：{ending.title} —— {ending.epithet}")
        return st


def run_interactive(package_dir: str, player_id: str | None = None) -> GameState:
    package = load_package(package_dir)
    if not package.players:
        raise RuntimeError("数据包里没有可扮演身份")
    player = package.players[0]
    if player_id:
        player = next(p for p in package.players if p.id == player_id)

    state = GameState.new(package, player)
    runner = GameRunner(package, state)
    return runner.run()


def run_scripted(
    package_dir: str,
    choices: list[str],
    player_id: str | None = None,
    out: TextIO | None = None,
) -> GameState:
    """用预设选择跑一局，便于测试与生成示例游玩记录。"""
    package = load_package(package_dir)
    player = package.players[0]
    if player_id:
        player = next(p for p in package.players if p.id == player_id)
    state = GameState.new(package, player)

    script = list(choices)
    lines: list[str] = []

    def default_out(s: str) -> None:
        lines.append(s)
        if out is not None:
            print(s, file=out)
        elif out is None and choices is not None:
            # 静默收集
            pass

    def default_inp(prompt: str) -> str:
        val = script.pop(0) if script else "1"
        lines.append(f"{prompt}{val}")
        return str(val)

    runner = GameRunner(package, state, out=default_out, inp=default_inp)
    final = runner.run()
    # 附加文本给调用方
    final.flags["_transcript"] = "\n".join(lines)
    return final
