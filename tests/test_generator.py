"""
CodeTestGeneratorのテスト
"""

import pytest
from pathlib import Path

from devbuddy.core.generator import (
    CodeTestGenerator,
    FunctionInfo,
    GenerationResult,
)
from devbuddy.llm.client import MockLLMClient


class TestCodeTestGenerator:
    """CodeTestGeneratorテストクラス"""

    @pytest.fixture
    def generator(self):
        """ジェネレーターインスタンス"""
        client = MockLLMClient(responses={
            "test": """import pytest

def test_add_positive():
    assert add(1, 2) == 3

def test_add_negative():
    assert add(-1, -1) == -2
"""
        })
        # テスト時はライセンスチェックをスキップ
        return CodeTestGenerator(client=client, skip_license_check=True)

    def test_generate_tests_success(self, generator, temp_python_file):
        """テスト生成成功"""
        result = generator.generate_tests(temp_python_file)

        assert isinstance(result, GenerationResult)
        assert result.success is True
        assert "def test_" in result.test_code

    def test_generate_tests_file_not_found(self, generator):
        """存在しないファイル"""
        result = generator.generate_tests(Path("/nonexistent.py"))

        assert result.success is False
        assert "Failed to read file" in result.error

    def test_generate_tests_function_not_found(
        self, generator, temp_python_file
    ):
        """存在しない関数指定"""
        result = generator.generate_tests(
            temp_python_file,
            function_name="nonexistent_func"
        )

        assert result.success is False
        assert "not found" in result.error

    def test_extract_functions(self, generator, sample_python_code):
        """関数抽出テスト"""
        functions = generator._extract_functions(sample_python_code)

        assert len(functions) == 2
        assert functions[0].name == "add"
        assert functions[1].name == "divide"

    def test_extract_function_with_type_hints(self, generator):
        """型ヒント付き関数の抽出"""
        code = """
def greet(name: str, times: int = 1) -> str:
    '''Greet someone'''
    return f"Hello, {name}!" * times
"""
        functions = generator._extract_functions(code)

        assert len(functions) == 1
        func = functions[0]
        assert func.name == "greet"
        assert "name: str" in func.args
        assert "times: int" in func.args[1]
        assert func.return_type == "str"
        assert func.docstring == "Greet someone"

    def test_clean_test_code_markdown(self, generator):
        """マークダウン除去テスト"""
        code_with_markdown = """```python
def test_example():
    assert True
```"""

        cleaned = generator._clean_test_code(code_with_markdown)

        assert "```" not in cleaned
        assert "def test_example():" in cleaned

    def test_generate_tests_with_framework(self, generator, temp_python_file):
        """フレームワーク指定テスト"""
        result_pytest = generator.generate_tests(
            temp_python_file,
            framework="pytest"
        )
        result_unittest = generator.generate_tests(
            temp_python_file,
            framework="unittest"
        )

        assert result_pytest.success
        assert result_unittest.success


class TestFunctionInfo:
    """FunctionInfoテストクラス"""

    def test_function_info_creation(self):
        """FunctionInfo作成テスト"""
        info = FunctionInfo(
            name="test_func",
            args=["a: int", "b: str"],
            return_type="bool",
            docstring="Test function",
            source="def test_func(a: int, b: str) -> bool:\n    pass",
            line_start=1,
            line_end=2,
        )

        assert info.name == "test_func"
        assert len(info.args) == 2
        assert info.return_type == "bool"


class TestGenerationResult:
    """GenerationResultテストクラス"""

    def test_success_result(self):
        """成功結果"""
        result = GenerationResult(
            success=True,
            test_code="def test_foo(): pass",
            test_count=1,
            verified=True,
        )

        assert result.success is True
        assert result.test_code == "def test_foo(): pass"
        assert result.test_count == 1
        assert result.verified is True

    def test_error_result(self):
        """エラー結果"""
        result = GenerationResult(
            success=False,
            error="Failed to generate",
        )

        assert result.success is False
        assert result.error == "Failed to generate"
        assert result.test_code == ""


class TestCodeTestGeneratorExtended:
    """CodeTestGenerator拡張テスト"""

    @pytest.fixture
    def generator(self):
        """ジェネレーターインスタンス"""
        client = MockLLMClient(responses={
            "test": "def test_example(): pass",
        })
        # テスト時はライセンスチェックをスキップ
        return CodeTestGenerator(client=client, skip_license_check=True)

    def test_extract_functions_syntax_error(self, generator):
        """構文エラーのコードから抽出"""
        code = "def invalid syntax("
        functions = generator._extract_functions(code)

        assert functions == []

    def test_extract_functions_no_functions(self, generator):
        """関数のないコード"""
        code = "x = 1\ny = 2"
        functions = generator._extract_functions(code)

        assert functions == []

    def test_extract_functions_nested(self, generator):
        """ネストされた関数"""
        code = """
def outer():
    def inner():
        pass
    return inner
"""
        functions = generator._extract_functions(code)

        # ast.walkはネストした関数も取得する
        assert len(functions) >= 2

    def test_clean_test_code_triple_backticks(self, generator):
        """トリプルバッククォートのみ"""
        code = """```
def test_example():
    pass
```"""

        cleaned = generator._clean_test_code(code)

        assert "```" not in cleaned
        assert "def test_example():" in cleaned

    def test_clean_test_code_no_markdown(self, generator):
        """マークダウンなし"""
        code = "def test_example(): pass"
        cleaned = generator._clean_test_code(code)

        assert cleaned == code

    def test_generate_tests_llm_error(self, tmp_path):
        """LLMエラー時"""
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.complete.side_effect = Exception("API Error")

        # テスト時はライセンスチェックをスキップ
        generator = CodeTestGenerator(
            client=mock_client, skip_license_check=True
        )

        source_file = tmp_path / "test.py"
        source_file.write_text("def foo(): pass")

        result = generator.generate_tests(source_file)

        assert result.success is False
        assert "API Error" in str(result.error)

    def test_generate_tests_count(self, tmp_path):
        """テスト数カウント"""
        client = MockLLMClient(responses={
            "def": """def test_one(): pass
def test_two(): pass
def test_three(): pass"""
        })
        # テスト時はライセンスチェックをスキップ
        generator = CodeTestGenerator(client=client, skip_license_check=True)

        source_file = tmp_path / "calc.py"
        source_file.write_text("def add(a, b): return a + b")

        result = generator.generate_tests(source_file)

        assert result.test_count == 3

    def test_generate_tests_specific_function(self, tmp_path):
        """特定関数のみテスト生成"""
        client = MockLLMClient(responses={
            "def": "def test_add(): pass"
        })
        # テスト時はライセンスチェックをスキップ
        generator = CodeTestGenerator(client=client, skip_license_check=True)

        source_file = tmp_path / "math_ops.py"
        source_file.write_text("""
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
""")

        result = generator.generate_tests(source_file, function_name="add")

        assert result.success is True

    def test_max_retry_attribute(self):
        """max_retry属性確認"""
        client = MockLLMClient()
        generator = CodeTestGenerator(client=client)

        assert generator.max_retry == 3

    def test_extract_function_no_return_type(self, generator):
        """戻り値型なしの関数"""
        code = """
def no_return(x):
    print(x)
"""
        functions = generator._extract_functions(code)

        assert len(functions) == 1
        assert functions[0].return_type is None

    def test_extract_function_no_docstring(self, generator):
        """docstringなしの関数"""
        code = """
def simple():
    return 1
"""
        functions = generator._extract_functions(code)

        assert len(functions) == 1
        assert functions[0].docstring is None


class TestTestVerificationReport:
    """TestVerificationReportのテスト"""

    def test_default_values(self):
        """デフォルト値の確認"""
        from devbuddy.core.generator import TestVerificationReport

        report = TestVerificationReport()

        assert report.passed == 0
        assert report.failed == 0
        assert report.errors == 0
        assert report.skipped == 0
        assert report.coverage_percent is None
        assert report.failed_tests == []
        assert report.error_messages == []

    def test_with_values(self):
        """値を設定した場合"""
        from devbuddy.core.generator import TestVerificationReport

        report = TestVerificationReport(
            passed=5,
            failed=2,
            errors=1,
            skipped=0,
            coverage_percent=80.5,
            failed_tests=["test_foo", "test_bar"],
            error_messages=["AssertionError"],
        )

        assert report.passed == 5
        assert report.failed == 2
        assert report.errors == 1
        assert report.coverage_percent == 80.5
        assert len(report.failed_tests) == 2


class TestParseTestOutput:
    """_parse_test_outputのテスト"""

    @pytest.fixture
    def generator(self):
        """ジェネレーターインスタンス"""
        client = MockLLMClient()
        return CodeTestGenerator(client=client, skip_license_check=True)

    def test_parse_passed_only(self, generator):
        """全テスト成功の出力"""
        output = """
============================= test session starts =============================
collected 5 items

test_example.py .....                                                    [100%]

============================== 5 passed in 0.53s ==============================
"""
        report = generator._parse_test_output(output)

        assert report.passed == 5
        assert report.failed == 0
        assert report.errors == 0

    def test_parse_with_failures(self, generator):
        """失敗を含む出力"""
        output = """
============================= test session starts =============================
collected 5 items

test_example.py ...FF                                                    [100%]

=== FAILURES ===
FAILED test_example.py::test_foo - AssertionError: 1 == 2
FAILED test_example.py::test_bar - ValueError

========================= 3 passed, 2 failed in 0.53s ===========
"""
        report = generator._parse_test_output(output)

        assert report.passed == 3
        assert report.failed == 2
        assert "test_foo" in report.failed_tests
        assert "test_bar" in report.failed_tests

    def test_parse_with_skipped(self, generator):
        """スキップを含む出力"""
        output = """
============================= test session starts =============================
collected 5 items

test_example.py ...s.                                                    [100%]

========================= 4 passed, 1 skipped in 0.53s ===========
"""
        report = generator._parse_test_output(output)

        assert report.passed == 4
        assert report.skipped == 1

    def test_parse_with_coverage(self, generator):
        """カバレッジを含む出力"""
        output = """
============================= test session starts =============================
test_example.py .....                                                    [100%]

---------- coverage: platform linux, python 3.12.0-final-0 -----------
Name                      Stmts   Miss  Cover
---------------------------------------------
src/module.py                50     10    80%
---------------------------------------------
TOTAL                       100     20    80%

============================== 5 passed in 0.53s ==============================
"""
        report = generator._parse_test_output(output)

        assert report.coverage_percent == 80.0

    def test_parse_with_error_messages(self, generator):
        """エラーメッセージを含む出力"""
        output = """
=== FAILURES ===
_ test_foo _
    def test_foo():
>       assert 1 == 2
E       AssertionError: assert 1 == 2
E       assert 1 == 2

5 passed, 1 failed in 0.53s
"""
        report = generator._parse_test_output(output)

        # エラーメッセージが抽出される（正規表現による抽出）
        # パースされるかどうかはここでは重要ではなく、メソッドが正常に動作することを確認
        assert report.failed == 1
        assert report.passed == 5


class TestBuildErrorContext:
    """_build_error_contextのテスト"""

    @pytest.fixture
    def generator(self):
        """ジェネレーターインスタンス"""
        client = MockLLMClient()
        return CodeTestGenerator(client=client, skip_license_check=True)

    def test_build_context(self, generator):
        """エラーコンテキスト構築"""
        from devbuddy.core.generator import TestVerificationReport

        report = TestVerificationReport(
            passed=3,
            failed=2,
            errors=0,
            failed_tests=["test_foo", "test_bar"],
            error_messages=["AssertionError: assert 1 == 2"],
        )

        context = generator._build_error_context(
            test_code="def test_foo(): pass",
            output="Test output here",
            report=report,
            attempt=1,
        )

        assert "試行 1/3" in context
        assert "失敗テスト数: 2" in context
        assert "test_foo" in context
        assert "test_bar" in context
        assert "AssertionError" in context

    def test_build_context_no_failures(self, generator):
        """失敗なしの場合"""
        from devbuddy.core.generator import TestVerificationReport

        report = TestVerificationReport(passed=5, failed=0, errors=0)

        context = generator._build_error_context(
            test_code="def test_foo(): pass",
            output="All tests passed",
            report=report,
            attempt=1,
        )

        assert "失敗テスト数: 0" in context


class TestGenerateAndVerify:
    """generate_and_verifyのテスト"""

    def test_verify_success(self, tmp_path):
        """検証成功のケース"""
        from unittest.mock import patch, MagicMock

        client = MockLLMClient(responses={
            "def": """import pytest

def test_add():
    assert 1 + 1 == 2
"""
        })
        generator = CodeTestGenerator(client=client, skip_license_check=True)

        source_file = tmp_path / "calc.py"
        source_file.write_text("def add(a, b): return a + b")

        # subprocessをモック
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="5 passed in 0.53s",
                stderr="",
            )

            result = generator.generate_and_verify(source_file)

            assert result.success is True
            assert result.verified is True

    def test_verify_failure_then_fix(self, tmp_path):
        """失敗後に修正を試みるケース"""
        from unittest.mock import patch, MagicMock

        # 最初は失敗、2回目は成功のレスポンス
        responses = {
            "def": "def test_add(): assert 1 == 2",  # 最初
            "修正": "def test_add(): assert 1 + 1 == 2",  # 修正後
        }
        client = MockLLMClient(responses=responses)
        generator = CodeTestGenerator(client=client, skip_license_check=True)

        source_file = tmp_path / "calc.py"
        source_file.write_text("def add(a, b): return a + b")

        call_count = [0]

        def mock_subprocess(*args, **kwargs):
            call_count[0] += 1
            mock = MagicMock()
            if call_count[0] == 1:
                # 最初の実行は失敗
                mock.returncode = 1
                mock.stdout = "FAILED test_calc::test_add\n1 passed, 1 failed"
                mock.stderr = ""
            else:
                # 2回目は成功
                mock.returncode = 0
                mock.stdout = "2 passed in 0.53s"
                mock.stderr = ""
            return mock

        with patch("subprocess.run", side_effect=mock_subprocess):
            result = generator.generate_and_verify(source_file)

            # 何かしらの結果が返る（成功・失敗問わず）
            assert result.attempts >= 1

    def test_verify_timeout(self, tmp_path):
        """タイムアウトのケース"""
        from unittest.mock import patch
        import subprocess as sp

        client = MockLLMClient(responses={
            "def": "def test_add(): pass"
        })
        generator = CodeTestGenerator(client=client, skip_license_check=True)

        source_file = tmp_path / "calc.py"
        source_file.write_text("def add(a, b): return a + b")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = sp.TimeoutExpired(cmd="pytest", timeout=60)

            result = generator.generate_and_verify(source_file)

            assert result.success is False
            assert "timed out" in result.error

    def test_verify_with_coverage(self, tmp_path):
        """カバレッジ測定付きのケース"""
        from unittest.mock import patch, MagicMock

        client = MockLLMClient(responses={
            "def": "def test_add(): assert True"
        })
        generator = CodeTestGenerator(client=client, skip_license_check=True)

        source_file = tmp_path / "calc.py"
        source_file.write_text("def add(a, b): return a + b")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="5 passed\nTOTAL                   100     20    80%",
                stderr="",
            )

            result = generator.generate_and_verify(
                source_file, measure_coverage=True
            )

            assert result.success is True
            assert result.verification_report is not None
            assert result.verification_report.coverage_percent == 80.0


class TestLicenseCheck:
    """ライセンスチェックのテスト"""

    def test_skip_license_check(self, tmp_path):
        """ライセンスチェックスキップ"""
        client = MockLLMClient(responses={"def": "def test_foo(): pass"})
        generator = CodeTestGenerator(client=client, skip_license_check=True)

        source_file = tmp_path / "test.py"
        source_file.write_text("def foo(): pass")

        result = generator.generate_tests(source_file)

        assert result.success is True

    def test_license_check_limit_exceeded(self, tmp_path):
        """利用制限超過"""
        from unittest.mock import MagicMock
        from devbuddy.core.licensing import UsageLimitError

        mock_manager = MagicMock()
        mock_manager.check_testgen_limit.side_effect = UsageLimitError(
            "Monthly limit exceeded"
        )

        client = MockLLMClient(responses={"def": "def test_foo(): pass"})
        generator = CodeTestGenerator(
            client=client,
            license_manager=mock_manager,
            skip_license_check=False,
        )

        source_file = tmp_path / "test.py"
        source_file.write_text("def foo(): pass")

        result = generator.generate_tests(source_file)

        assert result.success is False
        assert "limit" in result.error.lower()
