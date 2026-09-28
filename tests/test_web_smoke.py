"""HTTP smoke tests for the local browser workflow."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine import save_store  # noqa: E402
from production import image_gen, ingest, llm_config  # noqa: E402
from web import server  # noqa: E402


class TestWebWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        base = Path(cls.temp.name)
        samples = base / "samples"
        for name in ("xinghuagou", "tongzilou"):
            shutil.copytree(ROOT / "data" / "samples" / name / "package", samples / name / "package")
        cls.originals = {
            "samples": server.SAMPLES_ROOT,
            "packages": server.PKG_BY_ID,
            "package_dir": server.Handler.package_dir,
            "saves": save_store.SAVES,
            "meta": save_store.META_PATH,
            "ingest": ingest.SAMPLES,
            "assets": image_gen.ASSETS,
            "config_dir": llm_config.CONFIG_DIR,
            "config_path": llm_config.CONFIG_PATH,
        }
        server.SAMPLES_ROOT = samples
        server.Handler.package_dir = samples / "xinghuagou" / "package"
        server.PKG_BY_ID = {p["id"]: Path(p["path"]) for p in server.list_packages()}
        server.SESSIONS.clear()
        save_store.SAVES = base / "saves"
        save_store.META_PATH = save_store.SAVES / "_meta.json"
        ingest.SAMPLES = samples
        image_gen.ASSETS = base / "assets"
        llm_config.CONFIG_DIR = base / "config"
        llm_config.CONFIG_PATH = llm_config.CONFIG_DIR / "llm.json"
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base_url = f"http://127.0.0.1:{cls.httpd.server_port}"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join()
        server.SAMPLES_ROOT = cls.originals["samples"]
        server.PKG_BY_ID = cls.originals["packages"]
        server.Handler.package_dir = cls.originals["package_dir"]
        save_store.SAVES = cls.originals["saves"]
        save_store.META_PATH = cls.originals["meta"]
        ingest.SAMPLES = cls.originals["ingest"]
        image_gen.ASSETS = cls.originals["assets"]
        llm_config.CONFIG_DIR = cls.originals["config_dir"]
        llm_config.CONFIG_PATH = cls.originals["config_path"]
        cls.temp.cleanup()

    def request(self, path: str, body: dict | None = None, origin: str | None = None, extra_headers: dict | None = None):
        headers = dict(extra_headers or {})
        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if origin:
            headers["Origin"] = origin
        req = Request(self.base_url + path, data=data, headers=headers)
        try:
            with urlopen(req, timeout=10) as resp:
                raw = resp.read()
                return resp.status, json.loads(raw) if path.startswith("/api/") else raw
        except HTTPError as err:
            return err.code, err.read()

    def test_static_files_are_allowlisted(self) -> None:
        required = ("/", "/index.html", "/style.css", "/app.js")
        for path in required:
            self.assertEqual(self.request(path)[0], 200, path)
        # Scene art is optional: it ships only when its licence allows publication.
        # When present it must be served; when absent the app falls back in-browser.
        optional_art = "/assets/scenes/home.jpg"
        if (ROOT / "assets" / "scenes" / "home.jpg").is_file():
            self.assertEqual(self.request(optional_art)[0], 200, optional_art)
        else:
            self.assertEqual(self.request(optional_art)[0], 404, optional_art)
            self.skipTest("optional scene art not published in this checkout")
        for path in ("/data/config/llm.json", "/HANDOFF.md", "/data/saves/_meta.json", "/assets/%2e%2e/data/config/llm.json"):
            self.assertEqual(self.request(path)[0], 404, path)
        self.assertEqual(self.request("/api/meta_reset", {}, "https://other.example")[0], 403)
        self.assertEqual(self.request("/api/llm_config", extra_headers={"Host": "attacker.example"})[0], 403)
        self.assertEqual(self.request("/api/llm_test", {}, extra_headers={"Sec-Fetch-Site": "cross-site"})[0], 403)
        plain = Request(self.base_url + "/api/llm_test", data=b"{}", headers={"Content-Type": "text/plain"})
        with self.assertRaises(HTTPError) as failure:
            urlopen(plain, timeout=10)
        self.assertEqual(failure.exception.code, 415)
        # setUpClass redirects the API configuration into this disposable test directory.
        self.assertTrue(llm_config.CONFIG_PATH.is_relative_to(Path(self.temp.name)))
        _, cleared = self.request("/api/llm_config_save", {"clear_api_key": True})
        self.assertFalse(cleared["config"]["api_key_set"])
        self.assertNotIn("api_key", cleared["config"])

    def test_save_load_shelf_and_god_mode(self) -> None:
        _, snap = self.request("/api/new_game", {"book": "xinghuagou"})
        sid = snap["sid"]
        if snap["phase"] == "choose_scene":
            _, snap = self.request("/api/choose", {"sid": sid, "choice_id": snap["open_scenes"][0]["id"]})
        self.assertEqual(snap["phase"], "choose_choice")
        scene_id = snap["scene"]["id"]
        self.assertEqual(self.request("/api/save_write", {"sid": sid, "slot": "smoke"})[0], 200)
        legacy_path = save_store.SAVES / "slot_legacy.json"
        legacy = json.loads((save_store.SAVES / "slot_smoke.json").read_text(encoding="utf-8"))
        legacy.pop("current_scene_id", None)
        legacy_path.write_text(json.dumps(legacy, ensure_ascii=False), encoding="utf-8")
        _, old_save = self.request("/api/save_load", {"slot": "legacy"})
        self.assertEqual(old_save["scene"]["id"], scene_id)
        _, loaded = self.request("/api/save_load", {"slot": "smoke"})
        self.assertEqual(loaded["book"], "xinghuagou")
        self.assertEqual(loaded["scene"]["id"], scene_id)
        choice = next(c for c in loaded["scene"]["choices"] if c["available"])
        _, after = self.request("/api/choose", {"sid": loaded["sid"], "choice_id": choice["id"], "scene_id": scene_id})
        self.assertNotEqual(after["scene"]["id"] if after["scene"] else None, scene_id)
        self.assertEqual(after["phase"], "choose_scene")
        self.request("/api/save_write", {"sid": loaded["sid"], "slot": "smoke_after"})
        _, resumed_turn = self.request("/api/save_load", {"slot": "smoke_after"})
        self.assertEqual(resumed_turn["phase"], "choose_scene")
        self.assertIsNone(resumed_turn["scene"])
        self.assertEqual(resumed_turn["turn"], after["turn"])
        self.assertEqual(self.request("/api/game_meta", {"sid": resumed_turn["sid"]})[0], 200)
        _, god = self.request("/api/god_apply", {"sid": loaded["sid"], "kind": "relation", "target": after["relationships"][0]["id"], "delta": 5})
        self.assertTrue(god["result"]["ok"])
        _, blocked = self.request("/api/god_apply", {"sid": loaded["sid"], "kind": "canon"})
        self.assertFalse(blocked["result"]["ok"])
        self.request("/api/shelf_save", {"sid": loaded["sid"]})
        _, other = self.request("/api/shelf_load", {"book": "tongzi_low"})
        self.assertEqual(other["book"], "tongzi_low")
        _, resumed = self.request("/api/shelf_load", {"book": "xinghuagou"})
        self.assertTrue(resumed["resumed"])
        self.assertEqual(resumed["turn"], after["turn"])
        self.assertEqual(self.request("/api/achievements")[0], 200)

    def test_ingest_without_api_key(self) -> None:
        source = "老周说今日要搬家。\n\n小李问明日还能回来吗。"
        _, draft = self.request("/api/ingest", {"mode": "draft", "title": "烟火街", "text": source})
        self.assertTrue(draft["ok"])
        payload = {"mode": "extract", "title": "烟火街", "text": source, "extract": draft["draft"]}
        _, built = self.request("/api/ingest", payload)
        self.assertTrue(built["ok"])
        self.assertEqual(built["mode"], "local")
        self.assertGreater(built["quality"]["blockers"], 0)
        self.assertTrue((Path(built["workdir"]) / "quality_report.json").exists())
        self.assertFalse((server.SAMPLES_ROOT / built["id"] / "source" / "book.txt").exists())
        self.assertIn(built["id"], [b["id"] for b in self.request("/api/books")[1]["books"]])
        self.assertTrue((image_gen.ASSETS / built["id"] / "cover.svg").exists())
        self.assertEqual(self.request("/api/ingest", payload)[0], 400)

        llm_draft = dict(draft["draft"])
        llm_draft["meta"] = {**llm_draft["meta"], "source_id": "smoke_llm_draft"}
        self.assertEqual(self.request("/api/ingest", {"mode": "extract", "extract": llm_draft, "llm": True})[0], 400)
        self.assertFalse((server.SAMPLES_ROOT / "smoke_llm_draft" / "package").exists())


if __name__ == "__main__":
    unittest.main()
