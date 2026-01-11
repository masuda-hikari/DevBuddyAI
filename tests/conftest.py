"""
pytest共通設定・フィクスチャ
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from devbuddy.llm.client import MockLLMClient


@pytest.fixture(autouse=True)
def skip_license_check(request):
    """全テストでライセンスチェックをスキップ（ライセンステスト以外）"""
    # test_licensing.pyでのテストはモックしない
    if "test_licensing" in request.node.nodeid:
        yield
        return

    with patch(
        "devbuddy.core.licensing.LicenseManager.check_review_limit",
        return_value=True
    ), patch(
        "devbuddy.core.licensing.LicenseManager.check_testgen_limit",
        return_value=True
    ), patch(
        "devbuddy.core.licensing.LicenseManager.check_fix_limit",
        return_value=True
    ):
        yield


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
