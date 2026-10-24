from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DevelopmentEnvironmentSetupTest(unittest.TestCase):
    def test_setup_guide_covers_startup_database_credentials_and_video(self):
        guide = ROOT / "docs" / "development_environment_setup.md"
        text = guide.read_text(encoding="utf-8")

        required_sections = [
            "需要准备的软件",
            "获取代码并安装依赖",
            "数据库初始化与脚本",
            "启动服务",
            "登录、密码和模型凭据",
            "首次运行验收",
            "常见问题",
            "开发者手册",
            "用户手册",
            "后台任务与数据集状态",
            "用户常见问题",
            "Markdown/TXT 导入后索引失败并提示编码检测异常",
        ]
        for section in required_sections:
            self.assertIn(section, text)

        for term in [
            "Python 3.11.5",
            "npm ci",
            "npm run dev",
            "16088",
            "11420",
            "SQLite",
            "ddl/0.sql",
            "WENKB_JWT_SECRET",
            "API Key",
            "没有预置登录账号或默认密码",
        ]:
            self.assertIn(term, text)

        self.assertIn(
            "docs/development_environment_setup.md",
            (ROOT / "AGENTS.md").read_text(encoding="utf-8"),
        )
        self.assertFalse((ROOT / "docs" / "wenkb_operation_guide.md").exists())


if __name__ == "__main__":
    unittest.main()
