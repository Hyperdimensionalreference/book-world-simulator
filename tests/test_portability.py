# -*- coding: utf-8 -*-
"""换书复用测试：同一引擎、同一套流水线，两本气质完全不同的书。

跑：python tests/test_portability.py
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.session import GameSession
from production.pipeline import validate_extract  # noqa: F401
from production.scaffold import scaffold_package, validate_extract as ve, write_package
from production.validate import validate_package

BOOKS = {
    "xinghuagou": {
        "extract": ROOT / "data/samples/xinghuagou/extract/world_extract.json",
        "handmade": ROOT / "data/samples/xinghuagou/package",
        "scaffold": ROOT / "data/samples/xinghuagou/package_scaffold",
    },
    "tongzilou": {
        "extract": ROOT / "data/samples/tongzilou/extract/world_extract.json",
        "scaffold": ROOT / "data/samples/tongzilou/package",
    },
}


def play(pkg: str | Path, prefer: str = "low") -> GameSession:
    s = GameSession(str(pkg))
    steps = 0
    while steps < 45:
        steps += 1
        snap = s.snapshot()
        if snap.get("finished"):
            break
        if snap.get("scene"):
            av = [c for c in snap["scene"]["choices"] if c.get("available")]
            if not av:
                break
            pick = av[0] if prefer == "low" else av[-1]
            s.choose(pick["id"])
        else:
            opens = snap.get("open_scenes") or []
            if not opens:
                s.choose("rest")
            else:
                pick = opens[0] if prefer == "low" else opens[-1]
                s.choose(pick["id"])
    return s


class TestExtractSchema(unittest.TestCase):
    def test_both_extracts_valid(self):
        for name, cfg in BOOKS.items():
            extract = json.loads(cfg["extract"].read_text(encoding="utf-8"))
            errs = ve(extract)
            self.assertEqual(errs, [], f"{name} extract: {errs}")

    def test_extracts_are_different_worlds(self):
        a = json.loads(BOOKS["xinghuagou"]["extract"].read_text(encoding="utf-8"))
        b = json.loads(BOOKS["tongzilou"]["extract"].read_text(encoding="utf-8"))
        self.assertNotEqual(a["meta"]["source_id"], b["meta"]["source_id"])
        self.assertNotEqual(a["world_frame"]["scale"], b["world_frame"]["scale"])
        ids_a = {c["id"] for c in a["characters"]}
        ids_b = {c["id"] for c in b["characters"]}
        self.assertFalse(ids_a & ids_b, "两本书的人物 id 不应撞车")


class TestScaffoldAlwaysPlayable(unittest.TestCase):
    def test_scaffold_packages_validate(self):
        for name, cfg in BOOKS.items():
            problems = validate_package(cfg["scaffold"])
            self.assertEqual(problems, [], f"{name} scaffold: {problems}")

    def test_scaffold_endings_have_epithet(self):
        for name, cfg in BOOKS.items():
            endings = json.loads((cfg["scaffold"] / "endings.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(endings), 5)
            for e in endings:
                self.assertTrue(e.get("epithet"))

    def test_scaffold_canon_have_rumors(self):
        for name, cfg in BOOKS.items():
            world = json.loads((cfg["scaffold"] / "world.json").read_text(encoding="utf-8"))
            for e in world["canon_events"]:
                self.assertGreaterEqual(len(e.get("rumors") or []), 2)
                for r in e["rumors"]:
                    self.assertLess(r["turn"], e["turn"])


class TestAnyBookPlaysToEnding(unittest.TestCase):
    def test_tongzilou_full_run(self):
        s = play(BOOKS["tongzilou"]["scaffold"], prefer="low")
        self.assertTrue(s.state.finished)
        self.assertTrue(s.state.ending_id)
        self.assertTrue(s.state.flags.get("canon:canon_room_list"))
        self.assertTrue(s.state.flags.get("canon:canon_year_settle"))
        self.assertEqual(len(s.state.pending), 0)

    def test_tongzilou_diverges(self):
        a = play(BOOKS["tongzilou"]["scaffold"], prefer="low")
        b = play(BOOKS["tongzilou"]["scaffold"], prefer="high")
        self.assertTrue(a.state.ending_id)
        self.assertTrue(b.state.ending_id)
        self.assertNotEqual(a.state.chosen.get("s_open"), b.state.chosen.get("s_open"))
        # 定数相同
        for k in ["canon:canon_room_list", "canon:canon_injury", "canon:canon_factory_wave"]:
            self.assertTrue(a.state.flags.get(k))
            self.assertTrue(b.state.flags.get(k))

    def test_xinghuagou_scaffold_also_plays(self):
        s = play(BOOKS["xinghuagou"]["scaffold"], prefer="low")
        self.assertTrue(s.state.finished)
        self.assertTrue(s.state.ending_id)

    def test_handmade_still_plays(self):
        s = play(BOOKS["xinghuagou"]["handmade"], prefer="low")
        self.assertTrue(s.state.finished)
        self.assertEqual(s.state.ending_id, "end_li_family")


class TestEngineUnchanged(unittest.TestCase):
    def test_same_engine_class_for_all(self):
        for name, cfg in BOOKS.items():
            pkg = cfg["scaffold"]
            s = GameSession(str(pkg))
            snap = s.snapshot()
            self.assertIn(snap["phase"], {"choose_choice", "choose_scene", "ended"})
            self.assertTrue(snap["stats"])


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
