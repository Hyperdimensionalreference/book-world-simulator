"""API Key storage and outbound-request security checks."""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from production import llm_config  # noqa: E402


class TestKeySecurity(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows DPAPI only")
    def test_key_is_encrypted_and_never_returned_by_public_config(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            path = folder / "llm.json"
            with patch.object(llm_config, "CONFIG_DIR", folder), patch.object(llm_config, "CONFIG_PATH", path):
                llm_config.save_llm_config({"api_key": "dummy-local-test-key", "enabled": True})
                raw = path.read_text(encoding="utf-8")
                self.assertNotIn("dummy-local-test-key", raw)
                self.assertNotIn('"api_key"', raw)
                self.assertEqual(llm_config.load_llm_config()["api_key"], "dummy-local-test-key")
                public = llm_config.public_llm_config()
                self.assertTrue(public["api_key_set"])
                self.assertNotIn("api_key", public)

                # 旧版明文文件首次读取后原位迁移，且仍可正常使用。
                path.write_text(json.dumps({"api_key": "legacy-dummy-key"}), encoding="utf-8")
                self.assertEqual(llm_config.load_llm_config()["api_key"], "legacy-dummy-key")
                self.assertNotIn("legacy-dummy-key", path.read_text(encoding="utf-8"))

    def test_remote_http_is_rejected_before_sending_key(self):
        cfg = {"base_url": "http://provider.example/v1", "api_key": "dummy", "enabled": True}
        with patch.object(llm_config, "load_llm_config", return_value=cfg), patch.object(llm_config, "open_api_request") as send:
            with self.assertRaisesRegex(RuntimeError, "HTTPS"):
                llm_config.chat_completion("hello")
            send.assert_not_called()
        self.assertEqual(llm_config.api_url({"base_url": "http://127.0.0.1:1234/v1"}, "chat/completions"), "http://127.0.0.1:1234/v1/chat/completions")

    def test_invalid_header_key_is_rejected_without_echo(self):
        with self.assertRaises(RuntimeError) as failure:
            llm_config.api_key_header({"api_key": "dummy\nsecret"})
        self.assertNotIn("dummy", str(failure.exception))

    def test_provider_error_body_is_not_returned(self):
        cfg = {"base_url": "https://provider.example/v1", "api_key": "dummy-secret", "enabled": True}
        error = urllib.error.HTTPError("https://provider.example/v1/chat/completions", 401, "Unauthorized", {}, io.BytesIO(b"dummy-secret in body"))
        with patch.object(llm_config, "load_llm_config", return_value=cfg), patch.object(llm_config, "open_api_request", side_effect=error):
            with self.assertRaises(RuntimeError) as failure:
                llm_config.chat_completion("hello")
        self.assertIn("401", str(failure.exception))
        self.assertNotIn("dummy-secret", str(failure.exception))


if __name__ == "__main__":
    unittest.main()
