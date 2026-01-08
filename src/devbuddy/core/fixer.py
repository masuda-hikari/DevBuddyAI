"""
BugFixer - AIバグ修正エンジン

失敗テストや既知バグに対する修正を提案。
"""

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


@dataclass
class FixResult:
    """修正結果"""

    success: bool
    suggestions: list[FixSuggestion] = field(default_factory=list)
    error: Optional[str] = None


class BugFixer:
    """AIバグ修正エンジン"""

    def __init__(self, client: LLMClient):
        self.client = client
        self.prompts = PromptTemplates()

    def suggest_fix(
        self,
        test_path: Path,
        source_path: Optional[Path] = None,
    ) -> FixResult:
        """失敗テストに対する修正を提案

        Args:
            test_path: テストファイルパス
            source_path: ソースファイルパス（推測可能な場合は省略可）

        Returns:
            FixResult: 修正提案
        """
        # テストを実行して失敗情報を取得
        try:
            proc = subprocess.run(
                ["pytest", str(test_path), "-v", "--tb=long"],
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

        # AIに修正提案を依頼
        prompt = self.prompts.bug_fix(
            test_code=test_code,
            error_output=proc.stdout + proc.stderr,
            source_code=source_code,
        )

        try:
            response = self.client.complete(prompt)
            path_for_parse = source_path or test_path
            suggestions = self._parse_fix_response(response, path_for_parse)
        except Exception as e:
            return FixResult(success=False, error=str(e))

        return FixResult(success=True, suggestions=suggestions)

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

        return FixSuggestion(
            file_path=file_path,
            line=line,
            description=data["description"],
            original=data["original"],
            replacement=data["replacement"],
        )
