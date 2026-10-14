from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from src.product.contracts import SOURCE_VIEW_MODEL_VERSION
from src.product.status import PRODUCT_ERROR_BY_CODE


DEFAULT_VIEW_MODEL_PATH = Path("tests/fixtures/product_view_models_v0.4.18.3.json")


class ProductViewModelError(RuntimeError):
    def __init__(self, code: str, detail: str | None = None) -> None:
        catalog_item = PRODUCT_ERROR_BY_CODE[code]
        self.code = code
        self.http_status = int(catalog_item["http_status"])
        self.public_message = str(catalog_item["message"])
        self.detail = detail or self.public_message
        super().__init__(self.detail)


class ProductViewRepository(Protocol):
    source_name: str

    def load_payload(self) -> dict[str, Any]:
        ...


class FixtureProductViewRepository:
    source_name = "fixture_sample"

    def __init__(self, fixture_path: Path = DEFAULT_VIEW_MODEL_PATH) -> None:
        self.fixture_path = fixture_path

    def load_payload(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ProductViewModelError(
                "PRODUCT_VIEW_MODEL_UNAVAILABLE",
                f"product view model fixture is unavailable: {self.fixture_path}",
            ) from exc
        except json.JSONDecodeError as exc:
            raise ProductViewModelError(
                "PRODUCT_VIEW_MODEL_INVALID_JSON",
                f"product view model fixture is not valid JSON: {self.fixture_path}",
            ) from exc
        if payload.get("version") != SOURCE_VIEW_MODEL_VERSION:
            raise ProductViewModelError(
                "PRODUCT_VIEW_MODEL_VERSION_MISMATCH",
                f"product view model version mismatch: expected {SOURCE_VIEW_MODEL_VERSION}, got {payload.get('version')}",
            )
        return payload


PRODUCT_DATA_SOURCE_BOUNDARY = {
    "version": "0.4.18.8",
    "default_repository": "FixtureProductViewRepository",
    "default_source_name": "fixture_sample",
    "repository_interface": "ProductViewRepository.load_payload() -> dict[str, Any]",
    "router_dependency_boundary": "router depends on ProductViewModelService, not on fixture paths or real data clients",
    "service_dependency_boundary": "service depends on ProductViewRepository protocol",
    "future_allowed_providers": [
        "legal_rag_summary_provider",
        "market_signal_provider",
        "supply_chain_provider",
        "lifecycle_risk_provider",
        "permission_context_provider",
    ],
    "currently_connected_providers": ["fixture_sample"],
    "currently_disallowed_runtime_access": {
        "rag": "not_called",
        "qdrant": "not_called",
        "llm": "not_called",
        "market_data": "not_called",
        "map_data": "not_called",
        "supply_chain_data": "not_called",
    },
}
