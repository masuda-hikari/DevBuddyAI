"""
GoAnalyzer - Go静的解析

go vet、staticcheck等の静的解析ツールと統合。
"""

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from devbuddy.core.reviewer import Issue


@dataclass
class GoAnalysisConfig:
    """Go解析設定"""

    use_go_vet: bool = True
    use_staticcheck: bool = False
    use_golangci_lint: bool = False
    timeout: int = 120


class GoAnalyzer:
    """Go静的解析エンジン"""

    def __init__(self, config: Optional[GoAnalysisConfig] = None):
        self.config = config or GoAnalysisConfig()

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
            if self.config.use_go_vet:
                issues.extend(self._run_go_vet(file_path))
            if self.config.use_staticcheck:
                issues.extend(self._run_staticcheck(file_path))
            if self.config.use_golangci_lint:
                issues.extend(self._run_golangci_lint(file_path))

        return issues

    def _analyze_patterns(self, code: str) -> list[Issue]:
        """パターンベース解析"""
        issues = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # panic()の使用検出
            if re.search(r"\bpanic\s*\(", stripped):
                # テストファイル内は許容
                issues.append(
                    Issue(
                        level="warning",
                        line=i,
                        message="panic() usage detected",
                        suggestion="Consider returning an error instead "
                        "of panicking in production code",
                    )
                )

            # recover()の不適切な使用
            if re.search(r"\brecover\s*\(\s*\)", stripped):
                issues.append(
                    Issue(
                        level="info",
                        line=i,
                        message="recover() usage detected",
                        suggestion="Ensure recover() is only used for "
                        "graceful shutdown, not to hide bugs",
                    )
                )

            # fmt.Print*の使用（ロギングの代わりに）
            if re.search(r"\bfmt\.(Print|Printf|Println)\s*\(", stripped):
                issues.append(
                    Issue(
                        level="info",
                        line=i,
                        message="fmt.Print* usage detected",
                        suggestion="Consider using a proper logging package "
                        "(log, zerolog, zap) instead of fmt.Print*",
                    )
                )

            # エラーの無視検出（_ = err パターン）
            if re.search(r"_\s*=\s*\w+\.?\w*\s*$", stripped):
                if "err" in stripped.lower():
                    issues.append(
                        Issue(
                            level="warning",
                            line=i,
                            message="Error being ignored",
                            suggestion="Handle errors explicitly instead of "
                            "discarding them",
                        )
                    )

            # defer内でのエラー無視
            defer_pattern = r"\bdefer\s+\w+\.(Close|Flush|Sync)\s*\(\s*\)"
            if re.search(defer_pattern, stripped):
                issues.append(
                    Issue(
                        level="info",
                        line=i,
                        message="Deferred function call ignores error",
                        suggestion="Consider using a deferred function to "
                        "capture and log the error",
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

            # time.Sleep（本番環境での使用は要注意）
            if re.search(r"\btime\.Sleep\s*\(", stripped):
                issues.append(
                    Issue(
                        level="info",
                        line=i,
                        message="time.Sleep usage detected",
                        suggestion="Consider using context with timeout "
                        "or channels instead of time.Sleep",
                    )
                )

            # グローバル変数の検出（var宣言が関数外）
            if re.search(r"^var\s+\w+\s*=", stripped):
                issues.append(
                    Issue(
                        level="info",
                        line=i,
                        message="Global variable detected",
                        suggestion="Consider using dependency injection "
                        "instead of global variables",
                    )
                )

            # unsafeパッケージの使用
            if re.search(r'\b"unsafe"\b|unsafe\.', stripped):
                issues.append(
                    Issue(
                        level="warning",
                        line=i,
                        message="unsafe package usage detected",
                        suggestion="Ensure unsafe usage is necessary and "
                        "properly documented",
                    )
                )

            # reflect使用（パフォーマンスへの影響）
            if re.search(r'\breflect\.(TypeOf|ValueOf|DeepEqual)\b', stripped):
                issues.append(
                    Issue(
                        level="info",
                        line=i,
                        message="Reflection usage detected",
                        suggestion="Reflection can impact performance. "
                        "Consider type assertions or generics if possible",
                    )
                )

            # 空のif/else/for
            if re.search(r'\b(if|else|for)\s*\{[^}]*\}\s*$', stripped):
                if "{}" in stripped or "{ }" in stripped:
                    issues.append(
                        Issue(
                            level="style",
                            line=i,
                            message="Empty control block detected",
                            suggestion="Remove empty blocks or add "
                            "implementation/comment",
                        )
                    )

            # goto使用
            if re.search(r'\bgoto\s+\w+', stripped):
                issues.append(
                    Issue(
                        level="style",
                        line=i,
                        message="goto statement detected",
                        suggestion="Consider restructuring code to avoid "
                        "goto statements",
                    )
                )

            # 非標準のエラー変数名
            if re.search(r'err\d+\s*:?=', stripped):
                issues.append(
                    Issue(
                        level="style",
                        line=i,
                        message="Non-standard error variable name "
                        "(err1, err2, etc.)",
                        suggestion="Use descriptive error variable names "
                        "like 'parseErr', 'connectErr'",
                    )
                )

            # interface{}の使用（Go 1.18+ではanyを推奨）
            if re.search(r'\binterface\s*\{\s*\}', stripped):
                issues.append(
                    Issue(
                        level="style",
                        line=i,
                        message="interface{} detected",
                        suggestion="Consider using 'any' (Go 1.18+) or "
                        "generics instead of interface{}",
                    )
                )

            # マジックナンバー検出
            if re.search(r'[<>=!]=?\s*\d{2,}(?!\d*\.)', stripped):
                # 0, 1は許可
                match = re.search(r'\d+', stripped)
                if match and int(match.group()) > 1:
                    issues.append(
                        Issue(
                            level="style",
                            line=i,
                            message="Magic number detected",
                            suggestion="Consider extracting the number "
                            "into a named constant",
                        )
                    )

        return issues

    def _run_go_vet(self, file_path: Path) -> list[Issue]:
        """go vetを実行"""
        issues: list[Issue] = []

        try:
            cmd = ["go", "vet", str(file_path)]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                cwd=file_path.parent,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return issues

        # go vetの出力をパース
        # 形式: file.go:line:col: message
        for line in result.stderr.strip().split("\n"):
            if not line:
                continue

            match = re.match(r"([^:]+):(\d+):(?:\d+:)?\s*(.+)", line)
            if match:
                file_name = match.group(1)
                line_num = int(match.group(2))
                message = match.group(3)

                if file_path.name in file_name:
                    issues.append(
                        Issue(
                            level="warning",
                            line=line_num,
                            message=f"[go vet] {message}",
                        )
                    )

        return issues

    def _run_staticcheck(self, file_path: Path) -> list[Issue]:
        """staticcheckを実行"""
        issues: list[Issue] = []

        try:
            cmd = ["staticcheck", "-f", "json", str(file_path)]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                cwd=file_path.parent,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return issues

        # JSON Lines形式の出力をパース
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            try:
                data = json.loads(line)
                loc = data.get("location", {})
                if file_path.name not in loc.get("file", ""):
                    continue

                line_num = data.get("location", {}).get("line", 1)
                message = data.get("message", "")
                code = data.get("code", "")
                severity = data.get("severity", "")

                level = "warning"
                if severity == "error":
                    level = "bug"
                elif severity == "info":
                    level = "info"

                message_text = f"[{code}] {message}" if code else message
                issues.append(
                    Issue(
                        level=level,
                        line=line_num,
                        message=message_text,
                    )
                )
            except (json.JSONDecodeError, KeyError, TypeError):
                continue

        return issues

    def _run_golangci_lint(self, file_path: Path) -> list[Issue]:
        """golangci-lintを実行"""
        issues: list[Issue] = []

        try:
            cmd = [
                "golangci-lint",
                "run",
                "--out-format=json",
                str(file_path),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                cwd=file_path.parent,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return issues

        # JSON出力をパース
        try:
            data = json.loads(result.stdout)
            for issue in data.get("Issues", []) or []:
                pos = issue.get("Pos", {})
                if file_path.name not in pos.get("Filename", ""):
                    continue

                line_num = pos.get("Line", 1)
                message = issue.get("Text", "")
                linter = issue.get("FromLinter", "")
                severity = issue.get("Severity", "")

                level = "warning"
                if severity == "error":
                    level = "bug"

                message_text = f"[{linter}] {message}" if linter else message
                issues.append(
                    Issue(
                        level=level,
                        line=line_num,
                        message=message_text,
                    )
                )
        except (json.JSONDecodeError, TypeError):
            pass

        return issues

    def check_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        """簡易構文チェック

        Returns:
            tuple[bool, Optional[str]]: (有効か, エラーメッセージ)
        """
        # 基本的な括弧の対応をチェック
        brackets = {"(": ")", "[": "]", "{": "}"}
        stack = []
        in_string = False
        in_rune = False
        in_raw_string = False
        in_comment = False
        in_block_comment = False
        escape_next = False
        i = 0

        while i < len(code):
            char = code[i]

            # エスケープ処理
            if escape_next:
                escape_next = False
                i += 1
                continue

            # ブロックコメント終了チェック
            if in_block_comment:
                if char == "*" and i + 1 < len(code) and code[i + 1] == "/":
                    in_block_comment = False
                    i += 2
                    continue
                i += 1
                continue

            # 行コメント終了チェック
            if in_comment:
                if char == "\n":
                    in_comment = False
                i += 1
                continue

            # コメント開始チェック
            if char == "/" and i + 1 < len(code):
                if code[i + 1] == "/":
                    in_comment = True
                    i += 2
                    continue
                elif code[i + 1] == "*":
                    in_block_comment = True
                    i += 2
                    continue

            # raw文字列開始
            if char == "`":
                in_raw_string = not in_raw_string
                i += 1
                continue

            if in_raw_string:
                i += 1
                continue

            # 文字列処理
            if char == '"' and not in_rune:
                in_string = not in_string
                i += 1
                continue

            # runeリテラル処理
            if char == "'" and not in_string:
                in_rune = not in_rune
                i += 1
                continue

            if in_string or in_rune:
                if char == "\\":
                    escape_next = True
                i += 1
                continue

            # 括弧チェック
            if char in brackets:
                stack.append((char, i))
            elif char in brackets.values():
                if not stack:
                    return False, f"Unexpected closing bracket '{char}'"
                open_bracket, _ = stack.pop()
                if brackets[open_bracket] != char:
                    msg = f"Mismatched brackets: '{open_bracket}' and '{char}'"
                    return False, msg

            i += 1

        if stack:
            open_bracket, _ = stack[-1]
            return False, f"Unclosed bracket '{open_bracket}'"

        return True, None

    def get_functions(self, code: str) -> list[str]:
        """コード内の関数名を取得"""
        functions = []

        # func キーワードによる関数定義
        for match in re.finditer(
            r"\bfunc\s+(?:\([^)]+\)\s*)?(\w+)\s*\(", code
        ):
            functions.append(match.group(1))

        return list(set(functions))

    def get_types(self, code: str) -> list[str]:
        """コード内の型名を取得（struct, interface）"""
        types = []

        type_pattern = r"\btype\s+(\w+)\s+(struct|interface)\b"
        for match in re.finditer(type_pattern, code):
            types.append(match.group(1))

        return types

    def get_structs(self, code: str) -> list[str]:
        """コード内の構造体名を取得"""
        structs = []

        for match in re.finditer(r"\btype\s+(\w+)\s+struct\b", code):
            structs.append(match.group(1))

        return structs

    def get_interfaces(self, code: str) -> list[str]:
        """コード内のインターフェース名を取得"""
        interfaces = []

        for match in re.finditer(r"\btype\s+(\w+)\s+interface\b", code):
            interfaces.append(match.group(1))

        return interfaces

    def get_imports(self, code: str) -> list[str]:
        """importを取得"""
        imports = []

        # 単一import
        for match in re.finditer(r'\bimport\s+"([^"]+)"', code):
            imports.append(match.group(1))

        # グループimport
        import_block = re.search(r'\bimport\s*\((.*?)\)', code, re.DOTALL)
        if import_block:
            for match in re.finditer(r'"([^"]+)"', import_block.group(1)):
                imports.append(match.group(1))

        return imports

    def get_packages(self, code: str) -> list[str]:
        """パッケージ名を取得"""
        packages = []

        for match in re.finditer(r'\bpackage\s+(\w+)', code):
            packages.append(match.group(1))

        return packages

    def get_consts(self, code: str) -> list[str]:
        """定数名を取得"""
        consts = []

        # 単一const
        for match in re.finditer(r'\bconst\s+(\w+)\s*=', code):
            consts.append(match.group(1))

        # グループconst
        const_block = re.search(r'\bconst\s*\((.*?)\)', code, re.DOTALL)
        if const_block:
            for match in re.finditer(r'(\w+)\s*=', const_block.group(1)):
                consts.append(match.group(1))

        return consts

    def get_methods(self, code: str) -> list[dict[str, str]]:
        """メソッド情報を取得（レシーバ付き関数）"""
        methods = []

        for match in re.finditer(
            r'\bfunc\s+\(\s*\w+\s+\*?(\w+)\s*\)\s+(\w+)\s*\(', code
        ):
            methods.append({
                "receiver": match.group(1),
                "method": match.group(2),
            })

        return methods
