"""
PythonAnalyzer - Python静的解析

flake8、mypy等の静的解析ツールと統合。
"""

import ast
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from devbuddy.core.reviewer import Issue


@dataclass
class AnalysisConfig:
    """解析設定"""

    use_flake8: bool = True
    use_mypy: bool = False
    use_pylint: bool = False
    max_line_length: int = 120
    ignore_codes: list[str] | None = None


class PythonAnalyzer:
    """Python静的解析エンジン"""

    def __init__(self, config: Optional[AnalysisConfig] = None):
        self.config = config or AnalysisConfig()

    def analyze(
        self,
        code: str,
        file_path: Optional[Path] = None,
    ) -> list[Issue]:
        """コードを解析してIssueリストを返す

        Args:
            code: ソースコード
            file_path: ファイルパス（外部ツール用）

        Returns:
            list[Issue]: 検出された問題
        """
        issues = []

        # AST解析
        issues.extend(self._analyze_ast(code))

        # 外部ツール解析（ファイルがある場合）
        if file_path and file_path.exists():
            if self.config.use_flake8:
                issues.extend(self._run_flake8(file_path))
            if self.config.use_mypy:
                issues.extend(self._run_mypy(file_path))

        return issues

    def _analyze_ast(self, code: str) -> list[Issue]:
        """AST解析"""
        issues = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return [
                Issue(
                    level="bug",
                    line=e.lineno or 1,
                    message=f"Syntax error: {e.msg}",
                )
            ]

        for node in ast.walk(tree):
            # bare except検出
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append(
                    Issue(
                        level="warning",
                        line=node.lineno,
                        message="Bare except clause detected",
                        suggestion="Specify exception type "
                        "(e.g., except Exception:)",
                    )
                )

            # mutable default argument検出
            if isinstance(node, ast.FunctionDef):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        issues.append(
                            Issue(
                                level="warning",
                                line=node.lineno,
                                message=f"Mutable default argument "
                                f"in function '{node.name}'",
                                suggestion="Use None as default "
                                "and initialize inside function",
                            )
                        )

            # assert in non-test code
            if isinstance(node, ast.Assert):
                issues.append(
                    Issue(
                        level="info",
                        line=node.lineno,
                        message="Assert statement found",
                        suggestion="Consider using proper error handling "
                        "in production code",
                    )
                )

            # global statement検出
            if isinstance(node, ast.Global):
                issues.append(
                    Issue(
                        level="style",
                        line=node.lineno,
                        message="Global statement used",
                        suggestion="Consider using class attributes "
                        "or function parameters instead",
                    )
                )

            # exec/eval検出
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ("exec", "eval"):
                        issues.append(
                            Issue(
                                level="bug",
                                line=node.lineno,
                                message=f"Potentially dangerous "
                                f"{node.func.id}() usage",
                                suggestion="Avoid exec/eval "
                                "with untrusted input",
                            )
                        )

        return issues

    def _run_flake8(self, file_path: Path) -> list[Issue]:
        """flake8を実行"""
        issues: list[Issue] = []

        try:
            result = subprocess.run(
                [
                    "flake8",
                    str(file_path),
                    f"--max-line-length={self.config.max_line_length}",
                    "--format=%(row)d:%(col)d:%(code)s:%(text)s",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return issues

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            try:
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    row = int(parts[0])
                    code = parts[2]
                    text = parts[3]

                    # コードに基づいてレベル判定
                    level = self._flake8_code_to_level(code)

                    # 無視リストチェック
                    if self.config.ignore_codes:
                        if code in self.config.ignore_codes:
                            continue

                    issues.append(
                        Issue(
                            level=level,
                            line=row,
                            message=f"[{code}] {text}",
                        )
                    )
            except (ValueError, IndexError):
                continue

        return issues

    def _run_mypy(self, file_path: Path) -> list[Issue]:
        """mypyを実行"""
        issues: list[Issue] = []

        try:
            result = subprocess.run(
                [
                    "mypy",
                    str(file_path),
                    "--no-error-summary",
                    "--show-column-numbers",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return issues

        for line in result.stdout.strip().split("\n"):
            if not line or "error:" not in line:
                continue

            try:
                # 形式: file.py:line:col: error: message
                parts = line.split(":", 4)
                if len(parts) >= 5:
                    row = int(parts[1])
                    message = parts[4].strip()

                    issues.append(
                        Issue(
                            level="warning",
                            line=row,
                            message=f"[mypy] {message}",
                        )
                    )
            except (ValueError, IndexError):
                continue

        return issues

    def _flake8_code_to_level(self, code: str) -> str:
        """flake8エラーコードをレベルに変換"""
        if code.startswith("E9") or code.startswith("F"):
            # 構文エラー、未定義など
            return "bug"
        elif code.startswith("E"):
            # スタイルエラー
            return "style"
        elif code.startswith("W"):
            # 警告
            return "warning"
        elif code.startswith("C"):
            # 複雑度
            return "info"
        else:
            return "info"

    def check_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        """構文チェック

        Returns:
            tuple[bool, Optional[str]]: (有効か, エラーメッセージ)
        """
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}"

    def get_functions(self, code: str) -> list[str]:
        """コード内の関数名を取得"""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)

        return functions

    def get_classes(self, code: str) -> list[str]:
        """コード内のクラス名を取得"""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)

        return classes
