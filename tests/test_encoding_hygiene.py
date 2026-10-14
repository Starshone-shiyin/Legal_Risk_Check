import tempfile
import unittest
from pathlib import Path

from tools.check_encoding_hygiene import build_report


class EncodingHygieneTest(unittest.TestCase):
    def test_reports_utf8_decode_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bad_file = root / "bad.txt"
            bad_file.write_bytes(b"\xff\xfe\x00")

            report = build_report(root)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertEqual(report["summary"]["utf8_error_count"], 1)
        self.assertEqual(report["utf8_errors"][0]["path"], "bad.txt")

    def test_reports_suspicious_question_separator_as_advisory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            doc = root / "summary.md"
            suspicious_text = "最终证据缺少。" + "?" + "场景核心条文缺少。\n"
            doc.write_text(suspicious_text, encoding="utf-8")

            report = build_report(root)

        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["suspicious_question_separator_count"], 1)
        self.assertEqual(
            report["suspicious_question_separator_hits"][0]["marker"],
            "suspicious_question_mark_separator",
        )

    def test_allows_intentional_mojibake_markers_in_ingestion_checker(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tool = root / "tools" / "check_ingestion_quality.py"
            tool.parent.mkdir()
            markers = "|".join(chr(code) for code in [0x9365, 0x93B4, 0x7ED7, 0x6D93, 0x7039, 0x93C1, 0x9428])
            tool.write_text(
                'def suspicious_noise(text):\n'
                f'    if re.search(r"{markers}", text):\n'
                '        return ["possible_mojibake"]\n',
                encoding="utf-8",
            )

            report = build_report(root)

        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["mojibake_hit_count"], 0)
        self.assertGreaterEqual(report["summary"]["allowed_mojibake_hit_count"], 1)

    def test_reports_temp_directories_without_deleting_them(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            temp_dir = root / "tests" / "tmpabc123"
            temp_dir.mkdir(parents=True)

            report = build_report(root)

            self.assertTrue(temp_dir.exists())

        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["temporary_directory_count"], 1)
        self.assertEqual(report["temporary_directory_hits"][0]["path"], "tests/tmpabc123")
        self.assertTrue(report["temporary_directory_hits"][0]["empty"])

    def test_skips_own_default_report_to_avoid_recursive_findings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            report_path = root / "tests" / "encoding_hygiene_report.json"
            report_path.parent.mkdir()
            replacement_char = chr(0xFFFD)
            report_path.write_text(f'{{"preview": "if \\"{replacement_char}\\" in text"}}\n', encoding="utf-8")

            report = build_report(root)

        self.assertEqual(report["summary"]["status"], "passed")
        self.assertNotIn("tests/encoding_hygiene_report.json", report["files_checked"])
        self.assertEqual(report["summary"]["mojibake_hit_count"], 0)

    def test_skips_historical_and_review_snapshots(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            backup_file = root / "backup" / "old" / "snapshot.py"
            backup_file.parent.mkdir(parents=True)
            replacement_char = chr(0xFFFD)
            backup_file.write_text(f'text = "{replacement_char}"\n', encoding="utf-8")
            review_file = root / ".review_tmp" / "encoding.json"
            review_file.parent.mkdir(parents=True)
            review_file.write_text(f'{{"preview": "{replacement_char}"}}\n', encoding="utf-8")

            report = build_report(root)

        self.assertNotIn("backup/old/snapshot.py", report["files_checked"])
        self.assertNotIn(".review_tmp/encoding.json", report["files_checked"])
        self.assertEqual(report["summary"]["error_count"], 0)


if __name__ == "__main__":
    unittest.main()
