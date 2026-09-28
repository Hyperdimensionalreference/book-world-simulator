# -*- coding: utf-8 -*-
"""制作阶段生图：封面 + 场景氛围图（OpenAI 兼容 /v1/images/generations）。

游玩时不调用。未配置 Key 时生成本地 SVG 占位封面，保证投书流程不中断。
"""

from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "books"

from production.llm_config import api_key_header, api_url, load_llm_config, open_api_request


def _safe(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", name)[:40] or "book"


def book_dir(book_id: str) -> Path:
    d = ASSETS / _safe(book_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def generate_image(prompt: str, out_path: Path, size: str = "1024x1024") -> Path:
    """调用 OpenAI 兼容 images API；失败则写 SVG 占位。"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = load_llm_config()
    key = str(cfg.get("api_key") or "").strip()
    if cfg.get("enabled") and key:
        url = api_url(cfg, "images/generations")
        payload = {
            "model": str(cfg.get("image_model") or cfg.get("model") or "dall-e-3"),
            "prompt": prompt[:1800],
            "n": 1,
            "size": size if size in {"256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"} else "1024x1024",
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": api_key_header(cfg),
            },
            method="POST",
        )
        try:
            with open_api_request(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            b64 = (body.get("data") or [{}])[0].get("b64_json")
            if b64:
                out_path.write_bytes(base64.b64decode(b64))
                return out_path
            url_img = (body.get("data") or [{}])[0].get("url")
            if url_img:
                with urllib.request.urlopen(url_img, timeout=60) as r2:
                    out_path.write_bytes(r2.read())
                return out_path
        except Exception:
            pass

    # 占位 SVG（渐变纸感）
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#e8d5b5"/>
      <stop offset="50%" stop-color="#c4a574"/>
      <stop offset="100%" stop-color="#8f6a4a"/>
    </linearGradient>
  </defs>
  <rect width="1024" height="1024" fill="url(#g)"/>
  <rect x="48" y="48" width="928" height="928" fill="none" stroke="#f7efe4" stroke-width="8" opacity="0.55"/>
  <text x="512" y="500" text-anchor="middle" font-family="serif" font-size="72" fill="#2c2418" opacity="0.75">{_xml_escape(prompt[:8])}</text>
</svg>"""
    # 优先写 .svg，调用方用 webp/jpg 时会再包一层
    svg_path = out_path.with_suffix(".svg")
    svg_path.write_text(svg, encoding="utf-8")
    # 同时写一份假 jpg 路径的 svg 以便统一引用
    out_path.write_text(svg, encoding="utf-8")
    return out_path


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def cover_prompt(title: str, setting: str, scale: str = "") -> str:
    return (
        f"文学书籍封面插画，书名气质：《{title}》。"
        f"场景：{setting[:120]}。"
        "克制的纸本质感，水彩淡彩，东方审美，无文字无水印，构图留白，可做封面主视觉。"
    )


def place_prompt(setting: str, place_name: str, tone: str = "静谧叙事") -> str:
    return (
        f"叙事游戏场景插画：{place_name}。世界观：{setting[:100]}。"
        f"气氛{tone}，水彩淡彩纸质感，无人物面部特写，无文字水印，横构图。"
    )


def generate_book_assets(
    book_id: str,
    title: str,
    setting: str,
    places: list[dict[str, str]] | None = None,
    scale: str = "",
) -> dict[str, Any]:
    """生成封面 + 地点场景图，返回相对路径映射。"""
    d = book_dir(book_id)
    result: dict[str, Any] = {"book_id": book_id, "cover": None, "places": {}}

    cover_path = d / "cover.png"
    generate_image(cover_prompt(title, setting, scale), cover_path, size="1024x1024")
    # 若写出的是 svg 文本，保留 .svg
    if cover_path.exists() and cover_path.read_bytes()[:100].lstrip().startswith(b"<svg"):
        cover_path = cover_path.with_suffix(".svg")
    result["cover"] = f"assets/books/{_safe(book_id)}/{cover_path.name}"

    for p in places or []:
        pid = _safe(str(p.get("id") or p.get("name") or "place"))
        name = str(p.get("name") or pid)
        out = d / f"{pid}.png"
        generate_image(place_prompt(setting, name), out, size="1536x1024")
        if out.exists() and out.read_bytes()[:100].lstrip().startswith(b"<svg"):
            out = out.with_suffix(".svg")
        result["places"][str(p.get("id") or pid)] = (
            f"assets/books/{_safe(book_id)}/{out.name}"
        )

    (d / "assets.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def load_book_assets(book_id: str) -> dict[str, Any]:
    path = ASSETS / _safe(book_id) / "assets.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}
