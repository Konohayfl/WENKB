from pathlib import Path
import json
import os
import runpy
import sys
import unittest
from unittest.mock import Mock, patch


class CodeMaintenanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        server_dir = root / "wenkb-server"
        if str(server_dir) not in sys.path:
            sys.path.insert(0, str(server_dir))

    def test_health_endpoint_is_registered_and_reports_database(self):
        root = Path(__file__).resolve().parents[1]
        server_dir = root / "wenkb-server"
        original_cwd = Path.cwd()
        os.chdir(server_dir)
        try:
            with patch("server.db.DbUpgrade.upgrade_db"):
                namespace = runpy.run_path(
                    str(server_dir / "app.py"),
                    run_name="wenkb_server_health_test",
                )
        finally:
            os.chdir(original_cwd)
        routes = {
            route.path: route
            for route in namespace["app"].routes
            if hasattr(route, "path")
        }
        self.assertIn("/health", routes)
        response = routes["/health"].endpoint()
        self.assertTrue(response["success"])
        self.assertEqual(response["data"]["status"], "ok")
        self.assertEqual(response["data"]["database"], "ok")

    def test_retrieval_sources_include_stable_quote_identity(self):
        from langchain_core.documents import Document
        from server.core.tools.ask_to_llm import prob_related_documents_and_score

        sources = prob_related_documents_and_score([
            (
                Document(
                    page_content="片段内容",
                    metadata={
                        "dtsetId": "dataset-1",
                        "dtsetNm": "资料",
                        "fileNm": "资料.md",
                        "fileTyp": "md",
                        "chkId": "chunk-1",
                    },
                ),
                0.12,
            )
        ])

        self.assertEqual(sources[0]["sourceObjectType"], "chunk")
        self.assertEqual(sources[0]["sourceObjectId"], "chunk-1")
        self.assertEqual(sources[0]["chkId"], "chunk-1")
        self.assertEqual(sources[0]["content"], "片段内容")

    def test_message_quotes_are_persisted_as_snapshots(self):
        from server.core.tools.ask_to_llm import save_message_quotes
        from server.model.entity_knb import ChatMesg

        session = Mock()
        context = Mock()
        context.__enter__ = Mock(return_value=session)
        context.__exit__ = Mock(return_value=False)
        message = ChatMesg(
            mesgId="message-1",
            chatId="chat-1",
            reposId="repo-1",
        )
        sources = [{
            "dtsetId": "dataset-1",
            "dtsetNm": "资料",
            "fileNm": "资料.md",
            "fileTyp": "md",
            "score": 0.25,
            "content": "引用快照",
            "sourceObjectType": "chunk",
            "sourceObjectId": "chunk-1",
            "chkId": "chunk-1",
        }]

        with patch("server.core.tools.ask_to_llm.session_scope", return_value=context):
            save_message_quotes(message, sources)

        session.execute.assert_called_once()
        session.add_all.assert_called_once()
        quote = session.add_all.call_args.args[0][0]
        self.assertEqual(quote.mesgId, "message-1")
        self.assertEqual(quote.dtsetId, "dataset-1")
        self.assertEqual(quote.srcObjId, "chunk-1")
        self.assertEqual(quote.content, "引用快照")
        self.assertEqual(quote.quoteOrder, 0)

    def test_stream_failure_persists_fallback_message(self):
        from server.core.tools.ask_to_llm import ask_to_llm_stream
        from server.model.entity_knb import ChatMesg, ReposSetting

        session = Mock()
        context = Mock()
        context.__enter__ = Mock(return_value=session)
        context.__exit__ = Mock(return_value=False)
        session.get.return_value = None
        session.merge = Mock()
        session.execute = Mock()
        session.add_all = Mock()

        fake_client = Mock()

        def stream(_):
            yield "部分回答"
            raise RuntimeError("boom")

        fake_client.stream.side_effect = stream

        setting = ReposSetting(
            reposId="repo-1",
            llmTptur=0.2,
            maxHist=4,
            maxCtx=4,
            smlrTrval=0.5,
            topK=4,
        )
        chat_mesg = ChatMesg(
            mesgId="message-1",
            reposId="repo-1",
            chatId="chat-1",
        )

        with patch("server.core.tools.ask_to_llm.get_user_llm_client", return_value=fake_client), patch(
            "server.core.tools.ask_to_llm.get_question_prompts_and_sources",
            return_value=("prompt", []),
        ), patch("server.core.tools.ask_to_llm.session_scope", return_value=context):
            outputs = list(
                ask_to_llm_stream(
                    setting=setting,
                    chatMesg=chat_mesg,
                    question="问题",
                    userId="user-1",
                )
            )

        self.assertIn("chat_message_error", outputs[1])
        self.assertEqual(
            outputs[-2],
            json.dumps(
                {"type": "chat_message_chunk", "data": "很抱歉，似乎发生了错误"},
                ensure_ascii=False,
            ),
        )
        self.assertIn("chat_message_quote", outputs[-1])
        self.assertEqual(session.merge.call_args.args[0].mesgCntnt, "很抱歉，似乎发生了错误")

    def test_chat_history_is_used_without_a_separate_llm_rewrite_call(self):
        from server.core.tools.ask_to_llm import ask_to_llm_stream
        from server.model.entity_knb import ChatMesg, ReposSetting

        history = [ChatMesg(crtRole="usr", mesgCntnt="解释一下向量检索")]
        fake_client = Mock()
        fake_client.stream.return_value = iter(["向量检索回答"])
        setting = ReposSetting(
            reposId="repo-1", llmTptur=0.2, maxHist=4, maxCtx=4,
            smlrTrval=0.5, topK=4,
        )
        message = ChatMesg(mesgId="message-2", reposId="repo-1", chatId="chat-1")

        with patch("server.core.tools.ask_to_llm.get_user_llm_client", return_value=fake_client), patch(
            "server.core.tools.ask_to_llm.get_question_prompts_and_sources",
            return_value=("answer prompt", []),
        ) as retrieval, patch("server.core.tools.ask_to_llm.save_message_quotes"), patch(
            "server.core.tools.ask_to_llm.persist_chat_message"
        ):
            list(ask_to_llm_stream(setting, message, "那它有什么优势？", "user-1", history))

        fake_client.invoke.assert_not_called()
        retrieval.assert_called_once_with("repo-1", "那它有什么优势？", setting, history)
        fake_client.stream.assert_called_once_with("answer prompt")

    def test_history_context_is_added_to_final_prompt(self):
        from langchain_core.documents import Document
        from server.core.tools.ask_to_llm import generate_llm_prompts
        from server.model.entity_knb import ChatMesg

        prompt = generate_llm_prompts(
            "那它有什么优势？",
            [(Document(page_content="向量检索片段", metadata={}), 0.1)],
            [ChatMesg(crtRole="usr", mesgCntnt="解释一下向量检索")],
        )

        self.assertIn("解释一下向量检索", prompt)
        self.assertIn("当前问题：那它有什么优势？", prompt)
        self.assertIn("仅用于理解当前问题，不作为事实依据", prompt)
        self.assertIn("向量检索片段", prompt)

    def test_quote_migration_and_schema_version_are_aligned(self):
        root = Path(__file__).resolve().parents[1]
        common = (root / "wenkb-server" / "config" / "common.py").read_text(
            encoding="utf-8"
        )
        migration = (
            root / "wenkb-server" / "server" / "db" / "upgrade" / "ddl" / "5.sql"
        ).read_text(encoding="utf-8")
        fresh_install = (
            root / "wenkb-server" / "server" / "db" / "upgrade" / "ddl" / "0.sql"
        ).read_text(encoding="utf-8")
        upgrade_baseline = (
            root / "wenkb-server" / "server" / "db" / "upgrade" / "ddl" / "2.sql"
        ).read_text(encoding="utf-8")

        self.assertIn("DB_SCHEMA_VERSION = 6", common)
        self.assertIn('ALTER TABLE "t_knb_dataset_index_error" RENAME TO "t_knb_dataset_index_error_old"', migration)
        self.assertIn('"error_id" text(32) NOT NULL', migration)
        self.assertIn("idx_knb_dataset_index_error_query", migration)
        self.assertIn('"error_id" text(32) NOT NULL', fresh_install)
        self.assertIn("idx_knb_dataset_index_error_query", fresh_install)
        self.assertIn('"error_id" text(32) NOT NULL', upgrade_baseline)
        self.assertIn("idx_knb_dataset_index_error_query", upgrade_baseline)
        auth_migration = (
            root / "wenkb-server" / "server" / "db" / "upgrade" / "ddl" / "6.sql"
        ).read_text(encoding="utf-8")
        self.assertIn('CREATE TABLE IF NOT EXISTS "t_sys_user"', auth_migration)
        self.assertIn("uq_sys_user_username", auth_migration)

    def test_model_secret_encryption_round_trip_uses_valid_aes_parameters(self):
        from server.utils.secretutils import AES_IV, AES_KEY, aes_decrypt, aes_encrypt

        self.assertIn(len(AES_KEY.encode("utf-8")), (16, 24, 32))
        self.assertEqual(len(AES_IV.encode("utf-8")), 16)
        encrypted = aes_encrypt("test-tongyi-api-key")
        self.assertNotEqual(encrypted, "test-tongyi-api-key")
        self.assertEqual(aes_decrypt(encrypted), "test-tongyi-api-key")

    def test_openai_compatible_chat_clients_initialize_for_all_providers(self):
        from server.core.tools.llm_client_tools import LLMClient

        provider_configs = {
            "openai": ("gpt-4o-mini", "https://api.openai.com/v1"),
            "deepseek": ("deepseek-chat", "https://api.deepseek.com/v1"),
            "moonshot": ("moonshot-v1-8k", "https://api.moonshot.cn/v1"),
            "tongyi": (
                "qwen-plus",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
            "zhipuai": (
                "glm-4-flash",
                "https://open.bigmodel.cn/api/paas/v4",
            ),
            "nvidia": (
                "meta/llama-3.1-405b-instruct",
                "https://integrate.api.nvidia.com/v1",
            ),
        }

        for provider, (model, base_url) in provider_configs.items():
            with self.subTest(provider=provider), patch(
                "server.core.tools.llm_client_tools.get_model_arguments",
                return_value={
                    "provider": provider,
                    "model": model,
                    "base_url": base_url,
                    "api_key": "test-api-key",
                },
            ):
                llm_client = LLMClient(userId="user-1")

            self.assertIsNotNone(llm_client.client.root_client)
            self.assertIsNotNone(llm_client.client.root_async_client)
            llm_client.client.root_client.close()

    def test_openai_compatible_embedding_clients_initialize_for_all_providers(self):
        from server.core.tools.llm_client_tools import EmbeddingFunction

        provider_configs = {
            "openai": ("text-embedding-3-small", "https://api.openai.com/v1"),
            "deepseek": ("deepseek-embedding", "https://api.deepseek.com/v1"),
            "moonshot": ("embedding-v1", "https://api.moonshot.cn/v1"),
            "tongyi": (
                "text-embedding-v2",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
            "zhipuai": (
                "embedding-3",
                "https://open.bigmodel.cn/api/paas/v4",
            ),
            "nvidia": (
                "nvidia/embed-qa-4",
                "https://integrate.api.nvidia.com/v1",
            ),
        }

        for provider, (model, base_url) in provider_configs.items():
            with self.subTest(provider=provider), patch(
                "server.core.tools.llm_client_tools.get_model_arguments",
                return_value={
                    "provider": provider,
                    "model": model,
                    "base_url": base_url,
                    "api_key": "test-api-key",
                },
            ):
                embedding = EmbeddingFunction(userId="user-1")

            self.assertIsNotNone(embedding.function.client)
            self.assertIsNotNone(embedding.function.async_client)

    def test_local_embedding_model_validation_rejects_lfs_pointer(self):
        from server.core.tools.llm_client_tools import validate_local_embedding_model

        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            model_dir = Path(temp_dir)
            (model_dir / "pytorch_model.bin").write_bytes(
                b"version https://git-lfs.github.com/spec/v1\n"
            )

            with self.assertRaisesRegex(RuntimeError, "Git LFS"):
                validate_local_embedding_model(str(model_dir))

    def test_embedding_dependency_versions_are_pinned_for_windows_runtime(self):
        root = Path(__file__).resolve().parents[1]
        requirements = (
            root / "wenkb-server" / "requirements.txt"
        ).read_text(encoding="utf-8")

        self.assertIn("torch==2.3.1", requirements)
        self.assertIn("fsspec==2024.6.1", requirements)

    def test_handoff_records_failure_fixes_and_authentication_prerequisite(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "docs" / "code_maintenance_handoff.md").read_text(
            encoding="utf-8"
        )

        for required in (
            "tests.test_failed_execution_regressions",
            "70 项全量 Python 测试通过",
            "前端测试 6 项全部通过",
            "生产构建成功",
            "测试成绩书阶段已完成",
            "WENKB_JWT_SECRET",
            "WebSocket 拒绝无效凭证",
            "TC-WKB-029、030、032",
        ):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
