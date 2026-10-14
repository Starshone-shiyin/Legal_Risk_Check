import unittest
from pathlib import Path


class FrontendBackendRoutingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).parents[1]
        cls.app_source = (root / "web" / "app.js").read_text(encoding="utf-8")

    def test_frontend_defaults_to_backend_start_script_port(self):
        self.assertIn('const DEFAULT_BACKEND_BASE_URL = "http://127.0.0.1:8000";', self.app_source)

    def test_stream_requests_use_failover_and_persist_working_backend(self):
        self.assertIn("async function fetchBackendStreamFrom(", self.app_source)
        self.assertIn("const candidates = [backendState.baseUrl, ...LOCAL_BACKEND_BASE_URLS]", self.app_source)
        self.assertIn("setWorkingBackendBaseUrl(baseUrl)", self.app_source)


if __name__ == "__main__":
    unittest.main()
