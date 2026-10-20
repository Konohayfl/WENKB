from pathlib import Path
import unittest


class DeploymentGuideTest(unittest.TestCase):
    def test_deployment_guide_doc_exists_and_covers_core_content(self):
        root = Path(__file__).resolve().parents[1]
        doc = root / "docs" / "deployment_guide.md"
        text = doc.read_text(encoding="utf-8")

        required_sections = [
            "文档目的",
            "设计依据",
            "当前部署策略",
            "部署前提",
            "启动与验收",
            "当前运维事项",
            "备份与恢复",
            "升级与回滚",
            "距离局域网部署所需要的改动",
            "风险与注意事项",
            "验收标准",
        ]
        for item in required_sections:
            self.assertIn(item, text)

        required_terms = [
            "SQLite",
            "16088",
            "resources/database/wenkb.db",
            "resources/vector_store",
            "resources/documents",
            "resources/static/upload",
            "健康检查",
            "备份",
            "回滚",
            "局域网",
            "访问控制",
            "共享存储",
            "WENKB_JWT_SECRET",
            "HS256 JWT",
        ]
        for item in required_terms:
            self.assertIn(item, text)

    def test_deployment_guide_is_implementation_agnostic(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "docs" / "deployment_guide.md").read_text(encoding="utf-8")

        forbidden_markers = [
            ".py",
            "wenkb-server/",
            "wenkb-client/",
        ]
        for item in forbidden_markers:
            self.assertNotIn(item, text)

    def test_agents_navigation_mentions_deployment_guide(self):
        root = Path(__file__).resolve().parents[1]
        agents = (root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("docs/deployment_guide.md", agents)


if __name__ == "__main__":
    unittest.main()
