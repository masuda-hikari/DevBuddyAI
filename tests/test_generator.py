"""
CodeTestGeneratorのテスト
"""

import pytest
from pathlib import Path

from devbuddy.core.generator import CodeTestGenerator, FunctionInfo, GenerationResult
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

    def test_generate_tests_function_not_found(self, generator, temp_python_file):
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
        generator = CodeTestGenerator(client=mock_client, skip_license_check=True)

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
