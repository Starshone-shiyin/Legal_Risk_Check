"""Immutable retrieval configurations used by offline ablation experiments.

The production RAG path intentionally keeps its established behavior when no
profile is supplied.  These profiles are opt-in and only isolate retrieval
components for reproducible, like-for-like evaluation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RetrievalExperimentProfile:
    """Feature switches for one retrieval-only ablation variant."""

    name: str
    description: str
    enable_sparse_recall: bool
    enable_concept_expansion: bool
    enable_concept_anchors: bool
    enable_deterministic_anchors: bool
    enable_complex_planner: bool
    enable_reranker: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_PROFILES: dict[str, RetrievalExperimentProfile] = {
    # Controlled ablation chain. Each C profile toggles exactly one additional
    # retrieval capability relative to its predecessor; production never uses
    # these profiles unless an experiment explicitly supplies one.
    "C0_dense": RetrievalExperimentProfile(
        name="C0_dense",
        description="Controlled baseline: dense retrieval only.",
        enable_sparse_recall=False,
        enable_concept_expansion=False,
        enable_concept_anchors=False,
        enable_deterministic_anchors=False,
        enable_complex_planner=False,
        enable_reranker=False,
    ),
    "C1_hybrid": RetrievalExperimentProfile(
        name="C1_hybrid",
        description="C0 plus BM25 sparse recall only.",
        enable_sparse_recall=True,
        enable_concept_expansion=False,
        enable_concept_anchors=False,
        enable_deterministic_anchors=False,
        enable_complex_planner=False,
        enable_reranker=False,
    ),
    "C2_query_expansion": RetrievalExperimentProfile(
        name="C2_query_expansion",
        description="C1 plus legal-concept query expansion only.",
        enable_sparse_recall=True,
        enable_concept_expansion=True,
        enable_concept_anchors=False,
        enable_deterministic_anchors=False,
        enable_complex_planner=False,
        enable_reranker=False,
    ),
    "C3_concept_anchors": RetrievalExperimentProfile(
        name="C3_concept_anchors",
        description="C2 plus direct legal-concept article anchors only.",
        enable_sparse_recall=True,
        enable_concept_expansion=True,
        enable_concept_anchors=True,
        enable_deterministic_anchors=False,
        enable_complex_planner=False,
        enable_reranker=False,
    ),
    "C4_scene_anchors": RetrievalExperimentProfile(
        name="C4_scene_anchors",
        description="C3 plus deterministic scenario anchors only.",
        enable_sparse_recall=True,
        enable_concept_expansion=True,
        enable_concept_anchors=True,
        enable_deterministic_anchors=True,
        enable_complex_planner=False,
        enable_reranker=False,
    ),
    "C5_complex_planner": RetrievalExperimentProfile(
        name="C5_complex_planner",
        description="C4 plus deterministic multi-issue planning only.",
        enable_sparse_recall=True,
        enable_concept_expansion=True,
        enable_concept_anchors=True,
        enable_deterministic_anchors=True,
        enable_complex_planner=True,
        enable_reranker=False,
    ),
    "C6_cross_encoder": RetrievalExperimentProfile(
        name="C6_cross_encoder",
        description="C5 plus Cross-Encoder reranking only.",
        enable_sparse_recall=True,
        enable_concept_expansion=True,
        enable_concept_anchors=True,
        enable_deterministic_anchors=True,
        enable_complex_planner=True,
        enable_reranker=True,
    ),
    "M1_dense": RetrievalExperimentProfile(
        name="M1_dense",
        description="Dense retrieval only; no sparse recall, anchors, planner, or reranking.",
        enable_sparse_recall=False,
        enable_concept_expansion=False,
        enable_concept_anchors=False,
        enable_deterministic_anchors=False,
        enable_complex_planner=False,
        enable_reranker=False,
    ),
    "M2_hybrid": RetrievalExperimentProfile(
        name="M2_hybrid",
        description="Dense and BM25 candidate union; no anchors, planner, or reranking.",
        enable_sparse_recall=True,
        enable_concept_expansion=False,
        enable_concept_anchors=False,
        enable_deterministic_anchors=False,
        enable_complex_planner=False,
        enable_reranker=False,
    ),
    "M3_concept": RetrievalExperimentProfile(
        name="M3_concept",
        description="M2 plus legal-concept query expansion and direct concept article anchors.",
        enable_sparse_recall=True,
        enable_concept_expansion=True,
        enable_concept_anchors=True,
        enable_deterministic_anchors=False,
        enable_complex_planner=False,
        enable_reranker=False,
    ),
    "M4_full": RetrievalExperimentProfile(
        name="M4_full",
        description="Full pipeline: dense/sparse recall, anchors, planner, and Cross-Encoder reranking.",
        enable_sparse_recall=True,
        enable_concept_expansion=True,
        enable_concept_anchors=True,
        enable_deterministic_anchors=True,
        enable_complex_planner=True,
        enable_reranker=True,
    ),
}


def resolve_experiment_profile(name: str | None) -> RetrievalExperimentProfile | None:
    """Resolve an opt-in profile, rejecting unknown names early."""
    if name is None:
        return None
    try:
        return _PROFILES[name]
    except KeyError as exc:
        available = ", ".join(_PROFILES)
        raise ValueError(f"Unknown experiment profile {name!r}; available: {available}") from exc


def list_experiment_profiles() -> list[RetrievalExperimentProfile]:
    """Return profiles in controlled-ablation then legacy-report order."""
    return list(_PROFILES.values())
