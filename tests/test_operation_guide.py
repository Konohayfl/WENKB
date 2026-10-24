from pathlib import Path
import unittest


class OperationGuideTest(unittest.TestCase):
    def test_operation_guide_covers_developer_and_user_manuals(self):
        root = Path(__file__).resolve().parents[1]
        doc = root / "docs" / "wenkb_operation_guide.md"
        text = doc.read_text(encoding="utf-8")

        required_sections = [
            "开发者手册目的",
            "项目运行形态",
            "本地目录说明",
            "启动流程",
            "后台任务",
            "数据与配置维护",
            "开发验证",
            "开发者常见排查",
            "用户手册目的",
            "首次使用",
            "配置大模型",
            "创建知识库",
            "导入资料",
            "管理数据集",
            "知识库问答",
            "搜索资料",
            "使用文档集",
            "用户常见问题",
            "用户使用建议",
            "手册维护建议",
        ]
        for item in required_sections:
            self.assertIn(item, text)

        required_terms = [
            "16088",
            "SQLite",
            "resources/database/wenkb.db",
            "/health",
            "idxSts",
            "enbSts = enb",
            "API Key",
            "PDF",
            "topK",
            "smlrTrval",
            "引用来源",
            "局域网部署",
            "文档转入知识库",
            "WENKB_JWT_SECRET",
            "登录 JWT",
            "注册账号",
            "密码哈希",
        ]
        for item in required_terms:
            self.assertIn(item, text)

        forbidden_markers = [
            "代码运行流程",
            "如何导入大模型",
            "如何导入知识库",
            "如何运用知识库进行问答",
            "常见排查点",
        ]
        for item in forbidden_markers:
            self.assertNotIn(item, text)


if __name__ == "__main__":
    unittest.main()
