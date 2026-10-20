from pathlib import Path
import os
import runpy
import site
import sys
import unittest


class ServerBootstrapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        venv_site = root / ".venv" / "Lib" / "site-packages"
        venv_scripts = root / ".venv" / "Scripts"
        if venv_site.exists():
            site.addsitedir(str(venv_site))
            if str(venv_site) not in sys.path:
                sys.path.insert(0, str(venv_site))
        if venv_scripts.exists() and hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(venv_scripts))

    def test_app_module_loads_from_repo_root(self):
        root = Path(__file__).resolve().parents[1]
        app_path = root / "wenkb-server" / "app.py"
        namespace = runpy.run_path(str(app_path), run_name="wenkb_server_app_test")
        self.assertIn("app", namespace)
        dispatchers = [
            middleware.kwargs.get("dispatch")
            for middleware in namespace["app"].user_middleware
        ]
        self.assertIn(namespace["request_identity_middleware"], dispatchers)

    def test_logger_creates_log_dir(self):
        root = Path(__file__).resolve().parents[1]
        server_dir = root / "wenkb-server"
        namespace = runpy.run_path(str(server_dir / "logger.py"), run_name="wenkb_logger_test")
        log_dir = Path(namespace["LOG_DIR"])
        self.assertTrue(log_dir.exists())


if __name__ == "__main__":
    unittest.main()
