from pathlib import Path
import unittest


class ApiDesignTest(unittest.TestCase):
    def test_api_design_doc_exists_and_covers_core_interfaces(self):
        root = Path(__file__).resolve().parents[1]
        doc = root / "docs" / "api_design.md"
        text = doc.read_text(encoding="utf-8")

        required_sections = [
            "文档目的",
            "设计依据",
            "接口设计原则",
            "通用约定",
            "接口总览",
            "系统配置接口",
            "知识库接口",
            "数据集接口",
            "聊天接口",
            "搜索接口",
            "文档集接口",
            "接口协作约束",
            "可测试性设计",
            "验收标准",
        ]
        for item in required_sections:
            self.assertIn(item, text)

        required_paths = [
            "/health",
            "/sys/auth/regist",
            "/sys/auth/login",
            "/sys/model/prvd/list",
            "/sys/model/prvd/my/list",
            "/sys/model/prvd/param/list/{prvdId}",
            "/sys/model/param/prvd/{prvdId}",
            "/sys/model/prvd/modl/{prvdId}",
            "/sys/model/my/list",
            "/sys/setting/user/{prmCd}",
            "/sys/file/upload",
            "/knb/repository/setting",
            "/knb/dataset/upload/document",
            "/knb/dataset/upload/link",
            "/knb/dataset/reindex/{id}",
            "/knb/chat/message",
            "/knb/chat/remessage",
            "/knb/search",
            "/doc/document/to/dataset",
        ]
        for item in required_paths:
            self.assertIn(item, text)

        required_events = [
            "chat_message_entity",
            "chat_message_chunk",
            "chat_message_quote",
            "chat_message_error",
        ]
        for item in required_events:
            self.assertIn(item, text)

    def test_navigation_mentions_api_design(self):
        root = Path(__file__).resolve().parents[1]
        agents = (root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("docs/api_design.md", agents)
        self.assertIn("docs/database_design.md", agents)

    def test_api_design_is_implementation_agnostic(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "docs" / "api_design.md").read_text(encoding="utf-8")

        for item in [".py", "wenkb-server/", "wenkb-client/"]:
            self.assertNotIn(item, text)


if __name__ == "__main__":
    unittest.main()
