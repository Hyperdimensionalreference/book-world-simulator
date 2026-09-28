# -*- coding: utf-8 -*-
"""多策略试玩：检查经济曲线、结局分叉、延迟回响。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from engine.session import GameSession


def play(prefer: str, name: str):
    s = GameSession(ROOT / "data" / "samples" / "xinghuagou" / "package")
    snaps = []
    steps = 0
    money_path = []
    while steps < 50:
        steps += 1
        snap = s.snapshot()
        money_path.append(snap["stats"][0]["value"])
        if snap.get("finished"):
            break
        if snap.get("scene"):
            avail = [c for c in snap["scene"]["choices"] if c.get("available")]
            if not avail:
                break
            pick = avail[0] if prefer == "low" else avail[-1]
            snap = s.choose(pick["id"], snap["scene"]["id"])
        else:
            opens = snap.get("open_scenes") or []
            if not opens:
                snap = s.choose("rest")
            else:
                pick = opens[0] if prefer == "low" else opens[-1]
                snap = s.choose(pick["id"])
    st = s.state
    stats = {k: st.get_stat(k) for k in ["money", "grain", "face", "guts", "warmth", "health", "craft", "favor_out", "favor_in"]}
    print(f"\n== {name} ==")
    print("ending:", st.ending_id)
    print("stats:", stats)
    print("rel:", {k: v for k, v in sorted(st.relationships.items(), key=lambda x: -x[1])[:6]})
    print("chosen:", len(st.chosen), "mem:", len(st.memory), "pending left:", len(st.pending))
    print("money path:", money_path[::2])
    print("flags sample:", [k for k in st.flags if k.startswith("helped") or k.startswith("learned") or k.startswith("refused") or k.startswith("lent") or k.startswith("backed")][:12])
    return st


play("low", "A 心软/先顾人")
play("high", "B 硬气/先顾己")
play("low", "A2 再跑心软看稳定性")
