# -*- coding: utf-8 -*-
"""投书入口后端：原文/提取 → 新的数据包（制作阶段，可离线启发式 + 人工修订）。"""

from __future__ import annotations

import json
import re
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "data" / "samples"

from production.scaffold import validate_extract
from production.image_gen import generate_book_assets


def _slug(s: str, fallback: str = "book") -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()
    return (s[:24] or fallback) + f"_{int(time.time()) % 100000}"


def draft_extract_from_text(title: str, text: str) -> dict[str, Any]:
    """从原文启发式起草 extract（保底可编辑，不冒充精读）。"""
    # 中文/英文人名候选：引号内、高频二字/三字称呼
    quoted = re.findall(r"[「『“\"]([^」』”\"]{2,12})[」』”\"]", text)
    # 常见称谓/名字模式
    names = re.findall(r"([一-龥]{2,3})(?=说|道|问|答|笑|哭|走|来|去)", text)
    from collections import Counter

    freq = Counter(n for n in names if n not in {"一个", "我们", "你们", "他们", "什么", "怎么", "这个", "那个", "自己"})
    top = [n for n, _ in freq.most_common(8)]
    if not top:
        top = ["主角", "配角甲", "配角乙", "长辈", "邻里"]

    # 章节/段落切分
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chapters = re.findall(r"(第[一二三四五六七八九十百零\d]+[章节回]|Chapter\s+\d+)", text)

    n_canon = max(4, min(8, 4 + len(chapters) // 4))
    n_conf = max(4, min(8, 5 + len(paras) // 80))

    canons = []
    for i in range(n_canon):
        turn = 2 + i * 2
        canons.append(
            {
                "id": f"canon_{i+1}",
                "turn": turn,
                "title": f"书中写定之事（待命名）{i+1}",
                "description": f"请依据原文第{i+1}段关键节点填写：时间、地点、人物、不可改写的结果。",
                "foreshadow": [
                    f"前置线索 A（流言/物价/人际）— 对应第{i+1}件定数",
                    f"前置线索 B（消失/来信/反常）— 对应第{i+1}件定数",
                ],
            }
        )

    conflicts = []
    templates = [
        ("material", "资源与生计", "钱粮/住处/土地", "少一分就紧一分"),
        ("family_face", "家里与面子", "家人期望与体面", "让人看扁还是出血"),
        ("social_debt", "人情债", "欠与被欠", "还法决定名声"),
        ("exit_or_stay", "离开或留下", "去远方还是守着", "两头都疼"),
        ("reputation", "名声与闲话", "别人怎么传你", "坏了不好修"),
        ("care_debt", "照应与代价", "病痛、老小、托付", "时间只有一份"),
    ]
    for i in range(n_conf):
        t = templates[i % len(templates)]
        conflicts.append(
            {
                "id": f"conf_{i+1}",
                "name": t[1] + f"（待命名{i+1}）",
                "type": t[0],
                "description": t[2] + "。请对照原文补具体人物与事件。",
                "stakes": t[3],
            }
        )

    characters = []
    roles = ["player", "family", "kin", "neighbor", "authority", "other", "other", "other"]
    names = list(top[:8])
    while len(names) < 5:
        names.append(f"人物{len(names)+1}")
    for i, name in enumerate(names[:8]):
        characters.append(
            {
                "id": f"ch_{i+1}",
                "name": name,
                "role": roles[min(i, len(roles) - 1)],
                "wants": "（待填）这个人最想要什么",
                "blocks": "（待填）谁或什么挡着他",
                "costs": "（待填）他要付什么代价",
                "speech_style": "（待填）说话像谁：短/长/官话/土话/口癖",
                "speech_examples": [f"「……{name}的口吻……」"],
            }
        )

    player = characters[0] if characters else {}
    player_id = player.get("id", "ch_1")

    return {
        "meta": {
            "source_id": _slug(title, "book"),
            "source_title": title or "未命名书中世界",
            "source_type": "user_upload",
            "extraction_note": "由投书入口启发式起草，请人工修订 wants/blocks/costs/定数描述后再用于正式制作。",
            "schema_version": "1.0",
        },
        "world_frame": {
            "scale": "other",
            "setting": f"来自《{title or '未命名'}》的可玩空间。原文约 {len(text)} 字，段落 {len(paras)}。请补时代与具体场所。",
            "time_unit": "章节/日",
            "power_map": "（待填）谁说了算，消息怎么走",
            "threat_style": "日常压力：资源、人情、名声、去留",
        },
        "conflict_sources": conflicts,
        "characters": characters,
        "canon_events": canons,
        "player_suggestions": [
            {
                "id": player_id,
                "name": player.get("name", "无名者"),
                "age": 28,
                "bio": "你扮演书中的普通人，不是被写死的主角。空白处才是你的空间。",
                "wants": player.get("wants", ""),
                "blocks": player.get("blocks", ""),
                "start_relationships": {
                    c["id"]: 12 for c in characters if c["id"] != player_id
                },
            }
        ],
        "play_space_note": "小人物可玩空间：在写定的岁月里选择处境、关系、代价与成为谁。",
        "avoid": ["复述原文段落", "改写定数", "拯救世界的爽文结构"],
    }


def ingest_book(
    title: str,
    text: str = "",
    extract: dict[str, Any] | None = None,
    book_id: str | None = None,
    llm: bool = False,
) -> dict[str, Any]:
    """网页投书 → 制作流水线；正文仅写入自动清理的临时文件。"""
    from production.generate_world import generate  # 避免与 draft_extract_from_text 循环导入

    warnings: list[str] = []
    if extract is None:
        if not text.strip():
            raise ValueError("需要原文文本或 extract JSON")
        extract = draft_extract_from_text(title, text)
        warnings.append("extract 为启发式起草，建议在编辑器里修订人物欲望与定数描述后再正式使用")
    else:
        extract = dict(extract)
        extract["meta"] = dict(extract.get("meta") or {})
        if title:
            extract["meta"]["source_title"] = title

    errs = validate_extract(extract)
    if errs:
        raise ValueError("extract 不完整：\n" + "\n".join(f"· {e}" for e in errs))

    bid = book_id or extract.get("meta", {}).get("source_id") or _slug(title)
    if not isinstance(bid, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{2,39}", bid):
        raise ValueError("source_id 须为 3–40 位英文字母、数字或下划线，且以字母开头")
    extract["meta"]["source_id"] = bid
    out_dir = SAMPLES / bid / "package"
    if any((out_dir / f"{name}.json").exists() for name in ("world", "scenes", "endings")):
        raise ValueError(f"同名世界已存在：{bid}；请修改 extract.meta.source_id 后重试，不会覆盖现有数据包")

    # 检查点保留在书的受控工作目录；模型失败后以同一份结构重试即可续做。
    workdir = SAMPLES / bid / ".package_production"
    with tempfile.TemporaryDirectory(prefix="book_ingest_") as temp:
        temp_root = Path(temp)
        extract_path = temp_root / "extract.json"
        extract_path.write_text(json.dumps(extract, ensure_ascii=False, indent=2), encoding="utf-8")
        source_path = None
        if text.strip():
            source_path = temp_root / "source.txt"
            source_path.write_text(text, encoding="utf-8")
        result = generate(
            out=out_dir,
            extract_path=extract_path,
            source_path=source_path,
            source_type=str(extract["meta"].get("source_type") or "user_upload"),
            llm=llm,
            workdir=workdir,
            resume=(workdir / "manifest.json").exists(),
        )
    quality = result["quality"]
    warnings.append(
        f"内容机检：{quality['blockers']} 个阻断项、{quality['warnings']} 个提醒；仍需逐幕人工复核"
    )

    # 自动配图：封面 + 地点氛围图（有 API 用模型，无则本地占位，不阻断流程）
    try:
        world = json.loads((out_dir / "world.json").read_text(encoding="utf-8"))
        setting = str((extract.get("world_frame") or {}).get("setting") or title or "书中世界")
        scale = str((extract.get("world_frame") or {}).get("scale") or "")
        places = [
            {"id": p.get("id"), "name": p.get("name")}
            for p in (world.get("places") or [])[:8]
        ]
        assets = generate_book_assets(bid, title or bid, setting, places=places, scale=scale)
        warnings.append(
            "已生成封面与场景图"
            + ("（自定义 API）" if assets.get("cover") and "png" in str(assets.get("cover")) else "（本地占位或已生成）")
        )
    except Exception as e:  # noqa: BLE001
        warnings.append(f"配图未完成：{e}")

    return {
        "id": bid,
        "title": extract["meta"].get("source_title") or title,
        "package_path": str(out_dir),
        "workdir": str(workdir),
        "mode": result["mode"],
        "quality": quality,
        "warnings": warnings,
    }
