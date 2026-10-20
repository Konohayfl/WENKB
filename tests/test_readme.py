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
            "数据与运行约定",
            "常见问题",
        ]
        for item in required_terms:
            self.assertIn(item, text)

        required_links = [
            "docs/requirements_analysis.md",
            "docs/architecture_design.md",
            "docs/detailed_design.md",
            "docs/database_design.md",
            "docs/api_design.md",
            "docs/wenkb_operation_guide.md",
            "docs/deployment_guide.md",
            "docs/test_plan.md",
            "docs/test_scorebook_manual_run.md",
            "docs/change_management.md",
            "docs/code_maintenance_handoff.md",
        ]
        for item in required_links:
            self.assertIn(item, text)

        required_values = [
            "16088",
            "11420",
            "wenkb-server/resources/database/wenkb.db",
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
