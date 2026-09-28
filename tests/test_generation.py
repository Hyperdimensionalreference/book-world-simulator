"""第三本原创短篇的制作闭环与可续跑模型阶段。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.session import GameSession  # noqa: E402
from production.generate_world import generate  # noqa: E402
from production.quality_check import review_package  # noqa: E402
from production.scaffold import scaffold_package  # noqa: E402
from production.validate import validate_package  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "nandi"
EXTRACT = json.loads((FIXTURE / "extract.json").read_text(encoding="utf-8"))


def play_to_end(package: Path, last: bool = False) -> GameSession:
    session = GameSession(str(package))
    for _ in range(55):
        snap = session.snapshot()
        if snap["finished"]:
            break
        if snap["scene"]:
            available = [choice for choice in snap["scene"]["choices"] if choice["available"]]
            session.choose((available[-1] if last else available[0])["id"])
        else:
            scenes = snap["open_scenes"]
            session.choose((scenes[-1] if last else scenes[0])["id"] if scenes else "rest")
    return session


def fake_chat(prompt: str, system: str = "") -> str:
    if "<source>" in prompt:
        return json.dumps({"setting": "南堤渡口", "characters": ["彭枝", "阿六"], "conflicts": ["停航后的工钱"], "events": ["新桥开通"]}, ensure_ascii=False)
    if prompt.startswith("合并以下结构笔记"):
        return json.dumps({"setting": "南堤渡口", "characters": ["彭枝", "阿六"], "conflicts": ["停航后的工钱"], "events": ["新桥开通"]}, ensure_ascii=False)
    if "结构笔记：" in prompt:
        return json.dumps(EXTRACT, ensure_ascii=False)
    if "\n场景：" in prompt:
        scene = json.loads(prompt.split("\n场景：", 1)[1])
        choices = []
        for choice in scene["choices"]:
            choices.append({
                "id": choice["id"],
                "text": f"在{scene['id']}选择{choice['id']}，当面说清代价。",
                "immediate": "有人听见了这句话，也记下了你当时站在哪一边。",
                "hook_texts": [f"{hook.get('actor', '街坊')}后来在渡口把这笔人情当面还给你。" for hook in choice.get("hooks") or []],
            })
        return json.dumps({
            "id": scene["id"],
            "title": scene["title"],
            "narration": f"南堤的风吹过{scene['id']}。阿六把船桨放下，说：「先算今天谁来补这块板。」彭枝看着岸上的人，知道船、欠账和孩子的路都要有人亲自接住。",
            "choices": choices,
        }, ensure_ascii=False)
    if "\n结局：" in prompt:
        ending = json.loads(prompt.split("\n结局：", 1)[1])
        return json.dumps({
            "id": ending["id"],
            "title": ending["title"],
            "body": "新桥照常开通。你在南堤留下的，是曾经借出去的手、还清的账和有人愿意向你开口的明天。",
            "epithet": "一个在旧渡口为具体的人留过位置的人",
        }, ensure_ascii=False)
    raise AssertionError("unexpected prompt")


class TestGeneration(unittest.TestCase):
    def test_cli_strict_keeps_draft_and_reports_blockers(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "package"
            proc = subprocess.run(
                [sys.executable, str(ROOT / "production" / "pipeline.py"), "generate", "--extract", str(FIXTURE / "extract.json"), "--out", str(out), "--strict"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertEqual(validate_package(out), [])
            self.assertTrue((Path(temp) / ".package_production" / "quality_report.json").exists())

    def test_local_draft_is_playable_but_marked_for_review(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "package"
            result = generate(out=out, source_path=FIXTURE / "source.txt", title="南堤渡口", source_id="nandi_draft", source_type="original_sample")
            self.assertEqual(validate_package(out), [])
            self.assertGreater(result["quality"]["blockers"], 0)
            self.assertFalse((out / "source.txt").exists())
            self.assertTrue((Path(result["workdir"]) / "quality_report.json").exists())

    def test_third_book_full_run_and_canon(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "package"
            result = generate(out=out, extract_path=FIXTURE / "extract.json", source_path=FIXTURE / "source.txt", source_type="original_sample")
            self.assertEqual(validate_package(out), [])
            self.assertTrue(result["quality"]["issues"])
            first, last = play_to_end(out), play_to_end(out, last=True)
            for session in (first, last):
                self.assertTrue(session.state.finished)
                self.assertTrue(session.state.ending_id)
                self.assertEqual(len(session.state.pending), 0)
                for event in EXTRACT["canon_events"]:
                    self.assertTrue(session.state.flags.get(f"canon:{event['id']}"))
            self.assertNotEqual(first.state.chosen["s_open"], last.state.chosen["s_open"])
            self.assertNotEqual(first.state.stats, last.state.stats)

            scenes_path = out / "scenes.json"
            scenes = json.loads(scenes_path.read_text(encoding="utf-8"))
            scenes[0]["narration"] = (FIXTURE / "source.txt").read_text(encoding="utf-8")[:80]
            scenes_path.write_text(json.dumps(scenes, ensure_ascii=False), encoding="utf-8")
            overlap = review_package(out, source_text=(FIXTURE / "source.txt").read_text(encoding="utf-8"))
            self.assertIn("source_overlap", [issue["code"] for issue in overlap["issues"]])

    def test_resume_after_model_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "package"
            seen = 0

            def flaky(prompt: str, system: str = "") -> str:
                nonlocal seen
                seen += 1
                if seen == 3:
                    raise RuntimeError("temporary model failure")
                return fake_chat(prompt, system)

            config = {"enabled": True, "api_key": "test", "model": "fake"}
            with patch("production.generate_world.load_llm_config", return_value=config), patch("production.generate_world.chat_completion", side_effect=flaky):
                with self.assertRaises(RuntimeError):
                    generate(out=out, source_path=FIXTURE / "source.txt", title=EXTRACT["meta"]["source_title"], source_id="nandi_ferry", source_type="original_sample", llm=True)
            self.assertFalse(out.exists())
            with patch("production.generate_world.load_llm_config", return_value=config), patch("production.generate_world.chat_completion", side_effect=fake_chat) as calls:
                generate(out=out, source_path=FIXTURE / "source.txt", title=EXTRACT["meta"]["source_title"], source_id="nandi_ferry", source_type="original_sample", llm=True, resume=True)
                prompts = [call.args[0] for call in calls.call_args_list]
                self.assertFalse(any("<source>" in prompt or "结构笔记：" in prompt for prompt in prompts))
            self.assertEqual(validate_package(out), [])

    def test_llm_pipeline_resumes_without_repeating_calls(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "package"
            long_source = Path(temp) / "long_source.txt"
            long_source.write_text(((FIXTURE / "source.txt").read_text(encoding="utf-8") + "\n\n") * 55, encoding="utf-8")
            with patch("production.generate_world.load_llm_config", return_value={"enabled": True, "api_key": "test", "model": "fake"}), patch("production.generate_world.chat_completion", side_effect=fake_chat) as calls:
                first = generate(out=out, source_path=long_source, title=EXTRACT["meta"]["source_title"], source_id="nandi_ferry", source_type="original_sample", llm=True)
                first_count = calls.call_count
                self.assertGreater(first_count, 25)
                second = generate(out=out, source_path=long_source, title=EXTRACT["meta"]["source_title"], source_id="nandi_ferry", source_type="original_sample", llm=True, resume=True, force=True)
                self.assertEqual(calls.call_count, first_count)
            self.assertEqual(validate_package(out), [])
            self.assertEqual(first["quality"], second["quality"])
            self.assertEqual(first["quality"]["blockers"], 0)
            self.assertIn("repeated_effect_pattern", [issue["code"] for issue in first["quality"]["issues"]])
            original = scaffold_package(EXTRACT)
            generated = json.loads((out / "scenes.json").read_text(encoding="utf-8"))
            for before, after in zip(original["scenes"], generated):
                self.assertEqual(before["trigger"], after["trigger"])
                self.assertEqual([c["effects"] for c in before["choices"]], [c["effects"] for c in after["choices"]])


if __name__ == "__main__":
    unittest.main()
