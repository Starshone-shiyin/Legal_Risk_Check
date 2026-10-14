import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app
from src.supply_chain import router as supply_chain_router_module
from src.supply_chain.repository import SupplyChainRepository
from src.supply_chain.service import SupplyChainService


class SupplyChainApiTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.previous_service = supply_chain_router_module.service
        supply_chain_router_module.service = SupplyChainService(
            SupplyChainRepository(Path(self.temporary_directory.name) / "supply_chain.json")
        )
        self.client = TestClient(app)

    def tearDown(self):
        supply_chain_router_module.service = self.previous_service
        self.temporary_directory.cleanup()

    def test_supplier_records_are_created_updated_and_deleted(self):
        payload = {
            "name": "测试供应商",
            "country": "中国",
            "province": "广东",
            "city": "深圳",
            "category": "电子元器件",
            "spend_share": 32.5,
            "criticality": 88,
            "alternate_sources": 1,
            "compliance_risk": 24,
            "external_tags": ["出口管制"],
            "external_signal_ids": [],
            "security_code": "NVDA",
            "risk_owner": "采购合规负责人",
            "control_status": "monitoring",
            "last_reviewed_at": "2026-07-27",
            "evidence_refs": ["供应商尽调报告"],
        }

        created = self.client.post("/supply-chain/suppliers", json=payload)
        self.assertEqual(created.status_code, 201)
        supplier_id = created.json()["data"]["supplier_id"]

        listed = self.client.get("/supply-chain/suppliers")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.json()["items"]), 1)
        self.assertEqual(listed.json()["items"][0]["province"], "广东")
        self.assertEqual(listed.json()["items"][0]["security_code"], "us_NVDA")
        self.assertEqual(listed.json()["items"][0]["control_status"], "monitoring")

        payload["criticality"] = 67
        updated = self.client.put(f"/supply-chain/suppliers/{supplier_id}", json=payload)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["data"]["criticality"], 67)

        deleted = self.client.delete(f"/supply-chain/suppliers/{supplier_id}")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.json()["deleted_id"], supplier_id)
        self.assertEqual(self.client.get("/supply-chain/suppliers").json()["items"], [])


if __name__ == "__main__":
    unittest.main()
