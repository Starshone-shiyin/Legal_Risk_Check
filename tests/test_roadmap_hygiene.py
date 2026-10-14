from pathlib import Path
import re
import unittest


ROADMAP_PATH = Path("docs/project_review_and_roadmap.md")


class RoadmapHygieneTest(unittest.TestCase):
    def test_recommended_next_step_does_not_accumulate_completed_version_ledger(self):
        content = ROADMAP_PATH.read_text(encoding="utf-8")
        heading = re.search(r"^## 推荐下一步\s*$", content, flags=re.MULTILINE)
        self.assertIsNotNone(heading)
        next_step = content[heading.end() :]
        next_major = re.search(r"^##\s+", next_step, flags=re.MULTILINE)
        if next_major:
            next_step = next_step[: next_major.start()]

        self.assertNotIn("（已完成）", next_step)
        self.assertNotIn("已完成）", next_step)
        version_headings = re.findall(r"^###\s+v\d+\.\d+\.\d+", next_step, flags=re.MULTILINE)
        self.assertLessEqual(len(version_headings), 1)


if __name__ == "__main__":
    unittest.main()
