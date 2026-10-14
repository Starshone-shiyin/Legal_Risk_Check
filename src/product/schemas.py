from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from src.product.contracts import PRODUCT_API_VERSION, SOURCE_VIEW_MODEL_VERSION


class ProductResponseMeta(BaseModel):
    contract_version: str = PRODUCT_API_VERSION
    source_view_model_version: str = SOURCE_VIEW_MODEL_VERSION
    data_source: Literal["fixture_sample"] = "fixture_sample"
    runtime_data_access: dict[str, str] = Field(
        default_factory=lambda: {
            "rag": "not_called",
            "qdrant": "not_called",
            "llm": "not_called",
            "market_data": "not_called",
            "map_data": "not_called",
            "supply_chain_data": "not_called",
        }
    )


class ProductDataResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: dict[str, Any]
    meta: ProductResponseMeta = Field(default_factory=ProductResponseMeta)


class ProductListResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[dict[str, Any]]
    meta: ProductResponseMeta = Field(default_factory=ProductResponseMeta)
