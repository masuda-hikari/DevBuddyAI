"""
pytest共通設定・フィクスチャ
"""

import pytest
from pathlib import Path

from devbuddy.llm.client import MockLLMClient


@pytest.fixture
def mock_llm_client():
    """モックLLMクライアント"""
    return MockLLMClient(responses={
        "review": "[WARNING] Line 10: Potential issue\n  Suggestion: Fix it",
        "test": "def test_example():\n    assert True",
    })


@pytest.fixture
def sample_python_code():
    """サンプルPythonコード"""
    return '''
def add(a, b):
    return a + b

def divide(a, b):
    return a / b
'''


@pytest.fixture
def sample_buggy_code():
    """バグを含むサンプルコード"""
    return '''
def process(data):
    result = data["value"]  # KeyError possible
    return result / 0  # ZeroDivisionError
'''


@pytest.fixture
def temp_python_file(tmp_path, sample_python_code):
    """一時Pythonファイル"""
    file_path = tmp_path / "sample.py"
    file_path.write_text(sample_python_code, encoding="utf-8")
    return file_path


@pytest.fixture
def samples_dir():
    """サンプルディレクトリ"""
    return Path(__file__).parent.parent / "samples"
