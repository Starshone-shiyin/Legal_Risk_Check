from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from src.supply_chain.repository import SupplyChainRepository
from src.supply_chain.schemas import SupplierInput, SupplierRecord


class SupplierNotFoundError(LookupError):
    pass


class SupplyChainService:
    def __init__(self, repository: SupplyChainRepository | None = None) -> None:
        self.repository = repository or SupplyChainRepository()

    def list_suppliers(self) -> list[SupplierRecord]:
        return [SupplierRecord.model_validate(item) for item in self.repository.load()]

    def create_supplier(self, payload: SupplierInput) -> SupplierRecord:
        now = datetime.now(timezone.utc)
        record = SupplierRecord(
            supplier_id=f"supplier-{uuid4().hex[:12]}",
            created_at=now,
            updated_at=now,
            **payload.model_dump(),
        )
        items = self.repository.load()
        items.append(record.model_dump(mode="json"))
        self.repository.save(items)
        return record

    def update_supplier(self, supplier_id: str, payload: SupplierInput) -> SupplierRecord:
        items = self.repository.load()
        for index, item in enumerate(items):
            if item.get("supplier_id") != supplier_id:
                continue
            record = SupplierRecord(
                supplier_id=supplier_id,
                created_at=item["created_at"],
                updated_at=datetime.now(timezone.utc),
                **payload.model_dump(),
            )
            items[index] = record.model_dump(mode="json")
            self.repository.save(items)
            return record
        raise SupplierNotFoundError(supplier_id)

    def delete_supplier(self, supplier_id: str) -> None:
        items = self.repository.load()
        remaining = [item for item in items if item.get("supplier_id") != supplier_id]
        if len(remaining) == len(items):
            raise SupplierNotFoundError(supplier_id)
        self.repository.save(remaining)
