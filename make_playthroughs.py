#!/usr/bin/env python3
"""生成两条有意分叉的完整游玩示例，并写入 docs/PLAYTHROUGH.md 的原始记录。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from engine.models import load_package
from engine.runner import GameRunner
from engine.state import GameState

PKG = ROOT / "data" / "samples" / "xinghuagou" / "package"


def run(prefer: str, out_path: Path) -> GameState:
    package = load_package(PKG)
    player = package.players[0]
    state = GameState.new(package, player)
    lines: list[str] = []
    buffer: list[str] = []

    def out(s: str) -> None:
        lines.append(s)
        buffer.append(s)

    def inp(prompt: str) -> str:
        numbered = []
        for line in reversed(buffer[-40:]):
            stripped = line.strip()
            if not (len(stripped) > 2 and stripped[0].isdigit() and stripped[1] == "."):
                continue
            try:
                num = int(stripped.split(".", 1)[0])
            except ValueError:
                continue
            if num == 0 or "不可" in stripped:
                continue
            numbered.append(num)
        if not numbered:
            val = 1
        else:
            numbered = sorted(numbered)
            val = numbered[0] if prefer == "low" else numbered[-1]
        lines.append(f"{prompt}{val}")
        buffer.append(f"{prompt}{val}")
        return str(val)

    runner = GameRunner(package, state, out=out, inp=inp)
    final = runner.run()
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_path} -> {final.ending_id}")
    return final


def main() -> None:
    runs = ROOT / "runs"
    runs.mkdir(exist_ok=True)
    a = run("low", runs / "playthrough_A_tender.md")
    b = run("high", runs / "playthrough_B_hard.md")

    summary = []
    summary.append("# 两条完整游玩对照\n")
    summary.append("## A 线（偏心软 / 先问妹妹 / 照应李家）\n")
    summary.append(f"- 结局：`{a.ending_id}`")
    summary.append(f"- 钱 {a.stats.get('money')} · 面子 {a.stats.get('face')} · 温度 {a.stats.get('warmth')} · 硬气 {a.stats.get('guts')}")
    summary.append(f"- 小雨 {a.relationships.get('ma_xiaoyu')} · 李建国 {a.relationships.get('li_jianguo')} · 娘 {a.relationships.get('he_xiuying')}")
    summary.append(f"- 定数旗标数：{sum(1 for k in a.flags if str(k).startswith('canon:'))}")
    summary.append(f"- 记忆条数：{len(a.memory)} · 延迟后果队列残留：{len(a.pending)}\n")
    summary.append("## B 线（偏硬气 / 撑场面 / 先顾自己）\n")
    summary.append(f"- 结局：`{b.ending_id}`")
    summary.append(f"- 钱 {b.stats.get('money')} · 面子 {b.stats.get('face')} · 温度 {b.stats.get('warmth')} · 硬气 {b.stats.get('guts')}")
    summary.append(f"- 小雨 {b.relationships.get('ma_xiaoyu')} · 李建国 {b.relationships.get('li_jianguo')} · 娘 {b.relationships.get('he_xiuying')}")
    summary.append(f"- 定数旗标数：{sum(1 for k in b.flags if str(k).startswith('canon:'))}")
    summary.append(f"- 记忆条数：{len(b.memory)} · 延迟后果队列残留：{len(b.pending)}\n")
    summary.append("完整台本见 `runs/playthrough_A_tender.md` 与 `runs/playthrough_B_hard.md`。")
    (ROOT / "docs" / "PLAYTHROUGH.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("wrote docs/PLAYTHROUGH.md")


if __name__ == "__main__":
    main()
