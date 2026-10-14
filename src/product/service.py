from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from src.product.repository import (
    DEFAULT_VIEW_MODEL_PATH,
    FixtureProductViewRepository,
    ProductViewModelError,
    ProductViewRepository,
)

__all__ = ["DEFAULT_VIEW_MODEL_PATH", "ProductViewModelError", "ProductViewModelService"]


class ProductViewModelService:
    """Read-only fixture-backed service for product view endpoints."""

    def __init__(self, repository: ProductViewRepository | Path | None = None) -> None:
        if repository is None:
            self.repository = FixtureProductViewRepository()
        elif isinstance(repository, Path):
            self.repository = FixtureProductViewRepository(repository)
        else:
            self.repository = repository

    def _payload(self) -> dict[str, Any]:
        return self.repository.load_payload()

    def _view_model(self, name: str) -> dict[str, Any]:
        payload = self._payload()
        view_model = payload.get("view_models", {}).get(name)
        if not isinstance(view_model, dict):
            raise ProductViewModelError("PRODUCT_VIEW_MODEL_MISSING", f"missing product view model: {name}")
        return copy.deepcopy(view_model)

    def dashboard_summary(self) -> dict[str, Any]:
        return self._view_model("dashboard_summary")

    def legal_workspace(self) -> dict[str, Any]:
        return self._view_model("legal_workspace")

    def market_signals(self) -> dict[str, Any]:
        return self._view_model("market_signals")

    def supply_chain_map(self) -> dict[str, Any]:
        return self._view_model("supply_chain_map")

    def lifecycle_risk(self) -> dict[str, Any]:
        return self._view_model("lifecycle_risk")

    def product_risks(
        self,
        risk_level: str | None = None,
        domain: str | None = None,
        review_status: str | None = None,
    ) -> list[dict[str, Any]]:
        risks = copy.deepcopy(self._payload().get("product_risks", []))
        if risk_level:
            risks = [risk for risk in risks if risk.get("risk_level") == risk_level]
        if domain:
            risks = [risk for risk in risks if risk.get("domain") == domain]
        if review_status:
            risks = [risk for risk in risks if risk.get("review_status") == review_status]
        return risks
