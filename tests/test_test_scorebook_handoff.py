from collections import Counter
from pathlib import Path
import unittest

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "wenkb-test-book-in-progress"
WORKBOOK_PATH = (
    OUTPUT_DIR / "第14小组_基于大模型的个人知识库系统_测试成绩书.xlsx"
)
BUILDER_PATH = OUTPUT_DIR / "scripts" / "build_wenkb_test_book.mjs"
HANDOFF_PATH = ROOT / "docs" / "test_scorebook_handoff.md"
MANUAL_GUIDE_PATH = ROOT / "docs" / "test_scorebook_manual_run.md"
FOLLOWUP_PATH = ROOT / "docs" / "test_execution_followup.md"
EVIDENCE_README_PATH = OUTPUT_DIR / "evidence" / "README.md"


class TestScorebookHandoffTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workbook = load_workbook(WORKBOOK_PATH, data_only=False)
        cls.calculated_workbook = load_workbook(WORKBOOK_PATH, data_only=True)

    def test_artifacts_are_archived_as_an_in_progress_package(self):
        self.assertTrue(WORKBOOK_PATH.is_file())
        self.assertTrue(BUILDER_PATH.is_file())
        self.assertTrue(HANDOFF_PATH.is_file())
        self.assertTrue(MANUAL_GUIDE_PATH.is_file())
        self.assertTrue(EVIDENCE_README_PATH.is_file())
        self.assertFalse((ROOT / "outputs" / "wenkb-test-book-final").exists())
        self.assertFalse(
            WORKBOOK_PATH.with_suffix(WORKBOOK_PATH.suffix + ".inspect.ndjson").exists()
        )

        builder = BUILDER_PATH.read_text(encoding="utf-8")
        self.assertIn('"wenkb-test-book-in-progress"', builder)

    def test_workbook_sheets_and_plan_coverage_are_preserved(self):
        self.assertEqual(
            ["文件封面", "测试项目", "UI界面", "运行"],
            self.workbook.sheetnames,
        )

        cases = self.workbook["测试项目"]
        case_rows = [
            row
            for row in range(1, cases.max_row + 1)
            if str(cases.cell(row, 1).value or "").startswith("TC-")
        ]
        self.assertEqual("TC-WKB-001", cases.cell(case_rows[0], 1).value)
        self.assertEqual("TC-WKB-048", cases.cell(case_rows[-1], 1).value)
        self.assertEqual(48, len(case_rows))

        plan_counts = Counter(
            str(cases.cell(row, 2).value).split(" / ")[0]
            for row in case_rows
        )
        self.assertEqual(
            {f"TP-{index:03d}": 4 for index in range(1, 13)},
            plan_counts,
        )

    def test_execution_fields_match_the_recorded_test_results(self):
        cases = self.workbook["测试项目"]
        case_rows = [
            row
            for row in range(1, cases.max_row + 1)
            if str(cases.cell(row, 1).value or "").startswith("TC-")
        ]
        statuses = Counter(cases.cell(row, 9).value for row in case_rows)
        self.assertEqual({"通过": 26, "阻塞": 22}, statuses)

        regression_defects = {
            "TC-WKB-008": "DEF-WKB-005",
            "TC-WKB-010": "DEF-WKB-002",
            "TC-WKB-015": "DEF-WKB-003",
            "TC-WKB-038": "DEF-WKB-004",
            "TC-WKB-041": "DEF-WKB-001",
            "TC-WKB-042": "DEF-WKB-001",
            "TC-WKB-043": "DEF-WKB-001",
            "TC-WKB-044": "DEF-WKB-001",
        }

        for row in case_rows:
            case_id = cases.cell(row, 1).value
            self.assertTrue(cases.cell(row, 8).value)
            self.assertIn(cases.cell(row, 11).value, {"自动化执行", "李子昂", "杨帆"})
            self.assertIsNotNone(cases.cell(row, 10).value)
            if case_id in regression_defects:
                self.assertEqual("通过", cases.cell(row, 9).value)
                self.assertEqual(regression_defects[case_id], cases.cell(row, 12).value)
                self.assertIn("tests.test_failed_execution_regressions", cases.cell(row, 13).value)
            else:
                self.assertIsNone(cases.cell(row, 12).value)

    def test_run_summary_formulas_and_saved_values_match_execution_results(self):
        formulas = self.workbook["运行"]
        self.assertIsNone(formulas["B14"].value)
        self.assertEqual("WenKB 浏览器工作区与主导航", formulas["B19"].value)

    def test_runtime_evidence_is_separate_and_waits_for_manual_execution(self):
        run = self.workbook["运行"]
        self.assertEqual("项目实际运行情况（截图已粘贴；详见用例执行状态）", run["A36"].value)
        self.assertIn("8 条缺陷用例已按隔离 API 自动回归结果回填通过", run["A37"].value)
        self.assertEqual("运行界面截图（完成对应步骤后粘贴；当前为空白证据位）", run["A25"].value)
        self.assertEqual([f"S{index:02d}" for index in range(1, 7)], [run.cell(row, 1).value for row in range(18, 24)])
        self.assertEqual(6, len(run._images))

    def test_cover_and_formula_cells_are_consistent(self):
        cover = self.workbook["文件封面"]
        run = self.workbook["运行"]
        self.assertEqual("8 条缺陷用例已按自动化回归结果回填；22 条环境阻塞仍待手动执行", cover["B14"].value)
        self.assertIsNotNone(cover["B15"].value)
        self.assertEqual("26 通过，0 失败，22 阻塞；含 8 条隔离自动化回归通过，截图已粘贴", cover["B18"].value)
        self.assertIn("test_execution_followup.md", run["A37"].value)
        errors = [
            f"{sheet.title}!{cell.coordinate}"
            for sheet in self.calculated_workbook.worksheets
            for row in sheet.iter_rows()
            for cell in row
            if cell.data_type == "e"
        ]
        self.assertEqual([], errors)

    def test_manual_run_guide_protects_existing_data_and_defines_screenshots(self):
        text = MANUAL_GUIDE_PATH.read_text(encoding="utf-8")
        for required in (
            "隔离副本",
            "resources",
            "16088",
            "11420",
            "/health",
            "S01",
            "S06",
            "A55:I61",
            "A64:I70",
            "A73:I79",
            "A82:I88",
            "A91:I97",
            "A100:I106",
            "48 条",
            "API Key",
            "WENKB_JWT_SECRET",
            "scorebook-test-user",
        ):
            self.assertIn(required, text)

    def test_handoff_document_describes_scope_and_resume_checks(self):
        text = HANDOFF_PATH.read_text(encoding="utf-8")
        for required in (
            "48 条用例已执行",
            "后续计划",
            "Artifact Tool",
            "视觉复核",
            "48 条用例",
            "26 通过",
            "22 阻塞",
            "DEF-WKB-001",
            "项目实际运行情况",
            "test_scorebook_manual_run.md",
        ):
            self.assertIn(required, text)

    def test_followup_register_preserves_failed_and_blocked_diagnostics(self):
        text = FOLLOWUP_PATH.read_text(encoding="utf-8")
        for required in (
            "TC-WKB-008",
            "TC-WKB-010",
            "TC-WKB-015",
            "TC-WKB-038",
            "TC-WKB-041",
            "TC-WKB-042",
            "TC-WKB-043",
            "TC-WKB-044",
            "TC-WKB-016",
            "TC-WKB-047",
            "DEF-WKB-005",
            "DEF-WKB-001",
            "26 通过",
            "22 条阻塞",
        ):
            self.assertIn(required, text)

        cases = self.workbook["测试项目"]
        pending = {
            cases.cell(row, 1).value
            for row in range(1, cases.max_row + 1)
            if cases.cell(row, 9).value == "未执行（待复测）"
        }
        self.assertEqual(set(), pending)
        regression_passed = {
            cases.cell(row, 1).value
            for row in range(1, cases.max_row + 1)
            if cases.cell(row, 9).value == "通过"
            and "tests.test_failed_execution_regressions" in str(cases.cell(row, 13).value)
        }
        self.assertEqual(
            {
                "TC-WKB-008", "TC-WKB-010", "TC-WKB-015", "TC-WKB-038",
                "TC-WKB-041", "TC-WKB-042", "TC-WKB-043", "TC-WKB-044",
            },
            regression_passed,
        )

    def test_failure_retest_results_and_remaining_blockers_are_explicit(self):
        text = FOLLOWUP_PATH.read_text(encoding="utf-8")
        for required in (
            "2.1 2026-10-21 修复与回归",
            "tests.test_failed_execution_regressions",
            "11 项通过",
            "2.2 2026-10-21 缺陷修复后自动化复测",
            "Python 全量测试",
            "6 项通过",
            "工作簿已填写对应实测结果、测试日期、执行者、缺陷编号和测试模块证据",
            "26 条通过、22 条阻塞",
            "不代表完整 UI、模型问答、向量一致性或端到端手工步骤均已完成",
            "WENKB_JWT_SECRET",
            "22 条阻塞仍依赖真实 LLM",
        ):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
