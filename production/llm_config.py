# -*- coding: utf-8 -*-
"""自定义大模型 API 配置（仅制作阶段使用；游玩可完全离线）。"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from production.secret_store import protect_secret, unprotect_secret

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "data" / "config"
CONFIG_PATH = CONFIG_DIR / "llm.json"

DEFAULT: dict[str, Any] = {
    "enabled": False,
    "base_url": "https://api.openai.com/v1",
    "api_key": "",
    "model": "gpt-4o-mini",
    "image_model": "dall-e-3",
    "temperature": 0.4,
    "timeout": 60,
}


def load_llm_config() -> dict[str, Any]:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            merged = {**DEFAULT, **{k: v for k, v in data.items() if k in DEFAULT and k != "api_key"}}
            if data.get("api_key_protected"):
                merged["api_key"] = unprotect_secret(str(data["api_key_protected"]))
                if "api_key" in data:
                    save_llm_config(merged)
            elif "api_key" in data:
                # 旧版配置在首次读取时原位迁移；失败则不继续使用明文。
                merged["api_key"] = str(data["api_key"] or "")
                save_llm_config(merged)
            return merged
        except json.JSONDecodeError:
            pass
    return dict(DEFAULT)


def save_llm_config(cfg: dict[str, Any]) -> dict[str, Any]:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    merged = {**DEFAULT, **{k: v for k, v in cfg.items() if k in DEFAULT}}
    if merged.get("api_key"):
        api_url(merged, "chat/completions")
        api_key_header(merged)
    saved = {k: v for k, v in merged.items() if k != "api_key"}
    if merged.get("api_key"):
        saved["api_key_protected"] = protect_secret(str(merged["api_key"]))
    temporary = CONFIG_PATH.with_name(CONFIG_PATH.name + ".tmp")
    temporary.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, CONFIG_PATH)
    return merged


def public_llm_config(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    data = cfg if cfg is not None else load_llm_config()
    out = {k: data.get(k, default) for k, default in DEFAULT.items() if k != "api_key"}
    out["api_key_set"] = bool(data.get("api_key"))
    return out


def api_url(cfg: dict[str, Any], endpoint: str) -> str:
    base = str(cfg.get("base_url") or "").rstrip("/")
    parsed = urlsplit(base)
    local = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    if (
        parsed.scheme not in ({"https", "http"} if local else {"https"})
        or not parsed.hostname or parsed.username or parsed.password
        or parsed.query or parsed.fragment
    ):
        raise RuntimeError("API 地址须为 HTTPS；仅本机地址可使用 HTTP，且不能包含账号、查询或片段")
    return base + "/" + endpoint.lstrip("/")


def api_key_header(cfg: dict[str, Any]) -> str:
    key = str(cfg.get("api_key") or "")
    if not key or not key.isascii() or any(not 33 <= ord(char) <= 126 for char in key):
        raise RuntimeError("API Key 格式无效；请重新填写")
    return "Bearer " + key


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def open_api_request(request: urllib.request.Request, timeout: int):
    return urllib.request.build_opener(_NoRedirect).open(request, timeout=timeout)


def chat_completion(prompt: str, system: str = "") -> str:
    """OpenAI 兼容 /chat/completions。仅制作阶段调用。"""
    cfg = load_llm_config()
    if not cfg.get("enabled"):
        raise RuntimeError("未启用自定义 API（设置里打开）")
    if not cfg.get("api_key"):
        raise RuntimeError("未配置 api_key")

    url = api_url(cfg, "chat/completions")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": cfg.get("model") or "gpt-4o-mini",
        "messages": messages,
        "temperature": float(cfg.get("temperature") or 0.4),
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
        with open_api_request(req, timeout=int(cfg.get("timeout") or 60)) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"API 返回 HTTP {e.code}；请检查地址、权限和模型设置") from None
    except Exception as e:  # noqa: BLE001
        raise RuntimeError("API 请求失败；请检查网络与 API 设置") from None

    try:
        return str(body["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError("API 响应格式异常") from None


def test_llm() -> dict[str, Any]:
    """连通性测试。"""
    try:
        chat_completion("回复两个字：可用", system="你是连通性测试助手，简短回复。")
        return {"ok": True}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
