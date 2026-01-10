"""
BugFixerのテスト
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from devbuddy.core.fixer import BugFixer, FixSuggestion, FixResult
from devbuddy.llm.client import MockLLMClient


class TestBugFixer:
    """BugFixerテストクラス"""

    @pytest.fixture
    def fixer(self):
        """フィクサーインスタンス"""
        client = MockLLMClient(responses={
            "fix": """FILE: test.py
LINE: 10
DESCRIPTION: Fix division by zero
ORIGINAL: return a / b
REPLACEMENT: return a / b if b != 0 else 0
"""
        })
        return BugFixer(client=client)

    def test_parse_fix_response(self, fixer):
        """AIレスポンスパースのテスト"""
        response = """FILE: src/calc.py
LINE: 42
DESCRIPTION: Fix null reference
ORIGINAL: data.value
REPLACEMENT: data.value if data else None
"""
        suggestions = fixer._parse_fix_response(response, Path("default.py"))

        assert len(suggestions) == 1
        assert suggestions[0].file_path == Path("src/calc.py")
        assert suggestions[0].line == 42
        assert suggestions[0].description == "Fix null reference"
        assert suggestions[0].original == "data.value"
        assert suggestions[0].replacement == "data.value if data else None"

    def test_parse_fix_response_multiple(self, fixer):
        """複数の修正提案パース"""
        response = """FILE: a.py
LINE: 1
DESCRIPTION: Fix 1
ORIGINAL: old1
REPLACEMENT: new1
FILE: b.py
LINE: 2
DESCRIPTION: Fix 2
ORIGINAL: old2
REPLACEMENT: new2
"""
        suggestions = fixer._parse_fix_response(response, Path("default.py"))

        assert len(suggestions) == 2
        assert suggestions[0].file_path == Path("a.py")
        assert suggestions[1].file_path == Path("b.py")

    def test_parse_fix_response_incomplete(self, fixer):
        """不完全なレスポンスのパース"""
        response = """FILE: test.py
LINE: 10
DESCRIPTION: Incomplete suggestion
"""
        suggestions = fixer._parse_fix_response(response, Path("default.py"))

        # 必須フィールド不足で除外される
        assert len(suggestions) == 0

    def test_create_suggestion_valid(self, fixer):
        """有効なデータからFixSuggestion作成"""
        data = {
            "file": "test.py",
            "line": "15",
            "description": "Test fix",
            "original": "old code",
            "replacement": "new code",
        }
        suggestion = fixer._create_suggestion(data, Path("default.py"))

        assert suggestion is not None
        assert suggestion.file_path == Path("test.py")
        assert suggestion.line == 15
        assert suggestion.description == "Test fix"

    def test_create_suggestion_missing_required(self, fixer):
        """必須フィールド不足"""
        data = {
            "file": "test.py",
            "description": "Missing fields",
        }
        suggestion = fixer._create_suggestion(data, Path("default.py"))

        assert suggestion is None

    def test_create_suggestion_invalid_line(self, fixer):
        """無効な行番号"""
        data = {
            "line": "not_a_number",
            "description": "Test",
            "original": "old",
            "replacement": "new",
        }
        suggestion = fixer._create_suggestion(data, Path("default.py"))

        assert suggestion is not None
        assert suggestion.line == 1  # デフォルト値

    def test_apply_fix_success(self, fixer, tmp_path):
        """修正適用成功"""
        test_file = tmp_path / "code.py"
        test_file.write_text("x = old_value\ny = 2", encoding="utf-8")

        suggestion = FixSuggestion(
            file_path=test_file,
            line=1,
            description="Replace value",
            original="old_value",
            replacement="new_value",
        )

        result = fixer.apply_fix(suggestion)

        assert result is True
        content = test_file.read_text(encoding="utf-8")
        assert "new_value" in content
        assert "old_value" not in content

    def test_apply_fix_not_found(self, fixer, tmp_path):
        """対象文字列が見つからない"""
        test_file = tmp_path / "code.py"
        test_file.write_text("x = 1", encoding="utf-8")

        suggestion = FixSuggestion(
            file_path=test_file,
            line=1,
            description="Replace nonexistent",
            original="nonexistent_string",
            replacement="new_value",
        )

        result = fixer.apply_fix(suggestion)

        assert result is False

    def test_apply_fix_file_not_found(self, fixer, tmp_path):
        """ファイルが存在しない"""
        suggestion = FixSuggestion(
            file_path=tmp_path / "nonexistent.py",
            line=1,
            description="Fix",
            original="old",
            replacement="new",
        )

        result = fixer.apply_fix(suggestion)

        assert result is False

    @patch("devbuddy.core.fixer.subprocess.run")
    def test_suggest_fix_test_timeout(self, mock_run, fixer):
        """テスト実行タイムアウト"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pytest", timeout=120)

        result = fixer.suggest_fix(Path("test.py"))

        assert result.success is False
        assert "timed out" in result.error

    @patch("devbuddy.core.fixer.subprocess.run")
    def test_suggest_fix_test_passes(self, mock_run, fixer):
        """テストが成功する場合"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = fixer.suggest_fix(Path("test.py"))

        assert result.success is True
        assert len(result.suggestions) == 0


class TestFixSuggestion:
    """FixSuggestionテストクラス"""

    def test_creation(self):
        """FixSuggestion作成テスト"""
        suggestion = FixSuggestion(
            file_path=Path("test.py"),
            line=10,
            description="Fix bug",
            original="old code",
            replacement="new code",
            confidence=0.85,
        )

        assert suggestion.file_path == Path("test.py")
        assert suggestion.line == 10
        assert suggestion.description == "Fix bug"
        assert suggestion.confidence == 0.85

    def test_default_confidence(self):
        """デフォルトconfidence"""
        suggestion = FixSuggestion(
            file_path=Path("test.py"),
            line=1,
            description="Fix",
            original="old",
            replacement="new",
        )

        assert suggestion.confidence == 0.0


class TestFixResult:
    """FixResultテストクラス"""

    def test_success_result(self):
        """成功結果"""
        result = FixResult(
            success=True,
            suggestions=[
                FixSuggestion(
                    file_path=Path("test.py"),
                    line=1,
                    description="Fix",
                    original="old",
                    replacement="new",
                )
            ],
        )

        assert result.success is True
        assert len(result.suggestions) == 1
        assert result.error is None

    def test_error_result(self):
        """エラー結果"""
        result = FixResult(
            success=False,
            error="Test failed",
        )

        assert result.success is False
        assert result.error == "Test failed"
        assert len(result.suggestions) == 0
