"""BM25 sparse encoder for Chinese legal text. Pure scipy + numpy, no torch.

Usage:
    encoder = BM25Encoder()
    encoder.fit(all_documents)          # once, on all chunks
    indices, values = encoder.encode(doc)  # per chunk during ingestion
"""

from __future__ import annotations

import json
import logging
import math
from collections import Counter
from functools import lru_cache
from pathlib import Path

import jieba
import numpy as np

logger = logging.getLogger(__name__)

BM25_K1 = 1.2
BM25_B = 0.75


class BM25Encoder:
    """Lightweight BM25 encoder for Qdrant sparse vectors."""

    def __init__(self):
        self.vocab: dict[str, int] = {}          # term -> index
        self.idf: dict[str, float] = {}          # term -> IDF
        self.doc_count: int = 0
        self.avgdl: float = 0.0
        self._fitted = False

    def _tokenize(self, text: str) -> list[str]:
        tokens = jieba.lcut(text)
        return [t.strip() for t in tokens if len(t.strip()) >= 2]

    def fit(self, documents: list[str]):
        """Fit BM25 on all documents: compute IDF and avgdl."""
        if not documents:
            logger.warning("BM25 fit called with empty document list")
            return

        N = len(documents)
        df: dict[str, int] = {}
        total_len = 0

        for doc in documents:
            tokens = self._tokenize(doc)
            total_len += len(tokens)
            seen = set()
            for token in tokens:
                if token not in seen:
                    df[token] = df.get(token, 0) + 1
                    seen.add(token)

        self.avgdl = total_len / N if N > 0 else 1.0
        self.doc_count = N

        # Build vocabulary + IDF
        self.vocab = {}
        self.idf = {}
        for idx, (term, freq) in enumerate(sorted(df.items())):
            self.vocab[term] = idx
            self.idf[term] = math.log((N - freq + 0.5) / (freq + 0.5) + 1.0)

        self._fitted = True
        logger.info("BM25 fitted: %d terms, %d docs, avgdl=%.1f",
                     len(self.vocab), N, self.avgdl)

    def encode(self, text: str) -> tuple[list[int], list[float]]:
        """Encode text to (indices, values) for Qdrant sparse vector."""
        if not self._fitted:
            return [], []

        tokens = self._tokenize(text)
        if not tokens:
            return [], []

        doc_len = len(tokens)
        tf = Counter(tokens)

        indices = []
        values = []
        for term, freq in tf.items():
            idx = self.vocab.get(term)
            if idx is None:
                continue
            idf = self.idf.get(term, 0.0)
            numerator = freq * (BM25_K1 + 1)
            denominator = freq + BM25_K1 * (1 - BM25_B + BM25_B * doc_len / self.avgdl)
            score = idf * numerator / denominator
            if score > 1e-6:
                indices.append(idx)
                values.append(float(score))

        return indices, values

    def save(self, path: str | Path):
        """Save encoder state to JSON."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "vocab": self.vocab,
                "idf": self.idf,
                "doc_count": self.doc_count,
                "avgdl": self.avgdl,
            }, f, ensure_ascii=False)
        logger.info("BM25 encoder saved to %s", path)

    @classmethod
    def load(cls, path: str | Path) -> "BM25Encoder":
        """Load encoder state from JSON."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        enc = cls()
        enc.vocab = data["vocab"]
        enc.idf = data["idf"]
        enc.doc_count = data["doc_count"]
        enc.avgdl = data["avgdl"]
        enc._fitted = True
        logger.info("BM25 encoder loaded from %s (%d terms)", path, len(enc.vocab))
        return enc


@lru_cache(maxsize=1)
def get_bm25_encoder() -> BM25Encoder:
    """Get or load the global BM25 encoder. Fits on first call if needed."""
    cache_path = Path(__file__).parent.parent.parent / "config" / "bm25_encoder.json"
    if cache_path.exists():
        try:
            return BM25Encoder.load(cache_path)
        except Exception:
            logger.warning("Failed to load cached BM25 encoder, will rebuild")

    encoder = BM25Encoder()
    all_docs = _collect_all_chunks()
    encoder.fit(all_docs)
    encoder.save(cache_path)
    return encoder


def _collect_all_chunks() -> list[str]:
    """Collect all chunk texts from knowledge manifest."""
    manifest_path = Path(__file__).parent.parent.parent / "knowledge_manifest.json"
    if not manifest_path.exists():
        return []

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    docs = []
    for entry in manifest.get("documents", []):
        file_path = Path(entry["file_path"])
        if not file_path.exists():
            continue
        text = file_path.read_text(encoding="utf-8")
        # Use same chunking logic as ingestion for consistency
        from src.rag.ingestion import load_txt
        chunks = load_txt(str(file_path))
        for chunk in chunks:
            docs.append(chunk.page_content)
    return docs
