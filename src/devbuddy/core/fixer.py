"""
BugFixer - AIバグ修正エンジン

失敗テストや既知バグに対する修正を提案。
自己検証ループにより、修正の品質を保証。
"""

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from devbuddy.llm.client import LLMClient
from devbuddy.llm.prompts import PromptTemplates


@dataclass
class FixSuggestion:
    """修正提案"""

    file_path: Path
    line: int
    description: str
    original: str
    replacement: str
    confidence: float = 0.0
    category: str = "unknown"  # bug, style, performance, security


@dataclass
class FixVerificationReport:
    """修正検証レポート"""

    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    fixed_count: int = 0
    remaining_issues: list[str] = field(default_factory=list)
    applied_suggestions: list[str] = field(default_factory=list)


@dataclass
class FixResult:
    """修正結果"""

    success: bool
    suggestions: list[FixSuggestion] = field(default_factory=list)
    error: Optional[str] = None
    verified: bool = False
    attempts: int = 1
    verification_report: Optional[FixVerificationReport] = None


class BugFixer:
    """AIバグ修正エンジン

    失敗テストや既知バグに対する修正を提案し、
    自己検証ループで修正の品質を保証する。
    """

    # 言語別テストランナー設定
    TEST_RUNNERS: dict[str, dict[str, list[str]]] = {
        "python": {
            "cmd": ["pytest", "-v", "--tb=long"],
            "extensions": [".py"],
        },
        "javascript": {
            "cmd": ["npm", "test", "--"],
            "extensions": [".js", ".jsx", ".ts", ".tsx"],
        },
        "rust": {
            "cmd": ["cargo", "test", "--"],
            "extensions": [".rs"],
        },
        "go": {
            "cmd": ["go", "test", "-v"],
            "extensions": [".go"],
        },
    }

    def __init__(self, client: LLMClient):
        self.client = client
        self.prompts = PromptTemplates()
        self.max_retry = 3

    def detect_language(self, file_path: Path) -> str:
        """ファイル拡張子から言語を検出"""
        ext = file_path.suffix.lower()
        for lang, config in self.TEST_RUNNERS.items():
            if ext in config["extensions"]:
                return lang
        return "python"  # デフォルト

    def get_test_command(
        self, language: str, test_path: Path
    ) -> list[str]:
        """言語に応じたテストコマンドを取得"""
        config = self.TEST_RUNNERS.get(language, self.TEST_RUNNERS["python"])
        cmd = config["cmd"].copy()
        cmd.append(str(test_path))
        return cmd

    def suggest_fix(
        self,
        test_path: Path,
        source_path: Optional[Path] = None,
        language: Optional[str] = None,
    ) -> FixResult:
        """失敗テストに対する修正を提案

        Args:
            test_path: テストファイルパス
            source_path: ソースファイルパス（推測可能な場合は省略可）
            language: プログラミング言語（省略時は自動検出）

        Returns:
            FixResult: 修正提案
        """
        # 言語を検出
        lang = language or self.detect_language(test_path)

        # テストを実行して失敗情報を取得
        try:
            cmd = self.get_test_command(lang, test_path)
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            return FixResult(success=False, error="Test execution timed out")
        except Exception as e:
            return FixResult(success=False, error=str(e))

        if proc.returncode == 0:
            return FixResult(success=True, suggestions=[])

        # テストコードを読み込み
        try:
            with open(test_path, encoding="utf-8") as f:
                test_code = f.read()
        except Exception as e:
            return FixResult(
                success=False, error=f"Failed to read test file: {e}"
            )

        # ソースコードを読み込み（指定されている場合）
        source_code = None
        if source_path and source_path.exists():
            try:
                with open(source_path, encoding="utf-8") as f:
                    source_code = f.read()
            except Exception:
                pass

        # エラー出力を解析してコンテキストを構築
        error_output = proc.stdout + proc.stderr
        error_context = self._build_error_context(error_output, lang)

        # AIに修正提案を依頼
        prompt = self.prompts.bug_fix(
            test_code=test_code,
            error_output=error_context,
            source_code=source_code,
        )

        try:
            response = self.client.complete(prompt)
            path_for_parse = source_path or test_path
            suggestions = self._parse_fix_response(response, path_for_parse)
        except Exception as e:
            return FixResult(success=False, error=str(e))

        return FixResult(success=True, suggestions=suggestions)

    def suggest_and_verify(
        self,
        test_path: Path,
        source_path: Optional[Path] = None,
        language: Optional[str] = None,
        auto_apply: bool = False,
    ) -> FixResult:
        """修正を提案し、適用して検証（自己検証ループ）

        Args:
            test_path: テストファイルパス
            source_path: ソースファイルパス
            language: プログラミング言語
            auto_apply: 修正を自動適用するか

        Returns:
            FixResult: 修正・検証結果
        """
        result = FixResult(success=False)
        lang = language or self.detect_language(test_path)
        applied_suggestions: list[str] = []

        for attempt in range(self.max_retry):
            result = self.suggest_fix(test_path, source_path, lang)
            result.attempts = attempt + 1

            if not result.success:
                return result

            if not result.suggestions:
                # 修正提案がない（テスト成功）
                result.verified = True
                return result

            if auto_apply:
                # 修正を適用
                for suggestion in result.suggestions:
                    if self.apply_fix(suggestion):
                        applied_suggestions.append(suggestion.description)

                # テストを再実行して検証
                try:
                    cmd = self.get_test_command(lang, test_path)
                    proc = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )

                    # 検証レポートを作成
                    report = self._parse_test_output(proc.stdout + proc.stderr)
                    report.applied_suggestions = applied_suggestions.copy()
                    report.fixed_count = len(applied_suggestions)
                    result.verification_report = report

                    if proc.returncode == 0:
                        result.verified = True
                        return result

                    # 失敗した場合、残りの問題を記録
                    report.remaining_issues = self._extract_remaining_issues(
                        proc.stdout + proc.stderr
                    )

                except subprocess.TimeoutExpired:
                    result.error = "Verification timed out"
                    return result
                except Exception as e:
                    result.error = str(e)
                    return result
            else:
                # auto_apply=False の場合は提案のみ返す
                return result

        return result

    def apply_fix(self, suggestion: FixSuggestion) -> bool:
        """修正を適用

        Args:
            suggestion: 修正提案

        Returns:
            bool: 適用成功
        """
        try:
            with open(suggestion.file_path, encoding="utf-8") as f:
                content = f.read()

            if suggestion.original not in content:
                return False

            new_content = content.replace(
                suggestion.original,
                suggestion.replacement,
                1,
            )

            with open(suggestion.file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return True
        except Exception:
            return False

    def _parse_fix_response(
        self, response: str, default_path: Path
    ) -> list[FixSuggestion]:
        """AIレスポンスを解析して修正提案リストに変換"""
        suggestions: list[Optional[FixSuggestion]] = []

        # レスポンスをパース
        # 期待形式:
        # FILE: path/to/file.py
        # LINE: 42
        # DESCRIPTION: 説明
        # ORIGINAL: 元のコード
        # REPLACEMENT: 修正後のコード

        current: dict[str, str] = {}
        lines = response.strip().split("\n")

        for line in lines:
            line = line.strip()
            if line.startswith("FILE:"):
                if current:
                    sugg = self._create_suggestion(current, default_path)
                    suggestions.append(sugg)
                current = {"file": line[5:].strip()}
            elif line.startswith("LINE:"):
                current["line"] = line[5:].strip()
            elif line.startswith("DESCRIPTION:"):
                current["description"] = line[12:].strip()
            elif line.startswith("ORIGINAL:"):
                current["original"] = line[9:].strip()
            elif line.startswith("REPLACEMENT:"):
                current["replacement"] = line[12:].strip()

        if current:
            suggestions.append(self._create_suggestion(current, default_path))

        return [s for s in suggestions if s is not None]

    def _create_suggestion(
        self, data: dict[str, str], default_path: Path
    ) -> Optional[FixSuggestion]:
        """辞書からFixSuggestionを作成"""
        required_keys = ["description", "original", "replacement"]
        if not all(k in data for k in required_keys):
            return None

        try:
            file_path = Path(data.get("file", str(default_path)))
            line = int(data.get("line", 1))
        except (ValueError, TypeError):
            file_path = default_path
            line = 1

        # カテゴリを検出
        category = self._detect_category(data["description"])

        # 信頼度を抽出
        confidence = self._extract_confidence(data)

        return FixSuggestion(
            file_path=file_path,
            line=line,
            description=data["description"],
            original=data["original"],
            replacement=data["replacement"],
            confidence=confidence,
            category=category,
        )

    def _detect_category(self, description: str) -> str:
        """説明文からカテゴリを検出

        優先順位: security > performance > style > bug > unknown
        """
        desc_lower = description.lower()

        # セキュリティは最優先
        if any(w in desc_lower for w in ["security", "injection", "xss", "csrf"]):
            return "security"
        # パフォーマンスは次に優先
        if any(w in desc_lower for w in ["performance", "optimize", "slow", "fast"]):
            return "performance"
        # スタイル
        if any(w in desc_lower for w in ["style", "format", "naming"]):
            return "style"
        # 一般的なバグ
        if any(w in desc_lower for w in ["bug", "error", "fix", "crash"]):
            return "bug"

        return "unknown"

    def _extract_confidence(self, data: dict[str, str]) -> float:
        """データから信頼度を抽出"""
        # CONFIDENCE: 0.85 形式を検出
        if "confidence" in data:
            try:
                return float(data["confidence"])
            except ValueError:
                pass

        # 説明文から推測
        desc = data.get("description", "").lower()
        if any(w in desc for w in ["critical", "must", "definitely"]):
            return 0.9
        if any(w in desc for w in ["likely", "probably", "should"]):
            return 0.7
        if any(w in desc for w in ["might", "could", "consider"]):
            return 0.5

        return 0.6  # デフォルト

    def _build_error_context(self, output: str, language: str) -> str:
        """エラー出力から構造化コンテキストを構築"""
        context_parts = [
            f"=== エラー解析 (言語: {language}) ===",
            "",
        ]

        # テスト結果サマリーを抽出
        report = self._parse_test_output(output)
        context_parts.append(
            f"テスト結果: 成功={report.passed}, "
            f"失敗={report.failed}, エラー={report.errors}"
        )
        context_parts.append("")

        # 失敗テストを抽出
        if report.remaining_issues:
            context_parts.append("失敗したテスト:")
            for issue in report.remaining_issues[:5]:
                context_parts.append(f"  - {issue}")
            context_parts.append("")

        # スタックトレースを抽出
        stack_traces = self._extract_stack_traces(output)
        if stack_traces:
            context_parts.append("スタックトレース:")
            for trace in stack_traces[:3]:
                context_parts.append(trace)
            context_parts.append("")

        context_parts.append("=== 完全な出力 ===")
        context_parts.append(output)

        return "\n".join(context_parts)

    def _parse_test_output(self, output: str) -> FixVerificationReport:
        """テスト出力を解析してレポートを生成"""
        report = FixVerificationReport()

        # pytest形式: "5 passed, 2 failed, 1 error in 0.53s"
        summary_match = re.search(
            r"(\d+) passed(?:.*?(\d+) failed)?(?:.*?(\d+) error)?",
            output,
            re.IGNORECASE
        )
        if summary_match:
            report.passed = int(summary_match.group(1) or 0)
            report.failed = int(summary_match.group(2) or 0)
            report.errors = int(summary_match.group(3) or 0)

        # skipped の解析
        skipped_match = re.search(r"(\d+) skipped", output, re.IGNORECASE)
        if skipped_match:
            report.skipped = int(skipped_match.group(1))

        # 失敗テスト名を抽出
        report.remaining_issues = self._extract_remaining_issues(output)

        return report

    def _extract_remaining_issues(self, output: str) -> list[str]:
        """出力から残りの問題を抽出"""
        issues: list[str] = []

        # pytest形式: "FAILED test_example.py::test_func - AssertionError"
        failed_matches = re.findall(
            r"FAILED\s+([\w./]+::\w+)",
            output
        )
        issues.extend(failed_matches)

        # ERROR形式
        error_matches = re.findall(
            r"ERROR\s+([\w./]+::\w+)",
            output
        )
        issues.extend(error_matches)

        return issues[:10]  # 最大10件

    def _extract_stack_traces(self, output: str) -> list[str]:
        """スタックトレースを抽出"""
        traces: list[str] = []

        # Pythonスタックトレース
        trace_pattern = r"(Traceback.*?(?=\n\n|\Z))"
        matches = re.findall(trace_pattern, output, re.DOTALL)
        traces.extend(matches[:3])

        # 短いエラー行
        error_lines = re.findall(r"(E\s+.+)", output)
        if not traces and error_lines:
            traces.extend(error_lines[:5])

        return traces
