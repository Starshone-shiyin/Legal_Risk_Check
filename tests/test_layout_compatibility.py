import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import (
    compatibility_contract,
    display_path,
    future_report_path,
    legacy_report_path,
    project_root,
    report_scaffold_path,
    resolve_existing_report,
    resolve_repo_path,
    resolve_report_pair,
)


class LayoutCompatibilityTest(unittest.TestCase):
    def test_named_helpers_keep_legacy_and_scaffold_paths_explicit(self):
        self.assertEqual(legacy_report_path("rag_eval_report.json"), Path("tests/rag_eval_report.json"))
        self.assertEqual(
            report_scaffold_path("eval", "rag_eval_report.json"),
            Path("reports/eval/rag_eval_report.json"),
        )
        with self.assertRaises(ValueError):
            legacy_report_path("nested/rag_eval_report.json")
        with self.assertRaises(ValueError):
            report_scaffold_path("unknown", "rag_eval_report.json")

    def test_future_report_path_maps_direct_tests_report_to_group(self):
        mapped = future_report_path("tests/rag_eval_report.json", "eval")

        self.assertEqual(mapped, Path("reports/eval/rag_eval_report.json"))

    def test_future_report_path_rejects_non_legacy_or_nested_paths(self):
        with self.assertRaises(ValueError):
            future_report_path("docs/rag_eval_report.json", "eval")
        with self.assertRaises(ValueError):
            future_report_path("tests/manual_review_export_pipeline_dry_run_artifacts/report.json", "dry_run")
        with self.assertRaises(ValueError):
            future_report_path("tests/rag_eval_report.json", "unknown")

    def test_resolve_report_pair_keeps_legacy_authoritative(self):
        resolution = resolve_report_pair("tests/manual_review_prescreen_report.json", "manual_review")

        self.assertEqual(resolution.selected_path, Path("tests/manual_review_prescreen_report.json"))
        self.assertEqual(resolution.selected_source, "legacy_tests")
        self.assertTrue(resolution.legacy_authoritative)
        self.assertFalse(resolution.migration_performed)

    def test_resolve_existing_report_uses_future_only_when_explicit_fallback_enabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "src").mkdir()
            (root / "tools").mkdir()
            (root / "tests").mkdir()
            future = root / "reports" / "eval" / "rag_eval_report.json"
            future.parent.mkdir(parents=True)
            future.write_text("{}", encoding="utf-8")

            default_resolution = resolve_existing_report("tests/rag_eval_report.json", "eval", root=root)
            fallback_resolution = resolve_existing_report(
                "tests/rag_eval_report.json",
                "eval",
                root=root,
                allow_future_fallback=True,
            )

        self.assertEqual(default_resolution.selected_path, Path("tests/rag_eval_report.json"))
        self.assertEqual(default_resolution.selected_source, "legacy_tests")
        self.assertEqual(fallback_resolution.selected_path, Path("reports/eval/rag_eval_report.json"))
        self.assertEqual(fallback_resolution.selected_source, "future_reports_fallback")

    def test_project_root_walks_up_from_nested_tool_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            nested = root / "tools" / "manual_review" / "workbench"
            (root / "src").mkdir()
            (root / "tests").mkdir()
            nested.mkdir(parents=True)

            resolved = project_root(nested)

        self.assertEqual(resolved, root.resolve())

    def test_resolve_and_display_repo_path_handle_windows_style_project_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "src").mkdir()
            (root / "tools").mkdir()
            (root / "tests").mkdir()
            target = root / "tests" / "rag_eval_cases.json"

            resolved = resolve_repo_path("tests/rag_eval_cases.json", root=root)
            displayed = display_path(target, root=root)

        self.assertEqual(resolved, target.resolve())
        self.assertEqual(Path(displayed), Path("tests/rag_eval_cases.json"))

    def test_contract_is_explicitly_non_migrating(self):
        contract = compatibility_contract()

        self.assertTrue(contract["legacy_report_paths_authoritative"])
        self.assertTrue(contract["future_report_paths_are_mirrors_only"])
        self.assertFalse(contract["automatic_migration"])
        self.assertFalse(contract["tool_entrypoint_migration"])


if __name__ == "__main__":
    unittest.main()
