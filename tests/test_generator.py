"""
TestGeneratorのテスト
"""

import pytest
from pathlib import Path

from devbuddy.core.generator import TestGenerator, FunctionInfo, GenerationResult
from devbuddy.llm.client import MockLLMClient


class TestTestGenerator:
    """TestGeneratorテストクラス"""

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
        return TestGenerator(client=client)

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
