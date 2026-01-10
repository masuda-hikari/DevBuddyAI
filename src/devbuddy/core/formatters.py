"""
出力フォーマッター

レビュー結果、テスト生成結果、修正提案を各種形式で出力。
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Union

from devbuddy.core.models import ReviewResult
from devbuddy.core.generator import GenerationResult
from devbuddy.core.fixer import FixResult


class OutputFormatter(ABC):
    """出力フォーマッター基底クラス"""

    @abstractmethod
    def format_review(self, results: list[ReviewResult]) -> str:
        """レビュー結果をフォーマット"""
        pass

    @abstractmethod
    def format_testgen(self, result: GenerationResult) -> str:
        """テスト生成結果をフォーマット"""
        pass

    @abstractmethod
    def format_fix(self, result: FixResult) -> str:
        """修正提案をフォーマット"""
        pass


class TextFormatter(OutputFormatter):
    """テキスト形式フォーマッター（デフォルト）"""

    def format_review(self, results: list[ReviewResult]) -> str:
        lines = []
        lines.append("=" * 50)
        lines.append("DevBuddyAI Code Review Results")
        lines.append("=" * 50)
        lines.append("")

        total_issues = {"bug": 0, "warning": 0, "style": 0, "info": 0}

        for result in results:
            if result.issues:
                lines.append(f"\n{result.file_path}")
                for issue in result.issues:
                    lines.append(
                        f"  [{issue.level.upper()}] "
                        f"Line {issue.line}: {issue.message}"
                    )
                    if issue.suggestion:
                        lines.append(f"    Suggestion: {issue.suggestion}")
                    total_issues[issue.level] = (
                        total_issues.get(issue.level, 0) + 1
                    )

        lines.append("")
        lines.append("-" * 50)
        bugs = total_issues["bug"]
        warnings = total_issues["warning"]
        styles = total_issues["style"]
        lines.append(
            f"Summary: {bugs} bugs, {warnings} warnings, {styles} style issues"
        )

        return "\n".join(lines)

    def format_testgen(self, result: GenerationResult) -> str:
        lines = []
        if result.success:
            lines.append("Generated Tests:")
            lines.append("-" * 40)
            lines.append(result.test_code)
            lines.append("")
            lines.append(f"Test count: {result.test_count}")
            if result.verified:
                lines.append("Status: Verified (all tests passed)")
            else:
                lines.append("Status: Not verified")
        else:
            lines.append(f"Error: {result.error}")
        return "\n".join(lines)

    def format_fix(self, result: FixResult) -> str:
        lines = []
        if result.suggestions:
            lines.append("Suggested Fixes:")
            for i, suggestion in enumerate(result.suggestions, 1):
                lines.append(f"\n{i}. {suggestion.description}")
                file_loc = f"{suggestion.file_path}:{suggestion.line}"
                lines.append(f"   File: {file_loc}")
                lines.append("   Change:")
                lines.append(f"   - {suggestion.original}")
                lines.append(f"   + {suggestion.replacement}")
        else:
            lines.append("No fixes suggested")
        return "\n".join(lines)


class JSONFormatter(OutputFormatter):
    """JSON形式フォーマッター"""

    def _serialize_path(
        self, obj: Union[Path, dict, list]
    ) -> Union[str, dict, list]:
        """Pathオブジェクトを文字列に変換（再帰処理）"""
        if isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: self._serialize_path(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_path(item) for item in obj]
        return obj

    def format_review(self, results: list[ReviewResult]) -> str:
        results_list: list[dict[str, Any]] = []
        summary: dict[str, int] = {
            "bug": 0,
            "warning": 0,
            "style": 0,
            "info": 0,
        }

        for result in results:
            issues_list: list[dict[str, Any]] = []
            for issue in result.issues:
                issue_data = {
                    "level": issue.level,
                    "line": issue.line,
                    "message": issue.message,
                    "suggestion": issue.suggestion,
                    "code_snippet": issue.code_snippet,
                }
                issues_list.append(issue_data)
                summary[issue.level] = summary.get(issue.level, 0) + 1

            file_data: dict[str, Any] = {
                "file_path": str(result.file_path),
                "success": result.success,
                "error": result.error,
                "issues": issues_list,
            }
            results_list.append(file_data)

        data = {
            "tool": "DevBuddyAI",
            "type": "code_review",
            "generated_at": datetime.now().isoformat(),
            "files_reviewed": len(results),
            "results": results_list,
            "summary": summary,
        }

        return json.dumps(data, ensure_ascii=False, indent=2)

    def format_testgen(self, result: GenerationResult) -> str:
        data = {
            "tool": "DevBuddyAI",
            "type": "test_generation",
            "generated_at": datetime.now().isoformat(),
            "success": result.success,
            "error": result.error,
            "test_count": result.test_count,
            "verified": result.verified,
            "test_code": result.test_code,
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def format_fix(self, result: FixResult) -> str:
        suggestions_list: list[dict[str, Any]] = []
        for suggestion in result.suggestions:
            sugg_data = {
                "file_path": str(suggestion.file_path),
                "line": suggestion.line,
                "description": suggestion.description,
                "original": suggestion.original,
                "replacement": suggestion.replacement,
                "confidence": suggestion.confidence,
            }
            suggestions_list.append(sugg_data)

        data = {
            "tool": "DevBuddyAI",
            "type": "fix_suggestions",
            "generated_at": datetime.now().isoformat(),
            "success": result.success,
            "error": result.error,
            "suggestion_count": len(result.suggestions),
            "suggestions": suggestions_list,
        }
        return json.dumps(data, ensure_ascii=False, indent=2)


class MarkdownFormatter(OutputFormatter):
    """Markdown形式フォーマッター"""

    def format_review(self, results: list[ReviewResult]) -> str:
        lines = []
        lines.append("# DevBuddyAI Code Review Report")
        lines.append("")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"**Generated:** {timestamp}")
        lines.append(f"**Files Reviewed:** {len(results)}")
        lines.append("")

        total_issues = {"bug": 0, "warning": 0, "style": 0, "info": 0}

        for result in results:
            if result.issues:
                lines.append(f"## 📄 {result.file_path}")
                lines.append("")
                lines.append("| Level | Line | Message | Suggestion |")
                lines.append("|-------|------|---------|------------|")
                for issue in result.issues:
                    level_emoji = {
                        "bug": "🔴",
                        "warning": "🟡",
                        "style": "🔵",
                        "info": "🟢",
                    }.get(issue.level, "⚪")
                    sugg = issue.suggestion or "-"
                    lines.append(
                        f"| {level_emoji} {issue.level.upper()} | "
                        f"{issue.line} | {issue.message} | {sugg} |"
                    )
                    total_issues[issue.level] = (
                        total_issues.get(issue.level, 0) + 1
                    )
                lines.append("")

        lines.append("## 📊 Summary")
        lines.append("")
        lines.append("| Category | Count |")
        lines.append("|----------|-------|")
        lines.append(f"| 🔴 Bugs | {total_issues['bug']} |")
        lines.append(f"| 🟡 Warnings | {total_issues['warning']} |")
        lines.append(f"| 🔵 Style | {total_issues['style']} |")
        lines.append(f"| 🟢 Info | {total_issues['info']} |")
        lines.append("")
        lines.append("---")
        lines.append("*Generated by DevBuddyAI*")

        return "\n".join(lines)

    def format_testgen(self, result: GenerationResult) -> str:
        lines = []
        lines.append("# DevBuddyAI Test Generation Report")
        lines.append("")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"**Generated:** {timestamp}")
        lines.append("")

        if result.success:
            status = "✅ Verified" if result.verified else "⚠️ Not Verified"
            lines.append(f"**Status:** {status}")
            lines.append(f"**Test Count:** {result.test_count}")
            lines.append("")
            lines.append("## Generated Test Code")
            lines.append("")
            lines.append("```python")
            lines.append(result.test_code)
            lines.append("```")
        else:
            lines.append("**Status:** ❌ Error")
            lines.append(f"**Error:** {result.error}")

        lines.append("")
        lines.append("---")
        lines.append("*Generated by DevBuddyAI*")

        return "\n".join(lines)

    def format_fix(self, result: FixResult) -> str:
        lines = []
        lines.append("# DevBuddyAI Fix Suggestions Report")
        lines.append("")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"**Generated:** {timestamp}")
        lines.append("")

        if result.suggestions:
            lines.append(f"**Suggestions:** {len(result.suggestions)}")
            lines.append("")

            for i, suggestion in enumerate(result.suggestions, 1):
                lines.append(f"## 🔧 Fix #{i}")
                lines.append("")
                lines.append(f"**Description:** {suggestion.description}")
                lines.append(f"**File:** `{suggestion.file_path}`")
                lines.append(f"**Line:** {suggestion.line}")
                lines.append(f"**Confidence:** {suggestion.confidence:.0%}")
                lines.append("")
                lines.append("### Change")
                lines.append("")
                lines.append("```diff")
                lines.append(f"- {suggestion.original}")
                lines.append(f"+ {suggestion.replacement}")
                lines.append("```")
                lines.append("")
        else:
            lines.append("No fixes suggested.")

        lines.append("---")
        lines.append("*Generated by DevBuddyAI*")

        return "\n".join(lines)


def get_formatter(format_type: str) -> OutputFormatter:
    """出力形式に応じたフォーマッターを取得

    Args:
        format_type: 出力形式（text, json, markdown）

    Returns:
        OutputFormatter: フォーマッターインスタンス
    """
    formatters: dict[str, type[OutputFormatter]] = {
        "text": TextFormatter,
        "json": JSONFormatter,
        "markdown": MarkdownFormatter,
        "md": MarkdownFormatter,
    }

    formatter_class = formatters.get(format_type.lower(), TextFormatter)
    return formatter_class()
