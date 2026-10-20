import os
from pathlib import Path
import site
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


ROOT = Path(__file__).resolve().parents[1]
SERVER_DIR = ROOT / "wenkb-server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))
VENV_SITE = ROOT / ".venv" / "Lib" / "site-packages"
if VENV_SITE.exists():
    site.addsitedir(str(VENV_SITE))

ORIGINAL_CWD = Path.cwd()
os.chdir(SERVER_DIR)
try:
    from server.db import DbManager
    from server.model.orm_knb import Base, ChatInfo, ChatMesg, Dataset, ReposInfo
    from server.utils.jwtutils import decode_token, generate_token
    from server.utils.authmiddleware import identity_from_token, request_identity_middleware
    from server.utils.websocketutils import WebsocketManager
    from server.exception.exception import golbal_exception_handlers
    from server.api.knb.ReposInfoApi import ReposInfoApi
    from server.api.knb.DatasetApi import DatasetApi
    from server.api.knb.ChatApi import ChatApi
finally:
    os.chdir(ORIGINAL_CWD)


class FailedExecutionRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jwt_secret = "test-only-secret-with-at-least-32-bytes"

    def setUp(self):
        self.original_session_factory = DbManager.SESSION
        self.temp_dir = tempfile.TemporaryDirectory()
        self.upload_root = Path(self.temp_dir.name) / "uploads"
        self.upload_root.mkdir()
        self.jwt_environment = patch.dict(
            os.environ, {"WENKB_JWT_SECRET": self.jwt_secret}
        )
        self.jwt_environment.start()

        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        DbManager.SESSION = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.app = FastAPI(exception_handlers=golbal_exception_handlers)
        self.app.middleware("http")(request_identity_middleware)
        self.manager = WebsocketManager()
        ReposInfoApi(self.app, self.manager)
        DatasetApi(self.app, self.manager)
        ChatApi(self.app, self.manager)
        self.client = TestClient(self.app)
        self.upload_path_patch = patch(
            "server.core.knb.ReposService.DATASET_UPLOAD_FILE_DIR",
            str(self.upload_root),
        )
        self.upload_path_patch.start()
        self.owner_token = generate_token({"id": "user-a", "name": "A"})
        self.other_token = generate_token({"id": "user-b", "name": "B"})

    def tearDown(self):
        self.client.close()
        self.upload_path_patch.stop()
        DbManager.SESSION = self.original_session_factory
        self.engine.dispose()
        self.jwt_environment.stop()
        self.temp_dir.cleanup()

    def add_repository(self, repos_id="repo-1", owner="user-a", auth_range="prvt"):
        with DbManager.session_scope() as session:
            session.add(ReposInfo(
                reposId=repos_id,
                reposNm="Knowledge base",
                vecModlId="default/m3e-small",
                crtUser=owner,
                authRang=auth_range,
                crtTm="2026-10-21 10:00:00",
            ))

    def row_count(self, model):
        with DbManager.session_scope(True) as session:
            return session.scalar(select(func.count()).select_from(model))

    def test_repository_creation_rejects_empty_name_without_persisting(self):
        response = self.client.post(
            "/knb/repository",
            headers={"token": self.owner_token},
            json={"reposNm": "  \t ", "vecModlId": "default/m3e-small"},
        )

        self.assertEqual(400, response.status_code)
        self.assertIn("名称不能为空", response.json()["msg"])
        self.assertEqual(0, self.row_count(ReposInfo))

    def test_repository_creation_trims_name_and_uses_authenticated_owner(self):
        response = self.client.post(
            "/knb/repository",
            headers={"token": self.owner_token},
            json={"reposNm": "  Valid name  ", "vecModlId": "default/m3e-small"},
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual("Valid name", response.json()["data"]["reposNm"])
        self.assertEqual("user-a", response.json()["data"]["crtUser"])

    def test_repository_identity_and_public_access_are_enforced(self):
        self.add_repository("private-repo", auth_range="prvt")
        self.add_repository("public-repo", auth_range="pblc")

        owner_list = self.client.post(
            "/knb/repository/list", headers={"token": self.owner_token}, json={}
        )
        other_list = self.client.post(
            "/knb/repository/list", headers={"token": self.other_token}, json={}
        )
        self.assertEqual({"private-repo", "public-repo"}, {r["reposId"] for r in owner_list.json()["data"]})
        self.assertEqual(["public-repo"], [r["reposId"] for r in other_list.json()["data"]])

        denied = self.client.get(
            "/knb/repository/private-repo", headers={"token": self.other_token}
        )
        public = self.client.get(
            "/knb/repository/public-repo", headers={"token": self.other_token}
        )
        self.assertEqual(403, denied.status_code)
        self.assertEqual(200, public.status_code)
        self.assertEqual("visit", public.json()["data"]["optAuth"])

        private_write = self.client.put(
            "/knb/repository/name",
            headers={"token": self.other_token},
            json={"reposId": "private-repo", "reposNm": "changed by B"},
        )
        write = self.client.put(
            "/knb/repository/name",
            headers={"token": self.other_token},
            json={"reposId": "public-repo", "reposNm": "changed by B"},
        )
        self.assertEqual(403, private_write.status_code)
        self.assertEqual(403, write.status_code)
        with DbManager.session_scope(True) as session:
            self.assertEqual("Knowledge base", session.get(ReposInfo, "private-repo").reposNm)
            self.assertEqual("Knowledge base", session.get(ReposInfo, "public-repo").reposNm)

    def test_missing_and_invalid_tokens_do_not_receive_a_shared_user_identity(self):
        missing = self.client.post("/knb/repository/list", json={})
        invalid = self.client.post(
            "/knb/repository/list", headers={"token": "different-token"}, json={}
        )

        self.assertEqual(401, missing.status_code)
        self.assertEqual(401, invalid.status_code)
        self.assertIsNone(identity_from_token("different-token"))
        self.assertEqual("user-a", identity_from_token(self.owner_token)["id"])

    def test_jwt_signing_fails_closed_for_a_short_secret(self):
        with patch.dict(os.environ, {"WENKB_JWT_SECRET": "short"}):
            with self.assertRaisesRegex(ValueError, "at least 32 bytes"):
                generate_token({"id": "user-a"})
            self.assertFalse(decode_token("untrusted-token"))

    def test_link_import_validates_the_entire_batch_before_saving(self):
        self.add_repository()
        response = self.client.post(
            "/knb/dataset/upload/link",
            headers={"token": self.owner_token},
            json={
                "reposId": "repo-1",
                "links": [
                    {"url": "https://example.com/article", "title": "Valid"},
                    {"url": "not-a-valid-url"},
                ],
            },
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual(0, self.row_count(Dataset))

    def test_valid_link_import_and_title_lookup_still_work(self):
        from server.api.knb import DatasetApi as dataset_api_module

        self.add_repository()
        urls = ["https://example.com/a", "http://example.org/b"]
        with patch.object(dataset_api_module, "get_webpage_title", side_effect=["A", "B"]):
            titles = self.client.post(
                "/knb/dataset/links/title",
                headers={"token": self.owner_token},
                json=urls,
            )
        self.assertEqual({urls[0]: "A", urls[1]: "B"}, titles.json()["data"])

        imported = self.client.post(
            "/knb/dataset/upload/link",
            headers={"token": self.owner_token},
            json={"reposId": "repo-1", "links": [{"url": url} for url in urls]},
        )
        self.assertEqual(200, imported.status_code)
        with DbManager.session_scope(True) as session:
            self.assertEqual(sorted(urls), session.scalars(select(Dataset.filePath).order_by(Dataset.filePath)).all())

    def test_invalid_link_title_lookup_is_rejected_without_fetching(self):
        from server.api.knb import DatasetApi as dataset_api_module

        with patch.object(dataset_api_module, "get_webpage_title") as get_title:
            responses = [
                self.client.post(
                    "/knb/dataset/links/title",
                    headers={"token": self.owner_token},
                    json=[url],
                )
                for url in (
                    "javascript:alert(1)",
                    "https://example.com:",
                    "https://user:password@example.com",
                )
            ]
        self.assertEqual([400, 400, 400], [response.status_code for response in responses])
        get_title.assert_not_called()

    def test_repository_deletion_removes_uploads_but_not_link_targets(self):
        self.add_repository()
        uploaded = self.upload_root / "document.pdf"
        uploaded.write_bytes(b"test upload")
        link_target = self.upload_root / "external-link-placeholder"
        link_target.write_bytes(b"not owned by link dataset")
        with DbManager.session_scope() as session:
            session.add_all([
                Dataset(dtsetId="uploaded", reposId="repo-1", fileTyp="pdf", filePath=str(uploaded)),
                Dataset(dtsetId="linked", reposId="repo-1", fileTyp="link", filePath=str(link_target)),
            ])

        with patch("server.core.knb.ReposService.vector_delete_collection"):
            response = self.client.delete(
                "/knb/repository/repo-1", headers={"token": self.owner_token}
            )

        self.assertEqual(200, response.status_code)
        self.assertFalse(uploaded.exists())
        self.assertTrue(link_target.exists())
        self.assertEqual(0, self.row_count(ReposInfo))
        self.assertEqual(0, self.row_count(Dataset))

    def test_vector_delete_failure_restores_staged_upload_and_keeps_rows(self):
        from server.core.knb.ReposService import ReposService

        self.add_repository()
        uploaded = self.upload_root / "document.pdf"
        uploaded.write_bytes(b"test upload")
        with DbManager.session_scope() as session:
            session.add(Dataset(
                dtsetId="uploaded", reposId="repo-1", fileTyp="pdf", filePath=str(uploaded)
            ))

        with patch("server.core.knb.ReposService.vector_delete_collection", side_effect=RuntimeError("vector store unavailable")):
            with self.assertRaisesRegex(RuntimeError, "vector store unavailable"):
                ReposService().remove_repository_by_id("repo-1")

        self.assertEqual(b"test upload", uploaded.read_bytes())
        self.assertEqual(1, self.row_count(ReposInfo))
        self.assertEqual(1, self.row_count(Dataset))
        self.assertEqual([], list(self.upload_root.glob(".repo-1.delete-*")))

    def test_llm_initialization_failure_is_persisted_and_readable_in_history(self):
        from server.core.tools import ask_to_llm as ask_module
        from server.model.entity_knb import ChatMesg as ChatMesgEntity, ReposSetting

        self.add_repository()
        with DbManager.session_scope() as session:
            session.add(ChatInfo(
                chatId="chat-1", reposId="repo-1", chatTtl="Test", crtUser="user-a"
            ))

        message = ChatMesgEntity(
            mesgId="assistant-1",
            reposId="repo-1",
            chatId="chat-1",
            mesgTyp="text",
            crtRole="sys",
        )
        with patch.object(ask_module, "get_user_llm_client", side_effect=RuntimeError("model unavailable")):
            events = list(ask_module.ask_to_llm_stream(
                setting=ReposSetting(reposId="repo-1", llmTptur=0.2),
                chatMesg=message,
                question="Question",
                userId="user-a",
            ))

        self.assertEqual(2, len(events))
        history = self.client.post(
            "/knb/chat/message/list",
            headers={"token": self.owner_token},
            json={"chatId": "chat-1"},
        )
        self.assertEqual(200, history.status_code)
        self.assertEqual("很抱歉，似乎发生了错误", history.json()["data"][0]["mesgCntnt"])


if __name__ == "__main__":
    unittest.main()
