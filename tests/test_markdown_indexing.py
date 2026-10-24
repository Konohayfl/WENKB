from pathlib import Path
import sys
import tempfile
import unittest


class MarkdownIndexingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        server_dir = Path(__file__).resolve().parents[1] / "wenkb-server"
        if str(server_dir) not in sys.path:
            sys.path.insert(0, str(server_dir))

    def test_utf8_markdown_is_split_without_encoding_autodetection(self):
        from server.core.tools.dataset_to_vector import file_to_documents

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "资料.md"
            path.write_bytes("# 索引测试\n\n这是 UTF-8 Markdown 内容。".encode("utf-8"))

            documents = file_to_documents(str(path))

        self.assertTrue(documents)
        self.assertIn("UTF-8 Markdown 内容", "\n".join(doc.page_content for doc in documents))
        self.assertEqual(documents[0].metadata["source"], str(path))

    def test_gb18030_markdown_is_decoded_and_split(self):
        from server.core.tools.dataset_to_vector import file_to_documents

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "资料.md"
            path.write_bytes("# 索引测试\n\n这是 GB18030 编码的内容。".encode("gb18030"))

            documents = file_to_documents(str(path))

        self.assertTrue(documents)
        self.assertIn("GB18030 编码的内容", "\n".join(doc.page_content for doc in documents))

    def test_utf8_text_file_uses_the_same_safe_loader(self):
        from server.core.tools.dataset_to_vector import file_to_documents

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "资料.txt"
            path.write_text("普通文本内容", encoding="utf-8")

            documents = file_to_documents(str(path))

        self.assertTrue(documents)
        self.assertIn("普通文本内容", documents[0].page_content)


if __name__ == "__main__":
    unittest.main()
