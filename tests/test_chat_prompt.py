from pathlib import Path
import sys
import unittest


class ChatPromptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        server_dir = Path(__file__).resolve().parents[1] / "wenkb-server"
        if str(server_dir) not in sys.path:
            sys.path.insert(0, str(server_dir))
        from config.prompt import REPOSCHAT_PROMPT_TEMPLATE

        cls.template = REPOSCHAT_PROMPT_TEMPLATE

    def test_prompt_allows_greetings_and_identity_without_retrieval(self):
        self.assertIn("允许日常对话", self.template)
        self.assertIn("询问助手身份或能力时，无需依赖知识片段", self.template)
        self.assertIn("我是 WENKB 知识库专家", self.template)

    def test_prompt_keeps_knowledge_answers_grounded_in_retrieval(self):
        self.assertIn("只能依据<context>中实际提供的知识片段回答", self.template)
        self.assertIn("不得用大模型已有知识补全", self.template)
        self.assertIn("当前知识库没有提供足够依据", self.template)
        self.assertIn("如果没有相关知识片段", self.template)

    def test_prompt_keeps_question_and_context_placeholders(self):
        rendered = self.template.replace("{question}", "你是谁？").replace("{context}", "")
        self.assertIn("你是谁？", rendered)
        self.assertIn("<context>\n\n</context>", rendered)


if __name__ == "__main__":
    unittest.main()
