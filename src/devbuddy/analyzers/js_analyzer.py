"""
JavaScriptAnalyzer - JavaScript/TypeScript静的解析

ESLint、tsc等の静的解析ツールと統合。
"""

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from devbuddy.core.reviewer import Issue


@dataclass
class JSAnalysisConfig:
    """JavaScript/TypeScript解析設定"""

    use_eslint: bool = True
    use_tsc: bool = False
    strict_mode: bool = False
    eslint_config: Optional[str] = None


class JavaScriptAnalyzer:
    """JavaScript/TypeScript静的解析エンジン"""

    def __init__(self, config: Optional[JSAnalysisConfig] = None):
        self.config = config or JSAnalysisConfig()

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

        # パターンベース解析（常に実行）
        issues.extend(self._analyze_patterns(code))

        # 外部ツール解析（ファイルがある場合）
        if file_path and file_path.exists():
            if self.config.use_eslint:
                issues.extend(self._run_eslint(file_path))
            if self.config.use_tsc and self._is_typescript(file_path):
                issues.extend(self._run_tsc(file_path))

        return issues

    def _is_typescript(self, file_path: Path) -> bool:
        """TypeScriptファイルかどうか判定"""
        return file_path.suffix in (".ts", ".tsx")

    def _analyze_patterns(self, code: str) -> list[Issue]:
        """パターンベース解析"""
        issues = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # console.log検出
            if re.search(r"\bconsole\.(log|debug|info)\s*\(", stripped):
                issues.append(
                    Issue(
                        level="info",
                        line=i,
                        message="console.log found",
                        suggestion="Remove console.log before production",
                    )
                )

            # debugger検出
            if re.search(r"^\s*debugger\s*;?\s*$", stripped):
                issues.append(
                    Issue(
                        level="warning",
                        line=i,
                        message="debugger statement found",
                        suggestion="Remove debugger before production",
                    )
                )

            # eval検出
            if re.search(r"\beval\s*\(", stripped):
                issues.append(
                    Issue(
                        level="bug",
                        line=i,
                        message="Potentially dangerous eval() usage",
                        suggestion="Avoid eval() with untrusted input",
                    )
                )

            # == vs === 検出（非null/undefined比較）
            if re.search(r"[^!=]==[^=]", stripped):
                # null/undefined比較は許可
                if not re.search(r"==\s*(null|undefined)", stripped):
                    issues.append(
                        Issue(
                            level="style",
                            line=i,
                            message="Non-strict equality (==) used",
                            suggestion="Use strict equality (===) instead",
                        )
                    )

            # var検出
            if re.search(r"^\s*var\s+", stripped):
                issues.append(
                    Issue(
                        level="style",
                        line=i,
                        message="var keyword used",
                        suggestion="Use let or const instead of var",
                    )
                )

            # 空のcatchブロック検出
            if re.search(r"catch\s*\([^)]*\)\s*\{\s*\}", stripped):
                issues.append(
                    Issue(
                        level="warning",
                        line=i,
                        message="Empty catch block detected",
                        suggestion="Handle or log the error in catch block",
                    )
                )

            # TODO/FIXME検出
            if re.search(r"\b(TODO|FIXME|XXX)\b", stripped, re.IGNORECASE):
                issues.append(
                    Issue(
                        level="info",
                        line=i,
                        message="TODO/FIXME comment found",
                        suggestion="Address the TODO/FIXME before merging",
                    )
                )

            # 潜在的なXSS - innerHTML
            if re.search(r"\.innerHTML\s*=", stripped):
                issues.append(
                    Issue(
                        level="warning",
                        line=i,
                        message="innerHTML assignment detected",
                        suggestion="Consider using textContent or "
                        "sanitize input to prevent XSS",
                    )
                )

            # 潜在的なSQLインジェクション
            if re.search(r"(query|execute)\s*\(\s*[`'\"].*\$\{", stripped):
                issues.append(
                    Issue(
                        level="bug",
                        line=i,
                        message="Potential SQL injection vulnerability",
                        suggestion="Use parameterized queries",
                    )
                )

            # any型の使用（TypeScript）
            if re.search(r":\s*any\b", stripped):
                issues.append(
                    Issue(
                        level="style",
                        line=i,
                        message="TypeScript 'any' type used",
                        suggestion="Consider using a more specific type",
                    )
                )

        return issues

    def _run_eslint(self, file_path: Path) -> list[Issue]:
        """ESLintを実行"""
        issues: list[Issue] = []

        try:
            cmd = [
                "npx",
                "eslint",
                str(file_path),
                "--format",
                "json",
            ]

            if self.config.eslint_config:
                cmd.extend(["--config", self.config.eslint_config])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=file_path.parent,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return issues

        # ESLintのJSON出力をパース
        try:
            output = json.loads(result.stdout)
            if output and len(output) > 0:
                for message in output[0].get("messages", []):
                    sev = message.get("severity", 1)
                    level = self._eslint_severity_to_level(sev)
                    line_num = message.get("line", 1)
                    rule_id = message.get("ruleId", "unknown")
                    text = message.get("message", "")

                    issues.append(
                        Issue(
                            level=level,
                            line=line_num,
                            message=f"[{rule_id}] {text}",
                        )
                    )
        except (json.JSONDecodeError, KeyError, IndexError):
            pass

        return issues

    def _run_tsc(self, file_path: Path) -> list[Issue]:
        """TypeScriptコンパイラを実行"""
        issues: list[Issue] = []

        try:
            cmd = [
                "npx",
                "tsc",
                str(file_path),
                "--noEmit",
                "--pretty",
                "false",
            ]

            if self.config.strict_mode:
                cmd.append("--strict")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=file_path.parent,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return issues

        # tscの出力をパース
        # 形式: file.ts(line,col): error TSxxxx: message
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            pattern = r".+\((\d+),\d+\):\s*(error|warning)\s+(TS\d+):\s*(.+)"
            match = re.match(pattern, line)
            if match:
                line_num = int(match.group(1))
                severity = match.group(2)
                code = match.group(3)
                message = match.group(4)

                level = "bug" if severity == "error" else "warning"

                issues.append(
                    Issue(
                        level=level,
                        line=line_num,
                        message=f"[{code}] {message}",
                    )
                )

        return issues

    def _eslint_severity_to_level(self, severity: int) -> str:
        """ESLint severityをレベルに変換"""
        if severity == 2:
            return "bug"
        elif severity == 1:
            return "warning"
        else:
            return "info"

    def check_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        """簡易構文チェック

        Returns:
            tuple[bool, Optional[str]]: (有効か, エラーメッセージ)
        """
        # 基本的な括弧の対応をチェック
        brackets = {"(": ")", "[": "]", "{": "}"}
        stack = []
        in_string = False
        string_char = None
        escape_next = False

        for i, char in enumerate(code):
            if escape_next:
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                continue

            if char in ('"', "'", "`"):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
                continue

            if in_string:
                continue

            if char in brackets:
                stack.append((char, i))
            elif char in brackets.values():
                if not stack:
                    return False, f"Unexpected closing bracket '{char}'"
                open_bracket, _ = stack.pop()
                if brackets[open_bracket] != char:
                    msg = f"Mismatched brackets: '{open_bracket}' and '{char}'"
                    return False, msg

        if stack:
            open_bracket, pos = stack[-1]
            return False, f"Unclosed bracket '{open_bracket}'"

        return True, None

    def get_functions(self, code: str) -> list[str]:
        """コード内の関数名を取得"""
        functions = []

        # function宣言
        for match in re.finditer(r"function\s+(\w+)\s*\(", code):
            functions.append(match.group(1))

        # アロー関数（変数に代入されたもの）
        arrow_pat = r"(?:const|let|var)\s+(\w+)\s*=\s*(?:\([^)]*\)|[^=])\s*=>"
        for match in re.finditer(arrow_pat, code):
            functions.append(match.group(1))

        # メソッド（オブジェクトリテラル内）
        method_pat = r"(\w+)\s*:\s*(?:async\s+)?function\s*\("
        for match in re.finditer(method_pat, code):
            functions.append(match.group(1))

        # クラスメソッド
        class_method_pat = r"^\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{"
        for match in re.finditer(class_method_pat, code, re.MULTILINE):
            name = match.group(1)
            reserved = ("if", "for", "while", "switch", "catch", "function")
            if name not in reserved:
                functions.append(name)

        return list(set(functions))

    def get_classes(self, code: str) -> list[str]:
        """コード内のクラス名を取得"""
        classes = []

        for match in re.finditer(r"class\s+(\w+)", code):
            classes.append(match.group(1))

        return classes

    def get_exports(self, code: str) -> list[str]:
        """エクスポートされている名前を取得"""
        exports = []

        # export default
        default_pat = r"export\s+default\s+(?:class|function)?\s*(\w+)"
        for match in re.finditer(default_pat, code):
            exports.append(match.group(1))

        # export const/let/var/function/class
        for match in re.finditer(
            r"export\s+(?:const|let|var|function|class)\s+(\w+)", code
        ):
            exports.append(match.group(1))

        # export { ... }
        for match in re.finditer(r"export\s*\{([^}]+)\}", code):
            names = match.group(1).split(",")
            for name in names:
                # "name as alias" -> name
                name = name.strip().split()[0]
                exports.append(name)

        return list(set(exports))

    def get_imports(self, code: str) -> list[dict[str, str]]:
        """インポート情報を取得"""
        imports = []

        # import { ... } from '...'
        for match in re.finditer(
            r"import\s*\{([^}]+)\}\s*from\s*['\"]([^'\"]+)['\"]", code
        ):
            names = [n.strip().split()[0] for n in match.group(1).split(",")]
            for name in names:
                imports.append({"name": name, "source": match.group(2)})

        # import name from '...'
        for match in re.finditer(
            r"import\s+(\w+)\s+from\s*['\"]([^'\"]+)['\"]", code
        ):
            imports.append({"name": match.group(1), "source": match.group(2)})

        # import * as name from '...'
        for match in re.finditer(
            r"import\s*\*\s*as\s+(\w+)\s+from\s*['\"]([^'\"]+)['\"]", code
        ):
            imports.append({"name": match.group(1), "source": match.group(2)})

        return imports
