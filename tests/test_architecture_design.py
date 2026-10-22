from pathlib import Path
import unittest


class ArchitectureDesignTest(unittest.TestCase):
    def test_requirements_and_architecture_docs_are_implementation_agnostic(self):
        root = Path(__file__).resolve().parents[1]
        req = (root / "docs" / "requirements_analysis.md").read_text(encoding="utf-8")
        arch = (root / "docs" / "architecture_design.md").read_text(encoding="utf-8")

        req_sections = [
            "需求分析",
            "参考对象",
            "产品定位",
            "业务流程",
            "功能需求",
            "非功能需求",
            "文档基线与维护",
        ]
        for item in req_sections:
            self.assertIn(item, req)
        self.assertNotIn("docs/user_manual.md", req)

        arch_sections = [
            "设计目的",
            "设计原则",
            "系统上下文",
            "总体架构",
            "分层设计",
            "核心模块",
            "关键数据流",
            "状态模型",
            "验收标准",
        ]
        for item in arch_sections:
            self.assertIn(item, arch)

        for text in (req, arch):
            self.assertNotIn(".py", text)
            self.assertNotIn("wenkb-server/", text)
            self.assertNotIn("wenkb-client/", text)

    def test_agents_navigation_includes_architecture_doc(self):
        root = Path(__file__).resolve().parents[1]
        agents = root / "AGENTS.md"
        text = agents.read_text(encoding="utf-8")
        self.assertIn("docs/architecture_design.md", text)
        self.assertIn("docs/requirements_analysis.md", text)
        self.assertIn("详细设计阶段再补充实现映射", text)


if __name__ == "__main__":
    unittest.main()
