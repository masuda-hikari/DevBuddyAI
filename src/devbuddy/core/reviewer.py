"""
CodeReviewer - AIコードレビューエンジン

コードを解析し、バグ、スタイル問題、改善点を検出。
"""

from pathlib import Path

from devbuddy.core.models import Issue, ReviewResult
from devbuddy.llm.client import LLMClient
from devbuddy.llm.prompts import PromptTemplates


class CodeReviewer:
    """AIコードレビューエンジン"""

    def __init__(self, client: LLMClient):
        self.client = client
        self._analyzer = None
        self.prompts = PromptTemplates()

    @property
    def analyzer(self):
        """遅延インポートでPythonAnalyzerを取得"""
        if self._analyzer is None:
            from devbuddy.analyzers.python_analyzer import PythonAnalyzer
            self._analyzer = PythonAnalyzer()
        return self._analyzer

    def review_file(
        self,
        file_path: Path,
        severity: str = "medium",
    ) -> ReviewResult:
        """ファイルをレビュー

        Args:
            file_path: レビュー対象ファイル
            severity: 重要度フィルタ (low/medium/high)

        Returns:
            ReviewResult: レビュー結果
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                code = f.read()
        except Exception as e:
            return ReviewResult(
                file_path=file_path,
                success=False,
                error=f"Failed to read file: {e}",
            )

        # 静的解析を実行
        static_issues = self.analyzer.analyze(code, file_path)

        # AIレビューを実行
        prompt = self.prompts.code_review(
            code=code,
            language="python",
            severity=severity,
        )

        try:
            ai_response = self.client.complete(prompt)
            ai_issues = self._parse_ai_response(ai_response)
        except Exception:
            # AIエラーは無視して静的解析結果のみ返す
            ai_issues = []

        # 結果をマージ
        all_issues = static_issues + ai_issues
        filtered_issues = self._filter_by_severity(all_issues, severity)

        return ReviewResult(
            file_path=file_path,
            issues=filtered_issues,
            summary=self._generate_summary(filtered_issues),
        )

    def review_diff(self, diff_content: str) -> ReviewResult:
        """git diffをレビュー

        Args:
            diff_content: diff内容

        Returns:
            ReviewResult: レビュー結果
        """
        prompt = self.prompts.diff_review(diff=diff_content)

        try:
            response = self.client.complete(prompt)
            issues = self._parse_ai_response(response)
        except Exception as e:
            return ReviewResult(
                file_path=Path("diff"),
                success=False,
                error=str(e),
            )

        return ReviewResult(
            file_path=Path("diff"),
            issues=issues,
        )

    def _parse_ai_response(self, response: str) -> list[Issue]:
        """AIレスポンスを解析してIssueリストに変換"""
        issues = []

        lines = response.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 簡易パース例: [LEVEL] Line N: message
            if line.startswith("["):
                try:
                    level_end = line.index("]")
                    level = line[1:level_end].lower()

                    rest = line[level_end + 1 :].strip()
                    if rest.startswith("Line "):
                        line_end = rest.index(":")
                        line_num = int(rest[5:line_end])
                        message = rest[line_end + 1 :].strip()

                        issues.append(
                            Issue(
                                level=level,
                                line=line_num,
                                message=message,
                            )
                        )
                except (ValueError, IndexError):
                    continue

        return issues

    def _filter_by_severity(
        self, issues: list[Issue], severity: str
    ) -> list[Issue]:
        """重要度でフィルタリング"""
        severity_order = {"bug": 4, "warning": 3, "style": 2, "info": 1}
        min_level = {"high": 4, "medium": 2, "low": 1}.get(severity, 2)

        return [
            issue
            for issue in issues
            if severity_order.get(issue.level, 0) >= min_level
        ]

    def _generate_summary(self, issues: list[Issue]) -> str:
        """サマリー生成"""
        counts = {}
        for issue in issues:
            counts[issue.level] = counts.get(issue.level, 0) + 1

        parts = []
        for level in ["bug", "warning", "style", "info"]:
            if level in counts:
                parts.append(f"{counts[level]} {level}s")

        return ", ".join(parts) if parts else "No issues found"
