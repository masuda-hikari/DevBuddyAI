"""
BugFixerのテスト
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from devbuddy.core.fixer import (
    BugFixer,
    FixSuggestion,
    FixResult,
    FixVerificationReport,
)
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

    def test_detect_language_python(self, fixer):
        """Python言語検出"""
        assert fixer.detect_language(Path("test.py")) == "python"

    def test_detect_language_javascript(self, fixer):
        """JavaScript言語検出"""
        assert fixer.detect_language(Path("test.js")) == "javascript"
        assert fixer.detect_language(Path("test.ts")) == "javascript"
        assert fixer.detect_language(Path("test.tsx")) == "javascript"

    def test_detect_language_rust(self, fixer):
        """Rust言語検出"""
        assert fixer.detect_language(Path("test.rs")) == "rust"

    def test_detect_language_go(self, fixer):
        """Go言語検出"""
        assert fixer.detect_language(Path("test.go")) == "go"

    def test_detect_language_unknown(self, fixer):
        """未知の拡張子はPythonにフォールバック"""
        assert fixer.detect_language(Path("test.xyz")) == "python"

    def test_get_test_command_python(self, fixer):
        """Pythonテストコマンド取得"""
        cmd = fixer.get_test_command("python", Path("test.py"))
        assert cmd[0] == "pytest"
        assert "test.py" in cmd[-1]

    def test_get_test_command_rust(self, fixer):
        """Rustテストコマンド取得"""
        cmd = fixer.get_test_command("rust", Path("test.rs"))
        assert cmd[0] == "cargo"
        assert cmd[1] == "test"

    def test_detect_category_bug(self, fixer):
        """バグカテゴリ検出"""
        assert fixer._detect_category("Fix division bug") == "bug"
        assert fixer._detect_category("Error handling") == "bug"

    def test_detect_category_security(self, fixer):
        """セキュリティカテゴリ検出"""
        assert fixer._detect_category("SQL injection fix") == "security"
        assert fixer._detect_category("XSS vulnerability") == "security"

    def test_detect_category_performance(self, fixer):
        """パフォーマンスカテゴリ検出"""
        assert fixer._detect_category("Optimize loop") == "performance"
        assert fixer._detect_category("Slow query fix") == "performance"

    def test_detect_category_style(self, fixer):
        """スタイルカテゴリ検出"""
        assert fixer._detect_category("Format code") == "style"
        assert fixer._detect_category("Naming convention") == "style"

    def test_detect_category_unknown(self, fixer):
        """不明カテゴリ"""
        assert fixer._detect_category("Some change") == "unknown"

    def test_extract_confidence_explicit(self, fixer):
        """明示的な信頼度抽出"""
        data = {"confidence": "0.85", "description": "test"}
        assert fixer._extract_confidence(data) == 0.85

    def test_extract_confidence_from_description(self, fixer):
        """説明文からの信頼度推測"""
        assert fixer._extract_confidence(
            {"description": "This is a critical fix"}
        ) == 0.9
        assert fixer._extract_confidence(
            {"description": "This likely fixes the issue"}
        ) == 0.7
        assert fixer._extract_confidence(
            {"description": "This might help"}
        ) == 0.5

    def test_extract_confidence_default(self, fixer):
        """デフォルト信頼度"""
        assert fixer._extract_confidence({"description": "Some fix"}) == 0.6

    def test_parse_test_output(self, fixer):
        """テスト出力解析"""
        output = "5 passed, 2 failed, 1 error in 0.53s"
        report = fixer._parse_test_output(output)

        assert report.passed == 5
        assert report.failed == 2
        assert report.errors == 1

    def test_parse_test_output_with_skipped(self, fixer):
        """skippedを含む出力解析"""
        output = "3 passed, 1 skipped in 0.5s"
        report = fixer._parse_test_output(output)

        assert report.passed == 3
        assert report.skipped == 1

    def test_extract_remaining_issues(self, fixer):
        """残り問題の抽出"""
        output = """
        FAILED test_example.py::test_func1 - AssertionError
        FAILED test_example.py::test_func2 - ValueError
        ERROR test_example.py::test_func3 - ImportError
        """
        issues = fixer._extract_remaining_issues(output)

        assert len(issues) == 3
        assert "test_example.py::test_func1" in issues
        assert "test_example.py::test_func3" in issues

    def test_extract_stack_traces(self, fixer):
        """スタックトレース抽出"""
        output = """
        Traceback (most recent call last):
          File "test.py", line 10, in test_func
            result = func()
        ValueError: invalid value

        """
        traces = fixer._extract_stack_traces(output)

        assert len(traces) >= 1

    def test_build_error_context(self, fixer):
        """エラーコンテキスト構築"""
        output = "1 passed, 1 failed in 0.5s\nFAILED test.py::test_func"
        context = fixer._build_error_context(output, "python")

        assert "エラー解析" in context
        assert "python" in context
        assert "失敗=1" in context

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
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd="pytest", timeout=120
        )

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

    def test_verified_result(self):
        """検証済み結果"""
        result = FixResult(
            success=True,
            verified=True,
            attempts=2,
        )

        assert result.verified is True
        assert result.attempts == 2

    def test_result_with_verification_report(self):
        """検証レポート付き結果"""
        report = FixVerificationReport(
            passed=5,
            failed=0,
            fixed_count=2,
            applied_suggestions=["Fix 1", "Fix 2"],
        )
        result = FixResult(
            success=True,
            verified=True,
            verification_report=report,
        )

        assert result.verification_report is not None
        assert result.verification_report.fixed_count == 2
        assert len(result.verification_report.applied_suggestions) == 2


class TestFixVerificationReport:
    """FixVerificationReportテストクラス"""

    def test_default_values(self):
        """デフォルト値"""
        report = FixVerificationReport()

        assert report.passed == 0
        assert report.failed == 0
        assert report.errors == 0
        assert report.skipped == 0
        assert report.fixed_count == 0
        assert len(report.remaining_issues) == 0
        assert len(report.applied_suggestions) == 0

    def test_with_values(self):
        """値設定"""
        report = FixVerificationReport(
            passed=10,
            failed=2,
            errors=1,
            fixed_count=3,
            remaining_issues=["issue1", "issue2"],
            applied_suggestions=["fix1", "fix2", "fix3"],
        )

        assert report.passed == 10
        assert report.failed == 2
        assert report.fixed_count == 3
        assert len(report.remaining_issues) == 2
        assert len(report.applied_suggestions) == 3
