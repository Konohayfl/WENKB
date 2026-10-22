from collections import Counter
from datetime import datetime
from pathlib import Path
import unittest

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "wenkb-test-book-in-progress"
WORKBOOK_PATH = (
    OUTPUT_DIR / "第14小组_基于大模型的个人知识库系统_测试成绩书.xlsx"
)
BUILDER_PATH = OUTPUT_DIR / "scripts" / "build_wenkb_test_book.mjs"
STATIC_REVIEW_CASES = {
    "TC-WKB-016": "通过",
    "TC-WKB-018": "通过",
    "TC-WKB-019": "通过",
    "TC-WKB-020": "通过",
    "TC-WKB-021": "通过",
    "TC-WKB-022": "通过",
    "TC-WKB-023": "通过",
    "TC-WKB-024": "通过",
    "TC-WKB-025": "通过",
    "TC-WKB-026": "通过",
    "TC-WKB-027": "通过",
    "TC-WKB-028": "通过",
    "TC-WKB-029": "通过",
    "TC-WKB-030": "通过",
    "TC-WKB-031": "通过",
    "TC-WKB-032": "通过",
    "TC-WKB-035": "通过",
    "TC-WKB-037": "通过",
    "TC-WKB-040": "通过",
    "TC-WKB-045": "通过",
    "TC-WKB-046": "通过",
    "TC-WKB-047": "通过",
}


class TestScorebookHandoffTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workbook = load_workbook(WORKBOOK_PATH, data_only=False)
        cls.calculated_workbook = load_workbook(WORKBOOK_PATH, data_only=True)

    def test_artifacts_are_archived_as_an_in_progress_package(self):
        self.assertTrue(WORKBOOK_PATH.is_file())
        self.assertTrue(BUILDER_PATH.is_file())
        self.assertTrue((OUTPUT_DIR / "evidence").is_dir())
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
        self.assertEqual(12, cases.max_column)
        self.assertNotIn("缺陷编号", [cell.value for cell in cases[2]])

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
        self.assertEqual({"通过": 48}, statuses)

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
                self.assertIn("tests.test_failed_execution_regressions", cases.cell(row, 12).value)

    def test_static_review_outcomes_have_automated_executor_and_code_evidence(self):
        cases = self.workbook["测试项目"]
        rows = {
            cases.cell(row, 1).value: row
            for row in range(1, cases.max_row + 1)
            if str(cases.cell(row, 1).value or "").startswith("TC-")
        }
        self.assertEqual(set(STATIC_REVIEW_CASES), set(STATIC_REVIEW_CASES) & set(rows))

        for case_id, expected_status in STATIC_REVIEW_CASES.items():
            row = rows[case_id]
            self.assertIn("静态", cases.cell(row, 8).value)
            self.assertEqual(expected_status, cases.cell(row, 9).value)
            self.assertEqual(datetime(2026, 10, 21), cases.cell(row, 10).value)
            self.assertEqual("自动化执行", cases.cell(row, 11).value)
            evidence = str(cases.cell(row, 12).value or "")
            self.assertRegex(evidence, r"\.(?:py|vue|less|json):\d")
            if case_id in {"TC-WKB-029", "TC-WKB-030", "TC-WKB-032"}:
                self.assertIn("tests.test_search_regressions", evidence)

    def test_search_implementation_and_regressions_cover_the_static_findings(self):
        root = Path(__file__).resolve().parents[1]
        search_api = (root / "wenkb-server" / "server" / "api" / "knb" / "SearchApi.py").read_text(encoding="utf-8")
        retriever = (root / "wenkb-server" / "server" / "core" / "tools" / "ask_to_llm.py").read_text(encoding="utf-8")
        search_view = (root / "wenkb-client" / "src" / "views" / "main" / "Search.vue").read_text(encoding="utf-8")
        dataset_view = (root / "wenkb-client" / "src" / "views" / "main" / "repository" / "Dataset.vue").read_text(encoding="utf-8")

        search_handler = search_api.split("# 搜索", 1)[1].split("# 搜索历史查询", 1)[0]
        result_item = search_view.split('<n-list-item v-for="(result, index) in resultList"', 1)[1].split("</n-list-item>", 1)[0]

        self.assertIn("session.get(ReposSetting, reposId)", search_handler)
        self.assertIn("Dataset.enbSts == 'enb'", search_handler)
        self.assertIn("Dataset.idxSts == 'ready'", search_handler)
        self.assertIn("setting_orm.topK", search_handler)
        self.assertIn("setting_orm.smlrTrval", search_handler)
        self.assertIn("{'dtsetId': {'$in': sorted(dataset_ids)}}", retriever)
        self.assertIn("@click=\"onResultClick(result)\"", result_item)
        self.assertIn("path: '/main/repository/detail'", search_view)
        self.assertIn("dtsetId: result.srcId", search_view)
        self.assertIn("route.query.dtsetId", dataset_view)
        self.assertIn("selectedId.value = dataset.dtsetId", dataset_view)

    def test_run_summary_formulas_and_saved_values_match_execution_results(self):
        formulas = self.workbook["运行"]
        self.assertIsNone(formulas["B14"].value)
        self.assertEqual("WenKB 浏览器工作区与主导航", formulas["B19"].value)

    def test_runtime_evidence_distinguishes_static_review_from_dynamic_execution(self):
        run = self.workbook["运行"]
        self.assertEqual("项目实际运行情况（截图已粘贴；详见用例执行状态）", run["A36"].value)
        self.assertIn("48 条用例结果和逐项证据已记录在本工作簿", run["A37"].value)
        self.assertEqual(3, run["A11"].value)
        self.assertIn("本表不设置缺陷编号列", run["B11"].value)
        self.assertEqual("仅界面已核验", run["F23"].value)
        self.assertIn("真实检索未执行", run["D23"].value)
        self.assertEqual("运行界面截图", run["A25"].value)
        self.assertEqual([f"S{index:02d}" for index in range(1, 7)], [run.cell(row, 1).value for row in range(18, 24)])
        self.assertEqual(6, len(run._images))

    def test_cover_and_formula_cells_are_consistent(self):
        cover = self.workbook["文件封面"]
        run = self.workbook["运行"]
        self.assertEqual("48 条用例复核完成：48 通过，0 失败，0 阻塞", cover["B12"].value)
        cover_basis = str(cover["A17"].value or "")
        self.assertTrue(
            "静态源码检查" in cover_basis or "测试计划" in cover_basis,
            f"unexpected scorebook basis text: {cover_basis}",
        )
        self.assertEqual("工作表说明", cover["A18"].value)
        self.assertIn("48 条用例结果和逐项证据已记录在本工作簿", run["A37"].value)
        errors = [
            f"{sheet.title}!{cell.coordinate}"
            for sheet in self.calculated_workbook.worksheets
            for row in sheet.iter_rows()
            for cell in row
            if cell.data_type == "e"
        ]
        self.assertEqual([], errors)

if __name__ == "__main__":
    unittest.main()
