import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.main import app
from src.runtime_settings.service import read_runtime_settings


class RuntimeSettingsApiTest(unittest.TestCase):
    def test_runtime_settings_masks_secrets_and_persists_rss_configuration(self):
        client = TestClient(app)
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            env_path = Path(directory) / ".env"
            env_path.write_text(
                'LLM_API_KEY="existing-secret"\nSILICONFLOW_API_KEY="embedding-secret"\n'
                'EXTERNAL_RISK_WEB_SEARCH_API_KEY="search-secret"\nLLM_MODEL="old-model"\n',
                encoding="utf-8",
            )
            with patch("src.runtime_settings.service.ENV_PATH", env_path):
                before = client.get("/settings/runtime")
                self.assertEqual(before.status_code, 200)
                self.assertNotIn("existing-secret", before.text)
                self.assertTrue(before.json()["data"]["llm_api_key_configured"])
                self.assertTrue(before.json()["data"]["vision_llm_api_key_configured"])
                self.assertEqual(before.json()["data"]["vision_llm_model"], "deepseek-v4-flash-vision-exp")
                self.assertTrue(before.json()["data"]["siliconflow_api_key_configured"])
                self.assertTrue(before.json()["data"]["external_risk_web_search_api_key_configured"])

                response = client.put(
                    "/settings/runtime",
                    json={
                        "llm_provider": "anthropic_messages",
                        "llm_base_url": "https://api.anthropic.com",
                        "llm_model": "configured-model",
                        "vision_llm_enabled": True,
                        "vision_llm_base_url": "https://vision.example.com/v1",
                        "vision_llm_model": "deepseek-v4-flash-vision-exp",
                        "vision_llm_api_key": "vision-secret",
                        "external_risk_live_enabled": True,
                        "external_risk_intelligence_poll_seconds": 120,
                        "external_risk_web_search_enabled": True,
                        "external_risk_web_search_provider": "tavily",
                        "external_risk_web_search_timeout_seconds": 10,
                        "external_risk_web_search_max_results": 4,
                        "intelligence_feeds": [
                            {
                                "feed_id": "company-rss",
                                "name": "Company RSS",
                                "url": "https://example.com/feed.xml",
                                "signal_type": "news",
                                "adapter": "rss_atom",
                                "risk_relevance": 0.8,
                            }
                        ],
                    },
                )

                self.assertEqual(response.status_code, 200)
                self.assertNotIn("existing-secret", response.text)
                data = response.json()["data"]
                self.assertEqual(data["llm_provider"], "anthropic_messages")
                self.assertEqual(data["llm_model"], "configured-model")
                self.assertTrue(data["vision_llm_enabled"])
                self.assertEqual(data["vision_llm_model"], "deepseek-v4-flash-vision-exp")
                self.assertEqual(data["external_risk_intelligence_poll_seconds"], 120)
                self.assertTrue(data["external_risk_web_search_enabled"])
                self.assertEqual(data["external_risk_web_search_provider"], "tavily")
                self.assertEqual(data["external_risk_web_search_max_results"], 4)
                self.assertEqual(data["intelligence_feeds"][0]["feed_id"], "company-rss")
                saved = env_path.read_text(encoding="utf-8")
                self.assertIn('LLM_PROVIDER="anthropic_messages"', saved)
                self.assertIn('LLM_MODEL="configured-model"', saved)
                self.assertIn('VISION_LLM_MODEL="deepseek-v4-flash-vision-exp"', saved)
                self.assertIn('VISION_LLM_API_KEY="vision-secret"', saved)
                self.assertIn("EXTERNAL_RISK_INTELLIGENCE_FEEDS", saved)
                self.assertIn('EXTERNAL_RISK_WEB_SEARCH_PROVIDER="tavily"', saved)
                self.assertNotIn("search-secret", response.text)
                self.assertNotIn("vision-secret", response.text)
                with patch.dict(os.environ, {}, clear=True):
                    persisted = read_runtime_settings()
                self.assertEqual(persisted.llm_provider, "anthropic_messages")
                self.assertEqual(persisted.llm_model, "configured-model")
                self.assertEqual(persisted.vision_llm_model, "deepseek-v4-flash-vision-exp")
                self.assertEqual(persisted.intelligence_feeds[0].feed_id, "company-rss")
                self.assertTrue(persisted.external_risk_web_search_enabled)

    def test_runtime_settings_rejects_unknown_web_search_provider(self):
        client = TestClient(app)
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            env_path = Path(directory) / ".env"
            env_path.write_text("", encoding="utf-8")
            with patch("src.runtime_settings.service.ENV_PATH", env_path):
                response = client.put(
                    "/settings/runtime",
                    json={"external_risk_web_search_provider": "untrusted-provider"},
                )
        self.assertEqual(response.status_code, 422)

    def test_runtime_settings_rejects_unknown_llm_protocol(self):
        client = TestClient(app)
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            env_path = Path(directory) / ".env"
            env_path.write_text("", encoding="utf-8")
            with patch("src.runtime_settings.service.ENV_PATH", env_path):
                response = client.put(
                    "/settings/runtime",
                    json={"llm_provider": "unsupported_protocol"},
                )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
