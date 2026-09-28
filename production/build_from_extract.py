#!/usr/bin/env python3
"""从提取结果 + 现成血肉，打包出可玩世界。

用法（示例，针对杏花沟样本）：
  python production/build_from_extract.py

注意：
- 这里用样本的 extract/world_extract.json 作为「制作阶段结构提取」的产物。
- scenes/endings 是基于该结构长出的可玩内容，不是原书情节。
- 换书时：按 PROMPTS.md 重跑提取，再生成新的 scenes/endings，引擎不动。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from production.validate import validate_package  # noqa: E402

SAMPLE = ROOT / "data" / "samples" / "xinghuagou"
EXTRACT = SAMPLE / "extract" / "world_extract.json"
PACKAGE = SAMPLE / "package"


def main() -> int:
    if not EXTRACT.exists():
        print("缺少 extract/world_extract.json")
        return 1

    # 样本路径：package/ 已含 scenes/endings/world。
    # 这里做一次「从提取骨架对照数据包」的检查，并重新写出 meta.source。
    extract = json.loads(EXTRACT.read_text(encoding="utf-8"))
    world_path = PACKAGE / "world.json"
    world = json.loads(world_path.read_text(encoding="utf-8"))

    # 把提取元数据写回数据包，保持可追溯（不含原文）
    world.setdefault("meta", {})
    world["meta"]["extract_source"] = {
        "source_id": extract.get("meta", {}).get("source_id"),
        "source_title": extract.get("meta", {}).get("source_title"),
        "source_type": extract.get("meta", {}).get("source_type"),
        "extraction_note": extract.get("meta", {}).get("extraction_note"),
        "conflict_sources": [
            c.get("id") for c in extract.get("conflict_sources") or []
        ],
        "canon_events": [e.get("id") for e in extract.get("canon_events") or []],
    }
    world["meta"]["play_space_note"] = extract.get("play_space_note", "")

    world_path.write_text(
        json.dumps(world, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    problems = validate_package(PACKAGE)
    if problems:
        print("校验失败：")
        for p in problems:
            print(" -", p)
        return 1

    print(f"✓ 已从提取结构刷新数据包：{PACKAGE}")
    print(f"  - 冲突源: {', '.join(world['meta']['extract_source']['conflict_sources'])}")
    print(f"  - 定数事件: {len(world.get('canon_events') or [])} 个")
    print(f"  - 场景: {len(json.loads((PACKAGE/'scenes.json').read_text(encoding='utf-8')))} 个")
    print(f"  - 结局: {len(json.loads((PACKAGE/'endings.json').read_text(encoding='utf-8')))} 个")
    print()
    print("游玩入口: python play.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
