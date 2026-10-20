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


class TestScorebookHandoffTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workbook = load_workbook(WORKBOOK_PATH, data_only=False)
        cls.calculated_workbook = load_workbook(WORKBOOK_PATH, data_only=True)

    def test_artifacts_are_archived_as_an_in_progress_package(self):
        self.assertTrue(WORKBOOK_PATH.is_file())
        self.assertTrue(BUILDER_PATH.is_file())
        self.assertTrue(HANDOFF_PATH.is_file())
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
        self.assertEqual("TC-WKB-001", cases.cell(5, 1).value)
        self.assertEqual("TC-WKB-048", cases.cell(52, 1).value)
        self.assertEqual(48, sum(1 for row in range(5, 53) if cases.cell(row, 1).value))

        plan_counts = Counter(
            str(cases.cell(row, 2).value).split(" / ")[0]
            for row in range(5, 53)
        )
        self.assertEqual(
            {f"TP-{index:03d}": 4 for index in range(1, 13)},
            plan_counts,
        )

    def test_execution_fields_remain_unexecuted_and_blank(self):
        cases = self.workbook["测试项目"]
        statuses = Counter(cases.cell(row, 9).value for row in range(5, 53))
        self.assertEqual({"未执行": 48}, statuses)

        for row in range(5, 53):
            for column in (8, 10, 11, 12):
                self.assertIn(cases.cell(row, column).value, (None, ""))

    def test_run_summary_formulas_and_saved_values_match_unexecuted_state(self):
        formulas = self.workbook["运行"]
        calculated = self.calculated_workbook["运行"]
        self.assertEqual("=COUNTA('测试项目'!A5:A52)", formulas["B10"].value)
        self.assertEqual(
            '=COUNTIFS(\'测试项目\'!I5:I52,"未执行")',
            formulas["B14"].value,
        )
        self.assertIn('IF(B16=0,"待执行"', formulas["B17"].value)
        self.assertEqual([48, 0, 0, 0, 48, 0, 0], [calculated.cell(row, 2).value for row in range(10, 17)])
        self.assertEqual("待执行", calculated["B17"].value)
        self.assertEqual("未完成：请先执行全部用例", calculated["B19"].value)

    def test_handoff_document_describes_scope_and_resume_checks(self):
        text = HANDOFF_PATH.read_text(encoding="utf-8")
        for required in (
            "执行前草案",
            "后续计划",
            "Artifact Tool",
            "视觉复核",
            "48 条用例",
            "没有执行任何 WenKB 产品功能测试",
        ):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
