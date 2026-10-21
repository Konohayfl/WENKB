import os
from pathlib import Path
import site
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.documents import Document
from sqlalchemy import create_engine
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
    from server.model.orm_knb import Base, Dataset, ReposInfo, ReposSetting
    from server.model.entity_knb import ReposSetting as ReposSettingEntity
    from server.utils.jwtutils import generate_token
    from server.utils.authmiddleware import request_identity_middleware
    from server.utils.websocketutils import WebsocketManager
    from server.exception.exception import golbal_exception_handlers
    from server.api.knb.SearchApi import SearchApi
    from server.core.tools import ask_to_llm
finally:
    os.chdir(ORIGINAL_CWD)


class SearchRegressionTest(unittest.TestCase):
    def setUp(self):
        self.original_session_factory = DbManager.SESSION
        self.jwt_environment = patch.dict(
            os.environ,
            {"WENKB_JWT_SECRET": "test-only-secret-with-at-least-32-bytes"},
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
        SearchApi(self.app, self.manager)
        self.client = TestClient(self.app)
        self.owner_token = generate_token({"id": "user-a", "name": "A"})
        with DbManager.session_scope() as session:
            session.add(ReposInfo(
                reposId="repo-1",
                reposNm="Knowledge base",
                vecModlId="default/m3e-small",
                crtUser="user-a",
                authRang="prvt",
                crtTm="2026-10-21 10:00:00",
            ))

    def tearDown(self):
        self.client.close()
        DbManager.SESSION = self.original_session_factory
        self.engine.dispose()
        self.jwt_environment.stop()

    def test_search_uses_settings_threshold_and_active_ready_datasets(self):
        with DbManager.session_scope() as session:
            session.add(ReposSetting(reposId="repo-1", topK=2, smlrTrval=0.45))
            session.add_all([
                Dataset(dtsetId="eligible", reposId="repo-1", idxSts="ready", enbSts="enb"),
                Dataset(dtsetId="disabled", reposId="repo-1", idxSts="ready", enbSts="une"),
                Dataset(dtsetId="not-ready", reposId="repo-1", idxSts="index", enbSts="enb"),
                Dataset(dtsetId="other-repo", reposId="repo-2", idxSts="ready", enbSts="enb"),
            ])

        docs = [
            (Document(page_content="accepted", metadata={"dtsetId": "eligible", "dtsetNm": "Ready", "fileTyp": "md"}), 0.2),
            (Document(page_content="over threshold", metadata={"dtsetId": "eligible", "dtsetNm": "Ready", "fileTyp": "md"}), 0.5),
            (Document(page_content="disabled dataset", metadata={"dtsetId": "disabled", "dtsetNm": "Disabled", "fileTyp": "md"}), 0.1),
        ]
        with patch("server.api.knb.SearchApi.get_related_docs_by_repos_id", return_value=docs) as retrieve:
            response = self.client.post(
                "/knb/search",
                headers={"token": self.owner_token},
                json={"reposId": "repo-1", "searchTxt": "needle", "noHist": True},
            )

        self.assertEqual(200, response.status_code)
        self.assertEqual(["accepted"], [item["content"] for item in response.json()["data"]])
        _, kwargs = retrieve.call_args
        self.assertEqual("needle", kwargs["question"])
        self.assertEqual(2, kwargs["setting"].topK)
        self.assertEqual(0.45, kwargs["setting"].smlrTrval)
        self.assertEqual({"eligible"}, kwargs["dataset_ids"])

    def test_retriever_passes_top_k_and_dataset_metadata_filter(self):
        class VectorStore:
            def __init__(self):
                self.call = None

            def similarity_search_with_score(self, question, k, filter=None):
                self.call = (question, k, filter)
                return []

        vector_store = VectorStore()
        with patch.object(ask_to_llm, "get_or_build_vector_db", return_value=vector_store):
            ask_to_llm.get_related_docs_by_repos_id(
                reposId="repo-1",
                question="needle",
                setting=ReposSettingEntity(topK=3, smlrTrval=0.4),
                dataset_ids={"dataset-b", "dataset-a"},
            )

        self.assertEqual(
            ("needle", 3, {"dtsetId": {"$in": ["dataset-a", "dataset-b"]}}),
            vector_store.call,
        )

    def test_retriever_skips_vector_search_when_no_dataset_is_eligible(self):
        vector_store = object()
        with patch.object(ask_to_llm, "get_or_build_vector_db", return_value=vector_store):
            with patch.object(ask_to_llm, "get_related_docs_with_score") as search:
                result = ask_to_llm.get_related_docs_by_repos_id(
                    reposId="repo-1",
                    question="needle",
                    setting=ReposSettingEntity(topK=3),
                    dataset_ids=set(),
                )

        self.assertEqual([], result)
        search.assert_not_called()

    def test_search_result_routes_to_the_selected_dataset(self):
        search_view = (
            ROOT / "wenkb-client" / "src" / "views" / "main" / "Search.vue"
        ).read_text(encoding="utf-8")
        dataset_view = (
            ROOT / "wenkb-client" / "src" / "views" / "main" / "repository" / "Dataset.vue"
        ).read_text(encoding="utf-8")

        self.assertIn("@click=\"onResultClick(result)\"", search_view)
        self.assertIn("path: '/main/repository/detail'", search_view)
        self.assertIn("dtsetId: result.srcId", search_view)
        self.assertIn("route.query.dtsetId", dataset_view)
        self.assertIn("/knb/dataset/list", dataset_view)
        self.assertIn("selectedId.value = dataset.dtsetId", dataset_view)


if __name__ == "__main__":
    unittest.main()
