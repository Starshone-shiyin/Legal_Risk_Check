from src.core.vectorstore import ensure_collection_with_sparse


ensure_collection_with_sparse("legal_knowledge")
print("✅ 集合 'legal_knowledge' 已确保支持 dense + bm25 sparse")
