from pathlib import Path
import unittest


class ReadmeTest(unittest.TestCase):
    def test_readme_covers_project_entry_points(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "README.md").read_text(encoding="utf-8")

        required_terms = [
            "快速开始",
            "后端",
            "前端",
            "主要能力",
            "文档入口",
            "目录说明",
            "常见问题",
        ]
        for item in required_terms:
            self.assertIn(item, text)

        required_links = [
            "AGENTS.md",
            "docs/development_environment_setup.md",
            "docs/deployment_guide.md",
            "docs/test_plan.md",
        ]
        for item in required_links:
            self.assertIn(item, text)

        self.assertNotIn("docs/requirements_analysis.md", text)
        self.assertNotIn("docs/test_scorebook_handoff.md", text)

        navigation = (root / "AGENTS.md").read_text(encoding="utf-8")
        for item in (
            "docs/requirements_analysis.md",
            "docs/architecture_knowledge_qa.md",
        ):
            self.assertIn(item, navigation)

        for retired_doc in (
            "docs/test_scorebook_handoff.md",
            "docs/test_execution_followup.md",
            "docs/test_scorebook_manual_run.md",
        ):
            self.assertFalse((root / retired_doc).exists())

        required_values = [
            "16088",
            "11420",
            "cd wenkb-server",
            "cd wenkb-client",
            "npm run dev",
            "WENKB_JWT_SECRET",
            "HS256 JWT",
        ]
        for item in required_values:
            self.assertIn(item, text)

    def test_readme_is_not_promotional(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "README.md").read_text(encoding="utf-8")

        forbidden_markers = [
            "✨",
            "🌐",
            "第二大脑",
            "重新定义",
            "下一代",
            "github.com/user-attachments",
        ]
        for item in forbidden_markers:
            self.assertNotIn(item, text)


if __name__ == "__main__":
    unittest.main()
