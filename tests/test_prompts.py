"""
PromptTemplatesのテスト
"""

import pytest
from devbuddy.llm.prompts import PromptTemplates
from devbuddy.core.generator import FunctionInfo


class TestPromptTemplates:
    """PromptTemplatesテストクラス"""

    @pytest.fixture
    def prompts(self):
        """プロンプトテンプレートインスタンス"""
        return PromptTemplates()

    def test_code_review_basic(self, prompts):
        """基本的なコードレビュープロンプト"""
        code = "x = 1 + 2"
        prompt = prompts.code_review(code)

        assert "python" in prompt.lower()
        assert "x = 1 + 2" in prompt
        assert "[BUG]" in prompt or "BUG" in prompt
        assert "[WARNING]" in prompt or "WARNING" in prompt

    def test_code_review_language(self, prompts):
        """言語指定"""
        code = "const x = 1;"
        prompt = prompts.code_review(code, language="javascript")

        assert "javascript" in prompt.lower()

    def test_code_review_severity_low(self, prompts):
        """重要度: low"""
        prompt = prompts.code_review("x = 1", severity="low")

        assert "全ての問題" in prompt or "情報レベル" in prompt

    def test_code_review_severity_medium(self, prompts):
        """重要度: medium"""
        prompt = prompts.code_review("x = 1", severity="medium")

        assert "バグ" in prompt
        assert "警告" in prompt
        assert "スタイル" in prompt

    def test_code_review_severity_high(self, prompts):
        """重要度: high"""
        prompt = prompts.code_review("x = 1", severity="high")

        assert "バグ" in prompt
        assert "重大" in prompt

    def test_diff_review(self, prompts):
        """diffレビュープロンプト"""
        diff = "@@ -1 +1 @@\n-old\n+new"
        prompt = prompts.diff_review(diff)

        assert "diff" in prompt.lower()
        assert "@@ -1 +1 @@" in prompt
        assert "追加されたコード" in prompt
        assert "削除" in prompt

    def test_test_generation_basic(self, prompts):
        """テスト生成プロンプト（基本）"""
        func = FunctionInfo(
            name="add",
            args=["a: int", "b: int"],
            return_type="int",
            docstring="Add two numbers",
            source="def add(a: int, b: int) -> int:\n    return a + b",
            line_start=1,
            line_end=2,
        )
        prompt = prompts.test_generation([func], "calculator", "pytest")

        assert "add" in prompt
        assert "a: int" in prompt
        assert "int" in prompt
        assert "pytest" in prompt.lower()
        assert "calculator" in prompt

    def test_test_generation_unittest(self, prompts):
        """テスト生成（unittest）"""
        func = FunctionInfo(
            name="test_func",
            args=[],
            return_type=None,
            docstring=None,
            source="def test_func(): pass",
            line_start=1,
            line_end=1,
        )
        prompt = prompts.test_generation([func], "module", "unittest")

        assert "unittest" in prompt.lower()
        assert "import unittest" in prompt

    def test_test_generation_multiple_functions(self, prompts):
        """複数関数のテスト生成"""
        funcs = [
            FunctionInfo(
                name="func1",
                args=["x"],
                return_type="int",
                docstring="Function 1",
                source="def func1(x): return x",
                line_start=1,
                line_end=1,
            ),
            FunctionInfo(
                name="func2",
                args=["y"],
                return_type="str",
                docstring="Function 2",
                source="def func2(y): return str(y)",
                line_start=2,
                line_end=2,
            ),
        ]
        prompt = prompts.test_generation(funcs, "module")

        assert "func1" in prompt
        assert "func2" in prompt
        assert "Function 1" in prompt
        assert "Function 2" in prompt

    def test_fix_failing_tests(self, prompts):
        """失敗テスト修正プロンプト"""
        test_code = "def test_fail(): assert 1 == 2"
        error = "AssertionError: assert 1 == 2"
        prompt = prompts.fix_failing_tests(test_code, error)

        assert "def test_fail" in prompt
        assert "AssertionError" in prompt
        assert "修正" in prompt

    def test_bug_fix_without_source(self, prompts):
        """バグ修正プロンプト（ソースなし）"""
        test_code = "def test_x(): assert func() == 1"
        error = "AssertionError"
        prompt = prompts.bug_fix(test_code, error)

        assert "def test_x" in prompt
        assert "AssertionError" in prompt
        assert "FILE:" in prompt
        assert "LINE:" in prompt
        assert "ORIGINAL:" in prompt
        assert "REPLACEMENT:" in prompt

    def test_bug_fix_with_source(self, prompts):
        """バグ修正プロンプト（ソースあり）"""
        test_code = "def test_x(): assert func() == 1"
        error = "AssertionError"
        source_code = "def func(): return 2"
        prompt = prompts.bug_fix(test_code, error, source_code)

        assert "def test_x" in prompt
        assert "def func" in prompt
        assert "ソースコード" in prompt

    def test_explain_code(self, prompts):
        """コード説明プロンプト"""
        code = "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"
        prompt = prompts.explain_code(code)

        assert "factorial" in prompt
        assert "python" in prompt.lower()
        assert "目的" in prompt
        assert "処理フロー" in prompt

    def test_explain_code_language(self, prompts):
        """コード説明（言語指定）"""
        code = "function hello() { return 'Hello'; }"
        prompt = prompts.explain_code(code, language="javascript")

        assert "javascript" in prompt.lower()
        assert "function hello" in prompt

    def test_suggest_improvements(self, prompts):
        """改善提案プロンプト"""
        code = "x = [i for i in range(1000000) if i % 2 == 0]"
        prompt = prompts.suggest_improvements(code)

        assert "range(1000000)" in prompt
        assert "パフォーマンス" in prompt
        assert "可読性" in prompt
        assert "保守性" in prompt

    def test_suggest_improvements_language(self, prompts):
        """改善提案（言語指定）"""
        code = "for (let i = 0; i < arr.length; i++) {}"
        prompt = prompts.suggest_improvements(code, language="javascript")

        assert "javascript" in prompt.lower()
