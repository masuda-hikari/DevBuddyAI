"""
PythonAnalyzerのテスト
"""

import pytest

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


class TestPythonAnalyzerFlake8:
    """flake8連携のテスト"""

    @pytest.fixture
    def analyzer(self):
        """アナライザーインスタンス"""
        config = AnalysisConfig(use_flake8=True)
        return PythonAnalyzer(config)

    def test_flake8_code_to_level_error(self, analyzer):
        """E9コードはbug"""
        level = analyzer._flake8_code_to_level("E901")
        assert level == "bug"

    def test_flake8_code_to_level_f_error(self, analyzer):
        """Fコードはbug"""
        level = analyzer._flake8_code_to_level("F401")
        assert level == "bug"

    def test_flake8_code_to_level_style(self, analyzer):
        """Eコード（E9以外）はstyle"""
        level = analyzer._flake8_code_to_level("E501")
        assert level == "style"

    def test_flake8_code_to_level_warning(self, analyzer):
        """Wコードはwarning"""
        level = analyzer._flake8_code_to_level("W503")
        assert level == "warning"

    def test_flake8_code_to_level_complexity(self, analyzer):
        """Cコードはinfo"""
        level = analyzer._flake8_code_to_level("C901")
        assert level == "info"

    def test_flake8_code_to_level_unknown(self, analyzer):
        """不明なコードはinfo"""
        level = analyzer._flake8_code_to_level("X001")
        assert level == "info"

    def test_analyze_with_file_flake8_disabled(self):
        """flake8無効時のコード解析"""
        config = AnalysisConfig(use_flake8=False, use_mypy=False)
        analyzer = PythonAnalyzer(config)
        code = "x = 1\n"
        issues = analyzer.analyze(code)
        # 外部ツール無効時は空（パターンベース解析のみ）
        assert isinstance(issues, list)

    def test_analyze_with_config_ignore_codes(self):
        """ignore_codes設定テスト"""
        config = AnalysisConfig(
            use_flake8=False,
            use_mypy=False,
            ignore_codes=["E501", "W503"]
        )
        analyzer = PythonAnalyzer(config)
        assert "E501" in analyzer.config.ignore_codes
        assert "W503" in analyzer.config.ignore_codes


class TestPythonAnalyzerMypy:
    """mypy連携のテスト（モック）"""

    @pytest.fixture
    def analyzer_with_mypy(self):
        """mypy有効アナライザー"""
        config = AnalysisConfig(use_mypy=True, use_flake8=False)
        return PythonAnalyzer(config)

    def test_mypy_config_enabled(self, analyzer_with_mypy):
        """mypy設定が有効"""
        assert analyzer_with_mypy.config.use_mypy is True

    def test_run_mypy_no_file(self, analyzer_with_mypy):
        """存在しないファイルでのmypy実行"""
        from pathlib import Path
        issues = analyzer_with_mypy._run_mypy(Path("/nonexistent/file.py"))
        # ファイルが存在しない場合は空リスト
        assert issues == []

    def test_run_flake8_no_file(self):
        """存在しないファイルでのflake8実行"""
        from pathlib import Path
        config = AnalysisConfig(use_flake8=True, use_mypy=False)
        analyzer = PythonAnalyzer(config)
        issues = analyzer._run_flake8(Path("/nonexistent/file.py"))
        # ファイルが存在しない場合、flake8がエラー出力
        # 空リストまたはエラー報告のいずれか
        assert isinstance(issues, list)


class TestPythonAnalyzerEdgeCases:
    """エッジケースのテスト"""

    @pytest.fixture
    def analyzer(self):
        """アナライザーインスタンス"""
        return PythonAnalyzer()

    def test_empty_code(self, analyzer):
        """空のコード"""
        issues = analyzer.analyze("")
        assert isinstance(issues, list)

    def test_whitespace_only(self, analyzer):
        """空白のみのコード"""
        issues = analyzer.analyze("   \n\n   ")
        assert isinstance(issues, list)

    def test_get_functions_syntax_error(self, analyzer):
        """構文エラーでの関数取得"""
        functions = analyzer.get_functions("def broken(")
        assert functions == []

    def test_get_classes_syntax_error(self, analyzer):
        """構文エラーでのクラス取得"""
        classes = analyzer.get_classes("class Broken(")
        assert classes == []

    def test_check_syntax_with_lineno(self, analyzer):
        """構文エラーの行番号付きメッセージ"""
        code = "def func():\n    x = ("
        valid, error = analyzer.check_syntax(code)
        assert valid is False
        assert "Line" in error
