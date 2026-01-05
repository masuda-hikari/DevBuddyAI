"""
CodeReviewerのテスト
"""

import pytest
from pathlib import Path

from devbuddy.core.reviewer import CodeReviewer, Issue, ReviewResult
from devbuddy.llm.client import MockLLMClient


class TestCodeReviewer:
    """CodeReviewerテストクラス"""

    @pytest.fixture
    def reviewer(self, mock_llm_client):
        """レビュアーインスタンス"""
        return CodeReviewer(client=mock_llm_client)

    def test_review_file_success(self, reviewer, temp_python_file):
        """ファイルレビュー成功テスト"""
        result = reviewer.review_file(temp_python_file)

        assert isinstance(result, ReviewResult)
        assert result.success is True
        assert result.file_path == temp_python_file

    def test_review_file_not_found(self, reviewer):
        """存在しないファイルのレビュー"""
        result = reviewer.review_file(Path("/nonexistent/file.py"))

        assert result.success is False
        assert "Failed to read file" in result.error

    def test_review_with_severity_filter(self, reviewer, temp_python_file):
        """重要度フィルタテスト"""
        result_low = reviewer.review_file(temp_python_file, severity="low")
        result_high = reviewer.review_file(temp_python_file, severity="high")

        # highの方がissueが少ないはず
        assert len(result_high.issues) <= len(result_low.issues)

    def test_parse_ai_response(self, reviewer):
        """AIレスポンスパースのテスト"""
        response = """[BUG] Line 5: Division by zero possible
[WARNING] Line 10: Unused variable
[STYLE] Line 15: Missing docstring"""

        issues = reviewer._parse_ai_response(response)

        assert len(issues) == 3
        assert issues[0].level == "bug"
        assert issues[0].line == 5
        assert issues[1].level == "warning"
        assert issues[2].level == "style"

    def test_filter_by_severity(self, reviewer):
        """重要度フィルタリングテスト"""
        issues = [
            Issue(level="bug", line=1, message="Critical bug"),
            Issue(level="warning", line=2, message="Warning"),
            Issue(level="style", line=3, message="Style issue"),
            Issue(level="info", line=4, message="Info"),
        ]

        # highはbugのみ
        high_issues = reviewer._filter_by_severity(issues, "high")
        assert len(high_issues) == 1
        assert high_issues[0].level == "bug"

        # mediumはbug, warning, style
        medium_issues = reviewer._filter_by_severity(issues, "medium")
        assert len(medium_issues) == 3

        # lowは全て
        low_issues = reviewer._filter_by_severity(issues, "low")
        assert len(low_issues) == 4

    def test_generate_summary(self, reviewer):
        """サマリー生成テスト"""
        issues = [
            Issue(level="bug", line=1, message="Bug 1"),
            Issue(level="bug", line=2, message="Bug 2"),
            Issue(level="warning", line=3, message="Warning"),
        ]

        summary = reviewer._generate_summary(issues)

        assert "2 bugs" in summary
        assert "1 warnings" in summary

    def test_empty_issues_summary(self, reviewer):
        """問題なしのサマリー"""
        summary = reviewer._generate_summary([])
        assert summary == "No issues found"
