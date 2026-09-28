# -*- coding: utf-8 -*-
"""灵活调用模型：创造模式干预后即时改写后续走向。

未启用 API 时用本地模板，保证创造模式可玩。
"""

from __future__ import annotations

import json
from typing import Any

from production.llm_config import load_llm_config, chat_completion


SYSTEM = (
    "你是书中世界导演。玩家开启创造模式做了「大方向」干预，但定数事件不可改写。\n"
    "请输出 JSON，字段：\n"
    "flavor: 80字内中文旁白（像命运侧写，不要说明书腔）\n"
    "beats: 3条后续走向要点（每条≤40字，不改定数，只改处境/关系/代价）\n"
    "warning: 1条「上帝也救不了」的提醒（≤30字）\n"
    "只输出 JSON。"
)


def _offline_flavor(kind: str, note: str) -> dict[str, Any]:
    if kind == "relation":
        flavor = f"谁与谁之间的温度被改写了一格。{note or ''} 不是所有人都察觉，但账本会记下。"
    elif kind == "stat":
        flavor = "命运的水位挪动了一寸。往后每一日，都会多一分余地或紧一分。"
    elif kind == "directive":
        flavor = f"手谕落在纸上：「{note or ''}」。风向会慢慢偏，但写定的事仍会来。"
    elif kind == "attitude":
        flavor = "有人待你的眉眼，被悄悄改了半寸。你自己未必立刻察觉。"
    else:
        flavor = "世界粗线被拨动。细节还要一日日长出来。"
    return {
        "flavor": flavor,
        "beats": [
            "后续可选场景会围绕你的手谕偏斜",
            "关系与代价将重新排队",
            "定数仍在原日等你",
        ],
        "warning": "写定的终局，上帝也只能陪你看清它。",
    }


def rewrite_after_god(
    *,
    kind: str,
    target: str = "",
    note: str = "",
    directive: str = "",
    book_title: str = "",
    turn_label: str = "",
    recent_memory: list[str] | None = None,
) -> dict[str, Any]:
    cfg = load_llm_config()
    prompt = (
        f"书：{book_title}\n此刻：{turn_label}\n"
        f"干预类型：{kind}\n对象：{target}\n"
        f"手谕/说明：{directive or note}\n"
        f"最近痕迹：{'；'.join((recent_memory or [])[-5:])}\n"
        "请按系统要求输出 JSON。"
    )
    if cfg.get("enabled") and cfg.get("api_key"):
        try:
            text = chat_completion(prompt, system=SYSTEM)
            raw = text.strip()
            if raw.startswith("```"):
                raw = raw.strip("`")
                raw = raw.split("\n", 1)[-1]
                raw = raw.rsplit("```", 1)[0]
            data = json.loads(raw)
            return {
                "source": "llm",
                "flavor": str(data.get("flavor") or "")[:300],
                "beats": [str(x)[:80] for x in (data.get("beats") or [])][:5],
                "warning": str(data.get("warning") or "")[:80],
            }
        except Exception as e:  # noqa: BLE001
            out = _offline_flavor(kind, note or directive)
            out["source"] = "offline"
            out["error"] = str(e)[:120]
            return out
    out = _offline_flavor(kind, note or directive)
    out["source"] = "offline"
    return out
