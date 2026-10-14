"""Compatibility helpers for future project layout cleanup.

The current project still treats root-level ``tools/*.py`` entrypoints and
``tests/*.json`` generated reports as authoritative. These helpers only expose
stable path calculations for future dual-read/dual-write work; they do not move
files or change any tool defaults.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


LEGACY_REPORT_ROOT = Path("tests")
FUTURE_REPORT_ROOT = Path("reports")

REPORT_GROUPS = {
    "eval": FUTURE_REPORT_ROOT / "eval",
    "audits": FUTURE_REPORT_ROOT / "audits",
    "manual_review": FUTURE_REPORT_ROOT / "manual_review",
    "dry_run": FUTURE_REPORT_ROOT / "dry_run",
}


@dataclass(frozen=True)
class LayoutResolution:
    """Resolved legacy and future paths for one project artifact."""

    artifact_name: str
    legacy_path: Path
    future_path: Path
    selected_path: Path
    selected_source: str
    legacy_authoritative: bool = True
    migration_performed: bool = False


def legacy_report_path(name: str) -> Path:
    """Return the current authoritative generated-report path under tests/."""

    path = Path(name)
    if path.is_absolute() or len(path.parts) != 1:
        raise ValueError(f"Expected a report filename, got: {name}")
    return LEGACY_REPORT_ROOT / path


def report_scaffold_path(group: str, name: str) -> Path:
    """Return the future scaffold path for an explicitly grouped report."""

    path = Path(name)
    if path.is_absolute() or len(path.parts) != 1:
        raise ValueError(f"Expected a report filename, got: {name}")
    if group not in REPORT_GROUPS:
        raise ValueError(f"Unknown report group: {group}")
    return REPORT_GROUPS[group] / path


def project_root(anchor: Path | None = None) -> Path:
    """Return the repository root without assuming the caller's depth.

    The function walks upward until it sees the directories that define this
    repository. This keeps future subdirectory tools from relying on
    ``Path(__file__).parents[1]``.
    """

    current = (anchor or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "src").is_dir() and (candidate / "tools").is_dir() and (candidate / "tests").is_dir():
            return candidate
    raise ValueError(f"Could not locate project root from {current}")


def normalize_relative_path(path: Path | str) -> Path:
    """Normalize a relative project path without resolving it against cwd."""

    raw_path = Path(path)
    if raw_path.is_absolute():
        raise ValueError(f"Expected a project-relative path, got absolute path: {raw_path}")
    return Path(*raw_path.parts)


def resolve_repo_path(path: Path | str, root: Path | None = None) -> Path:
    """Resolve a project-relative path against the repository root."""

    raw_path = Path(path)
    if raw_path.is_absolute():
        return raw_path
    return (project_root(root) / raw_path).resolve()


def display_path(path: Path | str, root: Path | None = None) -> str:
    """Return a project-relative display path when possible."""

    raw_path = Path(path)
    base = project_root(root)
    try:
        return str(raw_path.resolve().relative_to(base))
    except ValueError:
        return str(raw_path)


def future_report_path(legacy_report_path: Path | str, group: str) -> Path:
    """Map ``tests/<name>`` to ``reports/<group>/<name>`` for future mirrors."""

    legacy_path = normalize_relative_path(legacy_report_path)
    if group not in REPORT_GROUPS:
        raise ValueError(f"Unknown report group: {group}")
    if not legacy_path.parts or legacy_path.parts[0] != LEGACY_REPORT_ROOT.name:
        raise ValueError(f"Expected legacy report path under tests/: {legacy_path}")
    if len(legacy_path.parts) != 2:
        raise ValueError(f"Expected a direct tests/<file> report path: {legacy_path}")
    return REPORT_GROUPS[group] / legacy_path.name


def resolve_report_pair(legacy_report_path: Path | str, group: str) -> LayoutResolution:
    """Resolve current and future locations while keeping legacy authoritative."""

    legacy_path = normalize_relative_path(legacy_report_path)
    mapped_future_path = future_report_path(legacy_path, group)
    return LayoutResolution(
        artifact_name=legacy_path.name,
        legacy_path=legacy_path,
        future_path=mapped_future_path,
        selected_path=legacy_path,
        selected_source="legacy_tests",
    )


def resolve_existing_report(
    legacy_report_path: Path | str,
    group: str,
    root: Path | None = None,
    *,
    allow_future_fallback: bool = False,
) -> LayoutResolution:
    """Resolve an existing report for future compatibility.

    By default this returns the legacy ``tests/`` path even when a future mirror
    exists. ``allow_future_fallback`` is intentionally explicit and only applies
    when the legacy file is absent.
    """

    base = project_root(root) if root else project_root()
    pair = resolve_report_pair(legacy_report_path, group)
    legacy_exists = (base / pair.legacy_path).exists()
    future_exists = (base / pair.future_path).exists()
    if legacy_exists or not allow_future_fallback or not future_exists:
        return pair
    return LayoutResolution(
        artifact_name=pair.artifact_name,
        legacy_path=pair.legacy_path,
        future_path=pair.future_path,
        selected_path=pair.future_path,
        selected_source="future_reports_fallback",
    )


def compatibility_contract() -> dict[str, object]:
    """Return a serializable summary of the current layout contract."""

    return {
        "legacy_report_root": str(LEGACY_REPORT_ROOT),
        "future_report_root": str(FUTURE_REPORT_ROOT),
        "legacy_report_paths_authoritative": True,
        "future_report_paths_are_mirrors_only": True,
        "automatic_migration": False,
        "tool_entrypoint_migration": False,
        "report_groups": {name: str(path) for name, path in sorted(REPORT_GROUPS.items())},
    }
