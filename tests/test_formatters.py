"""
フォーマッターテスト
"""

import json
from pathlib import Path

from devbuddy.core.formatters import (
    TextFormatter,
    JSONFormatter,
    MarkdownFormatter,
    get_formatter,
)
from devbuddy.core.models import Issue, ReviewResult
from devbuddy.core.generator import GenerationResult
from devbuddy.core.fixer import FixResult, FixSuggestion


class TestTextFormatter:
    """TextFormatterのテスト"""

    def test_format_review_with_issues(self):
        """issueありのレビュー結果フォーマット"""
        formatter = TextFormatter()
        results = [
            ReviewResult(
                file_path=Path("test.py"),
                issues=[
                    Issue(level="bug", line=10, message="Potential bug"),
                    Issue(level="warning", line=20, message="Warning here"),
                ],
            )
        ]
        output = formatter.format_review(results)
        assert "DevBuddyAI Code Review Results" in output
        assert "test.py" in output
        assert "BUG" in output
        assert "WARNING" in output
        assert "1 bugs" in output
        assert "1 warnings" in output

    def test_format_review_no_issues(self):
        """issueなしのレビュー結果フォーマット"""
        formatter = TextFormatter()
        results = [
            ReviewResult(file_path=Path("clean.py"), issues=[])
        ]
        output = formatter.format_review(results)
        assert "0 bugs" in output
        assert "0 warnings" in output

    def test_format_testgen_success(self):
        """成功したテスト生成結果フォーマット"""
        formatter = TextFormatter()
        result = GenerationResult(
            success=True,
            test_code="def test_example():\n    pass",
            test_count=1,
            verified=True,
        )
        output = formatter.format_testgen(result)
        assert "Generated Tests:" in output
        assert "def test_example():" in output
        assert "Test count: 1" in output
        assert "Verified" in output

    def test_format_testgen_failure(self):
        """失敗したテスト生成結果フォーマット"""
        formatter = TextFormatter()
        result = GenerationResult(
            success=False,
            error="File not found",
        )
        output = formatter.format_testgen(result)
        assert "Error: File not found" in output

    def test_format_fix_with_suggestions(self):
        """提案ありの修正結果フォーマット"""
        formatter = TextFormatter()
        result = FixResult(
            success=True,
            suggestions=[
                FixSuggestion(
                    file_path=Path("bug.py"),
                    line=42,
                    description="Fix division by zero",
                    original="x / 0",
                    replacement="x / 1",
                    confidence=0.9,
                )
            ],
        )
        output = formatter.format_fix(result)
        assert "Suggested Fixes:" in output
        assert "Fix division by zero" in output
        assert "bug.py:42" in output

    def test_format_fix_no_suggestions(self):
        """提案なしの修正結果フォーマット"""
        formatter = TextFormatter()
        result = FixResult(success=True, suggestions=[])
        output = formatter.format_fix(result)
        assert "No fixes suggested" in output


class TestJSONFormatter:
    """JSONFormatterのテスト"""

    def test_format_review_valid_json(self):
        """レビュー結果が有効なJSONか確認"""
        formatter = JSONFormatter()
        results = [
            ReviewResult(
                file_path=Path("test.py"),
                issues=[
                    Issue(level="bug", line=10, message="Bug here"),
                ],
            )
        ]
        output = formatter.format_review(results)
        data = json.loads(output)
        assert data["tool"] == "DevBuddyAI"
        assert data["type"] == "code_review"
        assert len(data["results"]) == 1
        assert data["results"][0]["file_path"] == "test.py"
        assert data["summary"]["bug"] == 1

    def test_format_testgen_valid_json(self):
        """テスト生成結果が有効なJSONか確認"""
        formatter = JSONFormatter()
        result = GenerationResult(
            success=True,
            test_code="def test_x(): pass",
            test_count=1,
        )
        output = formatter.format_testgen(result)
        data = json.loads(output)
        assert data["tool"] == "DevBuddyAI"
        assert data["type"] == "test_generation"
        assert data["success"] is True
        assert data["test_count"] == 1

    def test_format_fix_valid_json(self):
        """修正結果が有効なJSONか確認"""
        formatter = JSONFormatter()
        result = FixResult(
            success=True,
            suggestions=[
                FixSuggestion(
                    file_path=Path("fix.py"),
                    line=10,
                    description="Fix bug",
                    original="old",
                    replacement="new",
                )
            ],
        )
        output = formatter.format_fix(result)
        data = json.loads(output)
        assert data["tool"] == "DevBuddyAI"
        assert data["type"] == "fix_suggestions"
        assert len(data["suggestions"]) == 1
        assert data["suggestions"][0]["file_path"] == "fix.py"


class TestMarkdownFormatter:
    """MarkdownFormatterのテスト"""

    def test_format_review_markdown(self):
        """レビュー結果がMarkdown形式か確認"""
        formatter = MarkdownFormatter()
        results = [
            ReviewResult(
                file_path=Path("test.py"),
                issues=[
                    Issue(level="bug", line=10, message="Bug found"),
                ],
            )
        ]
        output = formatter.format_review(results)
        assert "# DevBuddyAI Code Review Report" in output
        assert "## " in output  # セクションヘッダ
        assert "|" in output  # テーブル
        assert "Bugs" in output

    def test_format_testgen_markdown(self):
        """テスト生成結果がMarkdown形式か確認"""
        formatter = MarkdownFormatter()
        result = GenerationResult(
            success=True,
            test_code="def test_x(): pass",
            test_count=1,
            verified=True,
        )
        output = formatter.format_testgen(result)
        assert "# DevBuddyAI Test Generation Report" in output
        assert "```python" in output
        assert "Verified" in output

    def test_format_fix_markdown(self):
        """修正結果がMarkdown形式か確認"""
        formatter = MarkdownFormatter()
        result = FixResult(
            success=True,
            suggestions=[
                FixSuggestion(
                    file_path=Path("fix.py"),
                    line=10,
                    description="Fix bug",
                    original="old",
                    replacement="new",
                )
            ],
        )
        output = formatter.format_fix(result)
        assert "# DevBuddyAI Fix Suggestions Report" in output
        assert "```diff" in output
        assert "- old" in output
        assert "+ new" in output


class TestGetFormatter:
    """get_formatter関数のテスト"""

    def test_get_text_formatter(self):
        """textでTextFormatterを取得"""
        formatter = get_formatter("text")
        assert isinstance(formatter, TextFormatter)

    def test_get_json_formatter(self):
        """jsonでJSONFormatterを取得"""
        formatter = get_formatter("json")
        assert isinstance(formatter, JSONFormatter)

    def test_get_markdown_formatter(self):
        """markdownでMarkdownFormatterを取得"""
        formatter = get_formatter("markdown")
        assert isinstance(formatter, MarkdownFormatter)

    def test_get_md_formatter(self):
        """mdでMarkdownFormatterを取得"""
        formatter = get_formatter("md")
        assert isinstance(formatter, MarkdownFormatter)

    def test_get_unknown_formatter_defaults_to_text(self):
        """不明な形式はTextFormatterにフォールバック"""
        formatter = get_formatter("unknown")
        assert isinstance(formatter, TextFormatter)

    def test_get_formatter_case_insensitive(self):
        """大文字小文字を区別しない"""
        formatter = get_formatter("JSON")
        assert isinstance(formatter, JSONFormatter)
