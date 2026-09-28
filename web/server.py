"""书中世界模拟器 · 本地网页服务（仅标准库）。

用法：
  python web/server.py
  python web/server.py --port 8765 --open
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.models import load_package
from engine.session import GameSession, session_from_save, session_to_save
from engine.save_store import (
    delete_save,
    list_saves,
    load_meta,
    read_save,
    save_meta,
    write_save,
)
from engine.achievements import ACHIEVEMENTS, check_achievements
from engine.god_mode import apply_god_intervention, god_limits
from engine.shelf import (
    load_book_session,
    persist_book_session,
    shelf_status,
    book_slot,
)
from production.llm_config import (
    load_llm_config,
    public_llm_config,
    save_llm_config,
    test_llm,
)
from production.image_gen import load_book_assets
from production.god_llm import rewrite_after_god
from production.ingest import draft_extract_from_text, ingest_book

STATIC = ROOT  # 入口 index.html 在项目根目录
DEFAULT_PKG = ROOT / "data" / "samples" / "xinghuagou" / "package"
SAMPLES_ROOT = ROOT / "data" / "samples"
PID_FILE = ROOT / ".web-server.pid"


def list_packages() -> list[dict]:
    out = []
    if not SAMPLES_ROOT.exists():
        return out
    for d in sorted(SAMPLES_ROOT.iterdir()):
        pkg = d / "package"
        if not (pkg / "world.json").exists():
            continue
        try:
            info = load_package(pkg)
        except Exception:
            continue
        mid = str(info.meta.get("id") or d.name)
        assets = load_book_assets(mid)
        out.append(
            {
                "id": mid,
                "dir": d.name,
                "title": info.meta.get("title") or d.name,
                "path": str(pkg),
                "intro": (info.meta.get("intro") or "")[:120],
                "cover": assets.get("cover"),
                "place_art": assets.get("places") or {},
            }
        )
    return out


SESSIONS: dict[str, GameSession] = {}
LOCK = threading.Lock()
_next_id = 1
PKG_BY_ID: dict[str, Path] = {p["id"]: Path(p["path"]) for p in list_packages()}


def _pkg_info(package_dir: Path) -> dict:
    pkg = load_package(package_dir)
    return {
        "meta": pkg.meta,
        "players": [
            {"id": p.id, "name": p.name, "age": p.age, "bio": p.bio} for p in pkg.players
        ],
        "calendar": [
            {"index": t.get("index"), "label": t.get("label"), "note": t.get("note")}
            for t in pkg.calendar.turns
        ],
        "canon_timeline": [
            {"id": e.id, "turn": e.turn, "title": e.title} for e in pkg.canon_events
        ],
    }


class Handler(SimpleHTTPRequestHandler):
    package_dir: Path = DEFAULT_PKG

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        # 安静一些
        if "/api/" in str(args[0] if args else ""):
            return

    def _json(self, data, status: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        raw = self.rfile.read(length)
        try:
            value = json.loads(raw.decode("utf-8"))
            return value if isinstance(value, dict) else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def _local_host(self) -> bool:
        try:
            host = urlparse("//" + (self.headers.get("Host") or ""))
            return host.hostname in {"127.0.0.1", "localhost"} and host.port in {None, self.server.server_port}
        except ValueError:
            return False

    def do_GET(self) -> None:
        if not self._local_host():
            return self._json({"error": "host not allowed"}, 403)
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            return self._api_get(path)
        # The project root also contains source books, saves and API keys.
        # Serve only the page and image assets needed by the browser.
        decoded = unquote(path)
        if decoded in ("/", "/index.html", "/style.css", "/app.js"):
            return super().do_GET()
        if decoded.startswith("/assets/"):
            asset_root = (ROOT / "assets").resolve()
            target = (ROOT / decoded.lstrip("/")).resolve()
            if target.is_relative_to(asset_root) and target.is_file() and target.suffix.lower() in {
                ".png", ".jpg", ".jpeg", ".webp", ".svg"
            }:
                return super().do_GET()
        self.send_error(404, "not found")

    def do_POST(self) -> None:
        if not self._local_host():
            return self._json({"error": "host not allowed"}, 403)
        if self.headers.get("Sec-Fetch-Site") not in (None, "same-origin", "none"):
            return self._json({"error": "cross-site request not allowed"}, 403)
        origin = self.headers.get("Origin")
        if origin:
            parsed = urlparse(origin)
            try:
                allowed = parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"} and parsed.port == self.server.server_port
            except ValueError:
                allowed = False
            if not allowed:
                return self._json({"error": "origin not allowed"}, 403)
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            if self.headers.get_content_type() != "application/json":
                return self._json({"error": "JSON content type required"}, 415)
            try:
                size = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                return self._json({"error": "invalid content length"}, 400)
            if size < 0 or size > 20 * 1024 * 1024:
                return self._json({"error": "request too large"}, 413)
            return self._api_post(path, self._read_body())
        self._json({"error": "not found"}, 404)

    def do_HEAD(self) -> None:
        self.send_error(405, "method not allowed")

    def _api_get(self, path: str) -> None:
        if path == "/api/info":
            return self._json(
                {
                    "books": list_packages(),
                    "default": "xinghuagou",
                    "meta": _pkg_info(self.package_dir).get("meta"),
                }
            )
        if path == "/api/books":
            return self._json({"books": list_packages()})
        if path == "/api/saves":
            return self._json({"saves": list_saves(), "meta": load_meta()})
        if path == "/api/achievements":
            return self._json({"all": ACHIEVEMENTS, "meta": load_meta()})
        if path == "/api/llm_config":
            return self._json({"config": public_llm_config()})
        if path == "/api/shelf":
            ids = [p["id"] for p in list_packages()]
            return self._json({"shelf": shelf_status(ids), "books": list_packages()})
        if path == "/api/god_limits":
            return self._json(god_limits())
        if path.startswith("/api/save/"):
            slot = path.rsplit("/", 1)[-1]
            data = read_save(slot)
            if not data:
                return self._json({"error": "save not found"}, 404)
            return self._json(data)
        if path == "/api/snapshot":
            q = urlparse(self.path).query
            sid = ""
            for part in q.split("&"):
                if part.startswith("sid="):
                    sid = part.split("=", 1)[1]
            with LOCK:
                sess = SESSIONS.get(sid)
            if not sess:
                return self._json({"error": "no session"}, 404)
            return self._json(sess.snapshot())
        self._json({"error": "not found"}, 404)

    def _api_post(self, path: str, body: dict) -> None:
        global _next_id, PKG_BY_ID
        try:
            if path == "/api/new_game":
                player_id = body.get("player_id")
                book = str(body.get("book") or "")
                pkg_dir = PKG_BY_ID.get(book) or self.package_dir
                with LOCK:
                    sess = GameSession(pkg_dir, player_id=player_id)
                    sid = f"s{_next_id}"
                    _next_id += 1
                    SESSIONS[sid] = sess
                snap = sess.snapshot()
                snap["sid"] = sid
                snap["book"] = book or "default"
                return self._json(snap)
            if path == "/api/choose":
                sid = str(body.get("sid") or "")
                with LOCK:
                    sess = SESSIONS.get(sid)
                if not sess:
                    return self._json({"error": "no session"}, 404)
                snap = sess.choose(
                    choice_id=body.get("choice_id"),
                    scene_id=body.get("scene_id"),
                )
                snap["sid"] = sid
                # 自动写入该书的 book_ 槽，切换书也能接上
                try:
                    pid = str(sess.package.meta.get("id") or "world")
                    persist_book_session(pid, session_to_save(sess))
                except Exception:  # noqa: BLE001
                    pass
                return self._json(snap)
            if path == "/api/ingest":
                title = str(body.get("title") or "").strip()
                text = str(body.get("text") or "")
                extract = body.get("extract")
                mode = str(body.get("mode") or "auto")
                if mode == "extract" and not extract:
                    return self._json({"error": "extract 模式需要 extract 字段"}, 400)
                if mode == "draft":
                    if not text.strip():
                        return self._json({"error": "请粘贴或上传正文"}, 400)
                    draft = draft_extract_from_text(title, text)
                    return self._json({"ok": True, "draft": draft})
                try:
                    result = ingest_book(title=title, text=text, extract=extract, llm=body.get("llm") is True)
                except ValueError as error:
                    return self._json({"error": str(error)}, 400)
                # 刷新书目
                PKG_BY_ID = {p["id"]: Path(p["path"]) for p in list_packages()}
                meta = load_meta()
                meta["ingested"] = True
                if result.get("id"):
                    books = set(meta.get("books") or [])
                    books.add(result["id"])
                    meta["books"] = sorted(books)
                save_meta(meta)
                return self._json({"ok": True, **result, "books": list_packages()})
            if path == "/api/save_write":
                sid = str(body.get("sid") or "")
                slot = str(body.get("slot") or "auto")
                auto = bool(body.get("auto", False))
                with LOCK:
                    sess = SESSIONS.get(sid)
                if not sess:
                    return self._json({"error": "no session"}, 404)
                payload = session_to_save(sess)
                used = write_save(slot, payload, auto=auto)
                meta = load_meta()
                if sess.state.ending_id:
                    endings = set(meta.get("endings") or [])
                    endings.add(sess.state.ending_id)
                    meta["endings"] = sorted(endings)
                if sess.package.meta.get("id"):
                    books = set(meta.get("books") or [])
                    books.add(str(sess.package.meta.get("id")))
                    meta["books"] = sorted(books)
                newly = check_achievements(
                    sess.state, set(meta.get("unlocked") or []), meta
                )
                if newly:
                    meta["unlocked"] = sorted(
                        set(meta.get("unlocked") or []) | {a["id"] for a in newly}
                    )
                save_meta(meta)
                return self._json(
                    {
                        "ok": True,
                        "slot": used,
                        "saves": list_saves(),
                        "new_achievements": newly,
                        "meta": meta,
                    }
                )
            if path == "/api/save_load":
                slot = str(body.get("slot") or "")
                data = read_save(slot)
                if not data:
                    return self._json({"error": "存档不存在"}, 404)
                pkg_id = (data.get("state") or {}).get("package_id") or data.get("package_id")
                pkg_dir = PKG_BY_ID.get(str(pkg_id))
                if not pkg_dir:
                    for p in list_packages():
                        if p["id"] == pkg_id:
                            pkg_dir = Path(p["path"])
                            break
                if not pkg_dir:
                    return self._json({"error": "找不到对应世界包，可能已删除"}, 404)
                try:
                    sess = session_from_save(data, str(pkg_dir))
                except Exception as e:  # noqa: BLE001
                    return self._json({"error": f"读档失败：{e}"}, 400)
                with LOCK:
                    sid = f"s{_next_id}"
                    _next_id += 1
                    SESSIONS[sid] = sess
                snap = sess.snapshot()
                snap["sid"] = sid
                snap["restored_slot"] = slot
                snap["book"] = str(pkg_id)
                return self._json(snap)
            if path == "/api/save_delete":
                slot = str(body.get("slot") or "")
                ok = delete_save(slot)
                return self._json({"ok": ok, "saves": list_saves()})
            if path == "/api/game_meta":
                meta = load_meta()
                sid = str(body.get("sid") or "")
                newly = []
                with LOCK:
                    sess = SESSIONS.get(sid)
                if sess:
                    newly = check_achievements(
                        sess.state, set(meta.get("unlocked") or []), meta
                    )
                    changed = False
                    if newly:
                        meta["unlocked"] = sorted(
                            set(meta.get("unlocked") or []) | {a["id"] for a in newly}
                        )
                        changed = True
                    if sess.state.ending_id:
                        endings = set(meta.get("endings") or [])
                        if sess.state.ending_id not in endings:
                            endings.add(sess.state.ending_id)
                            meta["endings"] = sorted(endings)
                            changed = True
                    if changed:
                        save_meta(meta)
                return self._json({"meta": meta, "all": ACHIEVEMENTS, "new": newly})
            if path == "/api/meta_reset":
                meta = load_meta()
                meta["unlocked"] = []
                meta["endings"] = []
                meta["books"] = []
                meta["ingested"] = False
                save_meta(meta)
                return self._json({"ok": True, "meta": meta})
            if path == "/api/llm_config_save":
                # 只更新传入字段；api_key 空则保留原 key
                cur = load_llm_config()
                for k in ("enabled", "base_url", "model", "image_model", "temperature", "timeout"):
                    if k in body:
                        cur[k] = body[k]
                if body.get("clear_api_key") is True:
                    cur["api_key"] = ""
                elif str(body.get("api_key") or "").strip():
                    cur["api_key"] = str(body["api_key"]).strip()
                try:
                    saved = save_llm_config(cur)
                except RuntimeError as error:
                    return self._json({"error": str(error)}, 400)
                return self._json({"ok": True, "config": public_llm_config(saved)})
            if path == "/api/llm_test":
                return self._json(test_llm())
            if path == "/api/shelf_save":
                # 保存当前会话到该书的 book_ 槽
                sid = str(body.get("sid") or "")
                with LOCK:
                    sess = SESSIONS.get(sid)
                if not sess:
                    return self._json({"error": "no session"}, 404)
                pid = str(sess.package.meta.get("id") or "world")
                slot = persist_book_session(pid, session_to_save(sess))
                return self._json({"ok": True, "slot": slot, "shelf": shelf_status([p["id"] for p in list_packages()])})
            if path == "/api/shelf_load":
                book = str(body.get("book") or "")
                pkg_dir = PKG_BY_ID.get(book)
                if not pkg_dir:
                    for p in list_packages():
                        if p["id"] == book or p.get("dir") == book:
                            pkg_dir = Path(p["path"])
                            book = p["id"]
                            break
                if not pkg_dir:
                    return self._json({"error": "未知世界"}, 404)
                data = load_book_session(book)
                if data:
                    try:
                        sess = session_from_save(data, str(pkg_dir))
                    except Exception as e:  # noqa: BLE001
                        return self._json({"error": f"读档失败：{e}"}, 400)
                else:
                    sess = GameSession(pkg_dir)
                with LOCK:
                    sid = f"s{_next_id}"
                    _next_id += 1
                    SESSIONS[sid] = sess
                snap = sess.snapshot()
                snap["sid"] = sid
                snap["book"] = book
                snap["resumed"] = bool(data)
                return self._json(snap)
            if path == "/api/god_limits":
                return self._json(god_limits())
            if path == "/api/god_apply":
                sid = str(body.get("sid") or "")
                with LOCK:
                    sess = SESSIONS.get(sid)
                if not sess:
                    return self._json({"error": "no session"}, 404)
                result = apply_god_intervention(
                    sess.package,
                    sess.state,
                    kind=str(body.get("kind") or ""),
                    target=str(body.get("target") or ""),
                    stat=str(body.get("stat") or ""),
                    delta=int(body.get("delta") or 0),
                    note=str(body.get("note") or ""),
                    directive=str(body.get("directive") or ""),
                )
                rewrite = None
                if result.get("ok"):
                    rewrite = rewrite_after_god(
                        kind=str(body.get("kind") or ""),
                        target=str(body.get("target") or ""),
                        note=str(body.get("note") or ""),
                        directive=str(body.get("directive") or ""),
                        book_title=str(sess.package.meta.get("title") or ""),
                        turn_label=sess.package.turn_label(sess.state.turn),
                        recent_memory=[m.text for m in sess.state.memory[-8:]],
                    )
                    # 写入记忆与旗标，后续走向偏斜
                    sess.state.add_memory(
                        f"命运侧写：{rewrite.get('flavor', '')[:120]}",
                        actor="god",
                        tags=["god", "rewrite", rewrite.get("source", "")],
                    )
                    for i, beat in enumerate(rewrite.get("beats") or []):
                        sess.state.flags[f"god_beat_{i}"] = beat
                    if rewrite.get("warning"):
                        sess.state.flags["god_warning"] = rewrite["warning"]
                    try:
                        persist_book_session(
                            str(sess.package.meta.get("id") or "world"),
                            session_to_save(sess),
                        )
                    except Exception:  # noqa: BLE001
                        pass
                snap = sess.snapshot()
                snap["sid"] = sid
                return self._json({"result": result, "rewrite": rewrite, "snapshot": snap, "sid": sid})
            self._json({"error": "not found"}, 404)
        except Exception as error:  # noqa: BLE001 — 响应和服务日志均不回显第三方错误内容
            print(f"API error: {type(error).__name__}", file=sys.stderr)
            self._json({"error": "操作失败；请检查输入与本机配置"}, 500)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--open", action="store_true", help="启动后打开浏览器")
    ap.add_argument("--package", default=str(DEFAULT_PKG))
    args = ap.parse_args()

    Handler.package_dir = Path(args.package)
    if not Handler.package_dir.is_absolute():
        Handler.package_dir = ROOT / Handler.package_dir

    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    try:
        PID_FILE.write_text(str(os.getpid()), encoding="ascii")
    except OSError:
        print("警告：无法写入服务进程标识，停止脚本可能无法使用。")
    url = f"http://127.0.0.1:{args.port}/"
    print(f"书中世界模拟器 · 杏花沟")
    print(f"  本地地址: {url}")
    print(f"  数据包:   {Handler.package_dir}")
    print(f"  按 Ctrl+C 停止")

    if args.open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        httpd.server_close()
        try:
            if PID_FILE.read_text(encoding="ascii").strip() == str(os.getpid()):
                PID_FILE.unlink()
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
