from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProjectStructureTest(unittest.TestCase):
    def test_local_task_scratch_directory_is_ignored(self):
        ignore_rules = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

        self.assertIn(".codex_tmp/", ignore_rules)


if __name__ == "__main__":
    unittest.main()
