# -*- coding: utf-8 -*-
"""投书 → 可玩世界 流水线（制作阶段；游玩时零模型）。

用法：
  python production/pipeline.py validate-extract data/samples/xxx/extract/world_extract.json
  python production/pipeline.py scaffold data/samples/xxx/extract/world_extract.json data/samples/xxx/package
  python production/pipeline.py check data/samples/xxx/package
  python production/pipeline.py all data/samples/xxx/extract/world_extract.json data/samples/xxx/package
  python production/pipeline.py generate --extract data/samples/xxx/extract/world_extract.json --out data/samples/xxx/package --llm
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from production.scaffold import validate_extract, write_package
from production.validate import validate_package


def cmd_validate_extract(path: Path) -> int:
    extract = json.loads(path.read_text(encoding="utf-8"))
    errs = validate_extract(extract)
    if errs:
        print("EXTRACT FAIL")
        for e in errs:
            print(" -", e)
        return 1
    print("EXTRACT OK", path)
    return 0


def cmd_scaffold(src: Path, dst: Path) -> int:
    try:
        out = write_package(src, dst)
    except ValueError as e:
        print(e)
        return 1
    print("SCAFFOLD OK", out)
    return 0


def cmd_check(pkg: Path) -> int:
    problems = validate_package(pkg)
    if problems:
        print("PACKAGE FAIL")
        for p in problems:
            print(" -", p)
        return 1
    print("PACKAGE OK", pkg)
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    op = sys.argv[1]
    if op == "validate-extract":
        return cmd_validate_extract(Path(sys.argv[2]))
    if op == "scaffold":
        return cmd_scaffold(Path(sys.argv[2]), Path(sys.argv[3]))
    if op == "check":
        return cmd_check(Path(sys.argv[2]))
    if op == "all":
        src, dst = Path(sys.argv[2]), Path(sys.argv[3])
        if cmd_validate_extract(src) != 0:
            return 1
        if cmd_scaffold(src, dst) != 0:
            return 1
        return cmd_check(dst)
    if op == "generate":
        from production.generate_world import main as generate_main

        return generate_main(sys.argv[2:])
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
