"""
PythonAnalyzerのテスト
"""

import pytest
from pathlib import Path

from devbuddy.analyzers.python_analyzer import PythonAnalyzer, AnalysisConfig


class TestPythonAnalyzer:
    """PythonAnalyzerテストクラス"""

    @pytest.fixture
    def analyzer(self):
        """アナライザーインスタンス"""
        return PythonAnalyzer()

    def test_analyze_syntax_error(self, analyzer):
        """構文エラー検出"""
        code = "def broken("  # 構文エラー

        issues = analyzer.analyze(code)

        assert len(issues) == 1
        assert issues[0].level == "bug"
        assert "Syntax error" in issues[0].message

    def test_detect_bare_except(self, analyzer):
        """bare except検出"""
        code = """
try:
    x = 1
except:
    pass
"""
        issues = analyzer.analyze(code)

        bare_except = [i for i in issues if "Bare except" in i.message]
        assert len(bare_except) == 1
        assert bare_except[0].level == "warning"

    def test_detect_mutable_default(self, analyzer):
        """ミュータブルデフォルト引数検出"""
        code = """
def func(items=[]):
    items.append(1)
    return items
"""
        issues = analyzer.analyze(code)

        mutable = [i for i in issues if "Mutable default" in i.message]
        assert len(mutable) == 1
        assert mutable[0].level == "warning"

    def test_detect_eval_usage(self, analyzer):
        """eval使用検出"""
        code = """
result = eval("1 + 2")
"""
        issues = analyzer.analyze(code)

        eval_issues = [i for i in issues if "eval()" in i.message]
        assert len(eval_issues) == 1
        assert eval_issues[0].level == "bug"

    def test_detect_exec_usage(self, analyzer):
        """exec使用検出"""
        code = """
exec("x = 1")
"""
        issues = analyzer.analyze(code)

        exec_issues = [i for i in issues if "exec()" in i.message]
        assert len(exec_issues) == 1

    def test_detect_global_statement(self, analyzer):
        """global文検出"""
        code = """
counter = 0
def increment():
    global counter
    counter += 1
"""
        issues = analyzer.analyze(code)

        global_issues = [i for i in issues if "Global statement" in i.message]
        assert len(global_issues) == 1
        assert global_issues[0].level == "style"

    def test_check_syntax_valid(self, analyzer):
        """有効な構文チェック"""
        code = "x = 1 + 2"
        valid, error = analyzer.check_syntax(code)

        assert valid is True
        assert error is None

    def test_check_syntax_invalid(self, analyzer):
        """無効な構文チェック"""
        code = "x = ("
        valid, error = analyzer.check_syntax(code)

        assert valid is False
        assert error is not None

    def test_get_functions(self, analyzer):
        """関数名取得"""
        code = """
def func1():
    pass

def func2(x):
    return x

class MyClass:
    def method(self):
        pass
"""
        functions = analyzer.get_functions(code)

        assert "func1" in functions
        assert "func2" in functions
        assert "method" in functions

    def test_get_classes(self, analyzer):
        """クラス名取得"""
        code = """
class ClassA:
    pass

class ClassB(ClassA):
    pass
"""
        classes = analyzer.get_classes(code)

        assert "ClassA" in classes
        assert "ClassB" in classes

    def test_clean_code_no_issues(self, analyzer):
        """問題のないコード"""
        code = """
def clean_function(x: int) -> int:
    '''Clean function'''
    return x * 2
"""
        issues = analyzer.analyze(code)

        # assert以外の警告がない
        non_assert_issues = [i for i in issues if "Assert" not in i.message]
        assert len(non_assert_issues) == 0


class TestAnalysisConfig:
    """AnalysisConfigテストクラス"""

    def test_default_config(self):
        """デフォルト設定"""
        config = AnalysisConfig()

        assert config.use_flake8 is True
        assert config.use_mypy is False
        assert config.max_line_length == 120

    def test_custom_config(self):
        """カスタム設定"""
        config = AnalysisConfig(
            use_flake8=False,
            use_mypy=True,
            max_line_length=80,
            ignore_codes=["E501", "W503"],
        )

        assert config.use_flake8 is False
        assert config.use_mypy is True
        assert config.max_line_length == 80
        assert "E501" in config.ignore_codes
