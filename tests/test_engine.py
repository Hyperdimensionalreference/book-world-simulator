"""引擎与数据包的关键防线测试。

运行：python -m pytest tests/ -q
或：  python tests/test_engine.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.effects import fire_pending, schedule_hooks, apply_effect, meets_requirements
from engine.endings import evaluate_ending
from engine.models import EffectDef, HookDef, load_package
from engine.runner import GameRunner
from engine.state import GameState
from production.validate import validate_package

PKG = ROOT / "data" / "samples" / "xinghuagou" / "package"


def scripted_run(choices: list[str] | None = None, prefer: str = "low") -> tuple[GameState, list[str]]:
    """跑一局。

    - choices: 显式选项编号队列（可选）
    - prefer: 脚本耗尽或未给队列时的策略 low=取最小编号, high=取最大可用编号
    """
    package = load_package(PKG)
    player = package.players[0]
    state = GameState.new(package, player)
    remaining = list(choices or [])
    lines: list[str] = []
    buffer: list[str] = []

    def out(s: str) -> None:
        lines.append(s)
        buffer.append(s)

    def inp(prompt: str) -> str:
        # 从最近输出里解析可点编号
        numbered = []
        for line in reversed(buffer[-40:]):
            stripped = line.strip()
            if not stripped:
                continue
            if not (len(stripped) > 2 and stripped[0].isdigit() and stripped[1] == "."):
                continue
            try:
                num = int(stripped.split(".", 1)[0])
            except ValueError:
                continue
            if num == 0:
                continue
            if "不可" in stripped:
                continue
            numbered.append(num)
        if remaining:
            val = remaining.pop(0)
        elif numbered:
            numbered = sorted(numbered)
            val = numbered[0] if prefer == "low" else numbered[-1]
        else:
            val = "1"
        lines.append(f"{prompt}{val}")
        buffer.append(f"{prompt}{val}")
        return str(val)

    runner = GameRunner(package, state, out=out, inp=inp)
    final = runner.run()
    return final, lines


class TestPackage(unittest.TestCase):
    def test_package_valid(self):
        problems = validate_package(PKG)
        self.assertEqual(problems, [])

    def test_loads_scenes_and_endings(self):
        pkg = load_package(PKG)
        self.assertGreaterEqual(len(pkg.scenes), 15)
        self.assertGreaterEqual(len(pkg.endings), 5)
        self.assertGreaterEqual(len(pkg.canon_events), 6)

    def test_canon_have_early_rumors(self):
        pkg = load_package(PKG)
        for e in pkg.canon_events:
            self.assertTrue(e.rumors, f"{e.id} 无前置线索")
            for r in e.rumors:
                self.assertLess(r.turn, e.turn, f"{e.id} 线索不早于事件")


class TestHistoryDoesNotBend(unittest.TestCase):
    """历史不转弯：定数事件无论怎么选都会发生。"""

    def test_canon_flags_always_set(self):
        state, _ = scripted_run(prefer="low")
        for cid in [
            "canon:canon_land_survey",
            "canon:canon_zhao_engagement",
            "canon:canon_li_illness",
            "canon:canon_li_return",
            "canon:canon_bride_pressure",
            "canon:canon_li_death",
            "canon:canon_school_close",
            "canon:canon_year_end",
        ]:
            self.assertTrue(state.flags.get(cid), f"定数未发生: {cid}")

    def test_different_choices_same_canon(self):
        a, _ = scripted_run(prefer="low")
        b, _ = scripted_run(prefer="high")
        for cid in ["canon:canon_land_survey", "canon:canon_li_death", "canon:canon_year_end"]:
            self.assertTrue(a.flags.get(cid))
            self.assertTrue(b.flags.get(cid))
        # 但处境应不同：选择轨迹、关系或钱
        self.assertNotEqual(a.chosen.get("s_open_home"), b.chosen.get("s_open_home"))
        self.assertNotEqual(a.relationships.get("li_jianguo"), b.relationships.get("li_jianguo"))
        self.assertNotEqual(a.stats.get("money"), b.stats.get("money"))


class TestDelayedConsequences(unittest.TestCase):
    def test_hooks_fire_later(self):
        package = load_package(PKG)
        player = package.players[0]
        state = GameState.new(package, player)
        hook = HookDef(delay=3, type="message", text="后来的事", actor="x", stats={"face": 2})
        schedule_hooks(state, [hook], "s_test", "c_test")
        self.assertEqual(len(state.pending), 1)
        state.turn = 1
        self.assertEqual(fire_pending(state, package), [])
        self.assertEqual(len(state.pending), 1)
        state.turn = 3
        lines = fire_pending(state, package)
        self.assertTrue(any("后来的事" in x for x in lines))
        self.assertEqual(state.get_stat("face"), 52)
        self.assertEqual(len(state.pending), 0)

    def test_playthrough_has_delayed_lines(self):
        state, lines = scripted_run(prefer="low")
        text = "\n".join(lines)
        self.assertIn("迟来的后果", text)
        # 记忆里应有延迟回来的痕迹
        tags = {t for m in state.memory for t in m.tags}
        self.assertIn("delayed", tags)

    def test_relationship_remembers(self):
        state, _ = scripted_run(prefer="low")
        # 长期后果：小雨关系应明显高于开局
        self.assertGreaterEqual(state.relationships.get("ma_xiaoyu", 0), 60)


class TestSmallWorldHasWork(unittest.TestCase):
    def test_conflict_sources_present(self):
        pkg = load_package(PKG)
        # 土地、彩礼、人情、丧事、离开/留下 都有场景
        tags = {t for s in pkg.scenes for t in s.tags}
        joined = " ".join(tags)
        for key in ["土地", "彩礼", "人情", "妹妹", "离开", "照应"]:
            self.assertIn(key, joined, f"缺少冲突标签 {key}")

    def test_choices_are_genuine(self):
        problems = validate_package(PKG)
        self.assertFalse(any("假选择" in p for p in problems))


class TestEndings(unittest.TestCase):
    def test_epithet_answers_who_you_are(self):
        pkg = load_package(PKG)
        for e in pkg.endings:
            self.assertTrue(e.epithet.strip(), f"{e.id} 无 epithet")
            self.assertTrue(e.body.strip(), f"{e.id} 无 body")

    def test_endings_differ_by_play(self):
        a, _ = scripted_run(prefer="low")
        b, _ = scripted_run(prefer="high")
        self.assertTrue(a.ending_id)
        self.assertTrue(b.ending_id)
        # 两条线至少在情绪/关系上分叉（结局未必强制不同，但过程必须不同）
        self.assertNotEqual(a.chosen.get("s_open_home"), b.chosen.get("s_open_home"))
        self.assertNotEqual(a.relationships.get("ma_xiaoyu"), b.relationships.get("ma_xiaoyu"))


class TestRequirements(unittest.TestCase):
    def test_money_gate(self):
        package = load_package(PKG)
        player = package.players[0]
        state = GameState.new(package, player)
        state.stats["money"] = 10
        ok, reason = meets_requirements(state, {"stats": {"money": {"min": 80}}})
        self.assertFalse(ok)
        state.stats["money"] = 100
        ok, _ = meets_requirements(state, {"stats": {"money": {"min": 80}}})
        self.assertTrue(ok)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
