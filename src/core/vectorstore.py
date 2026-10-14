import logging

from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_qdrant import QdrantVectorStore

from src.config import get_settings
from src.core.embeddings import get_embeddings

logger = logging.getLogger(__name__)

COLLECTION_NAME = get_settings().qdrant_collection

def get_qdrant_client() -> QdrantClient:
    s = get_settings()
    return QdrantClient(host=s.qdrant_host, port=s.qdrant_port)


def ensure_collection_with_sparse(collection_name: str = COLLECTION_NAME) -> None:
    """确保 collection 存在且支持 dense + sparse vectors。不存在则创建，存在但无 sparse 则重建。"""
    client = get_qdrant_client()
    try:
        info = client.get_collection(collection_name)
        has_sparse = info.config.params.sparse_vectors is not None
        if has_sparse:
            logger.info("Collection %s already has sparse_vectors, skip", collection_name)
            return
        logger.info("Collection %s exists but no sparse_vectors, recreating", collection_name)
        client.delete_collection(collection_name)
    except Exception:
        logger.info("Collection %s does not exist, creating", collection_name)

    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
        sparse_vectors_config={
            "bm25": models.SparseVectorParams(
                index=models.SparseIndexParams(on_disk=False),
            )
        },
    )
    logger.info("Collection %s created with dense + sparse vectors", collection_name)


def get_vectorstore(collection_name: str = COLLECTION_NAME) -> QdrantVectorStore:
    return QdrantVectorStore(
        client=get_qdrant_client(),
        collection_name=collection_name,
        embedding=get_embeddings(),
    )
