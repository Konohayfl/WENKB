from pathlib import Path
import sqlite3
import unittest


class DatabaseDesignTest(unittest.TestCase):
    def test_versioned_runtime_database_has_current_schema_and_auth_table(self):
        root = Path(__file__).resolve().parents[1]
        database = root / "wenkb-server" / "resources" / "database" / "wenkb.db"
        self.assertTrue(database.is_file())

        with sqlite3.connect(database) as connection:
            version = connection.execute(
                "SELECT version FROM t_sys_schema_version"
            ).fetchone()
            self.assertEqual(version, (6,))
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            self.assertIn("t_sys_user", tables)
            indexes = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'index'"
                )
            }
            self.assertIn("uq_sys_user_username", indexes)

    def test_database_design_doc_exists_and_covers_core_domains(self):
        root = Path(__file__).resolve().parents[1]
        doc = root / "docs" / "database_design.md"
        text = doc.read_text(encoding="utf-8")

        required_sections = [
            "文档目的",
            "设计依据",
            "存储范围",
            "逻辑 ER 关系",
            "表清单",
            "系统与模型配置表",
            "知识库核心表",
            "知识增强表",
            "聊天与搜索表",
            "文档集表",
            "向量库映射设计",
            "事务与一致性规则",
            "状态流转规则",
            "安全与隐私设计",
            "验收标准",
        ]
        for item in required_sections:
            self.assertIn(item, text)

        required_entities = [
            "t_sys_model_provider",
            "t_sys_model",
            "t_sys_model_param_value",
            "t_sys_user_model_preference",
            "t_sys_user",
            "t_knb_repository",
            "t_knb_repository_setting",
            "t_knb_dataset",
            "t_knb_dataset_chunk",
            "t_knb_dataset_summary",
            "t_knb_repository_qa",
            "t_knb_dataset_triplet",
            "t_knb_index_error",
            "t_knb_chat",
            "t_knb_chat_message",
            "t_knb_chat_quote",
            "t_knb_search_history",
            "t_doc_docset",
            "t_doc_document",
            "t_doc_document_version",
        ]
        for item in required_entities:
            self.assertIn(item, text)

    def test_database_design_is_target_product_baseline(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "docs" / "database_design.md").read_text(encoding="utf-8")

        required_design_markers = [
            "不以当前项目代码作为设计依据",
            "关系型数据库",
            "向量数据库",
            "文件系统",
            "最终一致",
            "敏感数据",
            "加密存储",
            "脱敏",
            "引用表保存问答当时的片段快照",
        ]
        for item in required_design_markers:
            self.assertIn(item, text)

        forbidden_markers = [
            ".py",
            "wenkb-server/",
            "wenkb-client/",
        ]
        for item in forbidden_markers:
            self.assertNotIn(item, text)


if __name__ == "__main__":
    unittest.main()
