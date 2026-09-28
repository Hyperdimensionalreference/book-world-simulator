#!/usr/bin/env python3
"""书中世界模拟器 —— 本地游玩入口。

用法：
  python play.py                          # 交互游玩样本《杏花沟》
  python play.py --package data/samples/xinghuagou/package
  python play.py --script runs/sample_a.json
  python play.py --validate
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from engine.models import load_package  # noqa: E402
from engine.runner import GameRunner, run_interactive  # noqa: E402
from engine.state import GameState  # noqa: E402
from production.validate import validate_package  # noqa: E402


DEFAULT_PACKAGE = ROOT / "data" / "samples" / "xinghuagou" / "package"


def cmd_validate(package_dir: Path) -> int:
    problems = validate_package(package_dir)
    if not problems:
        print(f"[OK] 数据包合法：{package_dir}")
        return 0
    print(f"[FAIL] 数据包有问题（{len(problems)}）：{package_dir}")
    for p in problems:
        print(f"  - {p}")
    return 1


def cmd_play(package_dir: Path) -> int:
    print(f"\n加载数据包：{package_dir}\n")
    state = run_interactive(str(package_dir))
    print(f"\n[结局] {state.ending_id}")
    return 0


def cmd_script(package_dir: Path, script_path: Path) -> int:
    script = json.loads(script_path.read_text(encoding="utf-8"))
    choices = script.get("choices") or []
    player_id = script.get("player_id")
    package = load_package(package_dir)
    player = package.players[0]
    if player_id:
        player = next(p for p in package.players if p.id == player_id)
    state = GameState.new(package, player)

    remaining = list(choices)
    transcript: list[str] = []

    def out(s: str) -> None:
        transcript.append(s)
        print(s)

    def inp(prompt: str) -> str:
        val = remaining.pop(0) if remaining else "1"
        line = f"{prompt}{val}"
        transcript.append(line)
        print(line)
        return str(val)

    runner = GameRunner(package, state, out=out, inp=inp)
    final = runner.run()
    out_path = script.get("out")
    if out_path:
        Path(out_path).write_text("\n".join(transcript) + "\n", encoding="utf-8")
        print(f"\n[已写入游玩记录] {out_path}")
    print(f"\n[结局] {final.ending_id}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="书中世界模拟器")
    ap.add_argument(
        "--package",
        default=str(DEFAULT_PACKAGE),
        help="世界数据包目录（含 world.json）",
    )
    ap.add_argument("--validate", action="store_true", help="只做数据包校验")
    ap.add_argument("--script", help="用 JSON 脚本跑一局（自动试玩/测试）")
    args = ap.parse_args()

    package_dir = Path(args.package)
    if not package_dir.is_absolute():
        package_dir = ROOT / package_dir

    if args.validate:
        return cmd_validate(package_dir)
    if args.script:
        script_path = Path(args.script)
        if not script_path.is_absolute():
            script_path = ROOT / script_path
        return cmd_script(package_dir, script_path)
    return cmd_play(package_dir)


if __name__ == "__main__":
    raise SystemExit(main())
