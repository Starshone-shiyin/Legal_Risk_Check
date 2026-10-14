import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.check_research_figure_assets import FIGURE_NAMES, build_report


class ResearchFigureAssetsTest(unittest.TestCase):
    def test_current_core_technology_figures_pass_offline_quality_check(self):
        report = build_report(Path("reports/core_tech_20260810"))

        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["checked_figure_count"], 4)
        for figure in report["figures"]:
            self.assertEqual(figure["dimensions"], [2400, 1350])
            self.assertTrue(figure["checks"]["dpi_rounds_to_300"])
            self.assertTrue(figure["checks"]["rgb_or_rgba"])
            self.assertTrue(figure["checks"]["non_empty"])

    def test_accepts_png_dpi_rounding_and_rejects_invalid_figure_properties(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            figure_dir = Path(tmpdir)
            for name in FIGURE_NAMES:
                Image.new("RGB", (2400, 1350), "white").save(figure_dir / name, dpi=(300, 300))

            report = build_report(figure_dir)
            self.assertEqual(report["summary"]["status"], "passed")

            Image.new("L", (1200, 675), "white").save(figure_dir / FIGURE_NAMES[0], dpi=(72, 72))
            report = build_report(figure_dir)
            invalid = report["figures"][0]

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn(FIGURE_NAMES[0], report["summary"]["failed_figures"])
        self.assertFalse(invalid["checks"]["dimensions_2400x1350"])
        self.assertFalse(invalid["checks"]["dpi_rounds_to_300"])
        self.assertFalse(invalid["checks"]["rgb_or_rgba"])


if __name__ == "__main__":
    unittest.main()
