import importlib.util
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("affirmative_statement_lint.py")
SPEC = importlib.util.spec_from_file_location("affirmative_statement_lint", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class AffirmativeStatementLintTest(unittest.TestCase):
    def scan(self, text: str, allowlist: tuple[str, ...] = ()):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.md"
            path.write_text(text, encoding="utf-8")
            return MODULE.scan_file(path, allowlist)

    def test_flags_complete_negative_contrast(self):
        findings = self.scan("改变通常不是由一个大事件触发，而是多个小矛盾持续叠加。\n")
        self.assertIn("negative-contrast", {item[1].rule_id for item in findings})

    def test_flags_incomplete_negative_heading(self):
        findings = self.scan("### 高新南能进入候选，但不能自动赢得选择\n")
        self.assertIn("negative-heading", {item[1].rule_id for item in findings})

    def test_flags_transition_without_negative_word(self):
        findings = self.scan("价格促成进入谈判，却不能替代居住答案。\n")
        self.assertIn("transition-word", {item[1].rule_id for item in findings})

    def test_flags_topic_heading(self):
        findings = self.scan("## 三、三类优先购买任务\n")
        self.assertIn("topic-heading", {item[1].rule_id for item in findings})

    def test_accepts_affirmative_rewrite(self):
        findings = self.scan("最终选择由组合满足共同裁定，每一项居住条件都握有否决权。\n")
        self.assertEqual([], findings)

    def test_exact_approved_phrase_can_be_allowed(self):
        phrase = "生活不必重建，改善不止一套房"
        findings = self.scan(f"- {phrase}\n", (phrase,))
        self.assertEqual([], findings)

    def test_process_template_is_valid(self):
        findings = self.scan("户型楼层朝向先定居住基础，公区车位总价再完成裁定。\n")
        self.assertEqual([], findings)

    def test_report_only_returns_success_when_findings_exist(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.md"
            path.write_text("这不是结论，而是过程。\n", encoding="utf-8")
            with mock.patch.object(
                sys,
                "argv",
                ["affirmative_statement_lint.py", "--report-only", str(path)],
            ):
                self.assertEqual(0, MODULE.main())


if __name__ == "__main__":
    unittest.main()
