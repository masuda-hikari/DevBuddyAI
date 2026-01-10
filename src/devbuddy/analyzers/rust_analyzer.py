"""
RustAnalyzer - Rust静的解析

clippy、cargo check等の静的解析ツールと統合。
"""

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from devbuddy.core.reviewer import Issue


@dataclass
class RustAnalysisConfig:
    """Rust解析設定"""

    use_clippy: bool = True
    use_cargo_check: bool = False
    warn_as_error: bool = False
    deny_warnings: bool = False
    edition: str = "2021"


class RustAnalyzer:
    """Rust静的解析エンジン"""

    def __init__(self, config: Optional[RustAnalysisConfig] = None):
        self.config = config or RustAnalysisConfig()

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
            # Cargoプロジェクト内かどうかを確認
            cargo_root = self._find_cargo_root(file_path)
            if cargo_root:
                if self.config.use_clippy:
                    issues.extend(self._run_clippy(cargo_root, file_path))
                if self.config.use_cargo_check:
                    issues.extend(self._run_cargo_check(cargo_root, file_path))

        return issues

    def _find_cargo_root(self, file_path: Path) -> Optional[Path]:
        """Cargo.tomlを探してプロジェクトルートを返す"""
        current = file_path.parent
        for _ in range(10):  # 最大10階層まで探索
            if (current / "Cargo.toml").exists():
                return current
            if current.parent == current:
                break
            current = current.parent
        return None

    def _analyze_patterns(self, code: str) -> list[Issue]:
        """パターンベース解析"""
        issues = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # unwrap()の使用検出
            if re.search(r"\.unwrap\(\)", stripped):
                # expect()への変換を推奨
                issues.append(
                    Issue(
                        level="warning",
                        line=i,
                        message="unwrap() usage detected",
                        suggestion="Consider using expect() with a message, "
                        "or handle the error with match/if let",
                    )
                )

            # expect()の空メッセージ検出
            if re.search(r'\.expect\(\s*""\s*\)', stripped):
                issues.append(
                    Issue(
                        level="style",
                        line=i,
                        message="expect() with empty message",
                        suggestion="Provide a meaningful error message",
                    )
                )

            # panic!マクロの使用
            if re.search(r"\bpanic!\s*\(", stripped):
                issues.append(
                    Issue(
                        level="warning",
                        line=i,
                        message="panic! macro usage",
                        suggestion="Consider returning Result or Option "
                        "instead of panicking",
                    )
                )

            # println!/dbg!の使用（デバッグ用）
            if re.search(r"\b(println!|dbg!)\s*\(", stripped):
                issues.append(
                    Issue(
                        level="info",
                        line=i,
                        message="Debug output detected",
                        suggestion="Remove debug output before production",
                    )
                )

            # unsafe使用検出
            if re.search(r"\bunsafe\b", stripped):
                issues.append(
                    Issue(
                        level="warning",
                        line=i,
                        message="unsafe code block detected",
                        suggestion="Ensure unsafe code is necessary and "
                        "properly documented",
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

            # clone()の過剰使用の可能性
            clone_count = len(re.findall(r"\.clone\(\)", stripped))
            if clone_count >= 2:
                issues.append(
                    Issue(
                        level="style",
                        line=i,
                        message="Multiple clone() calls on same line",
                        suggestion="Consider using references to avoid "
                        "unnecessary cloning",
                    )
                )

            # 非推奨: mem::transmute
            if re.search(r"\b(mem::)?transmute\b", stripped):
                issues.append(
                    Issue(
                        level="bug",
                        line=i,
                        message="transmute usage detected",
                        suggestion="transmute is extremely unsafe. "
                        "Consider safer alternatives",
                    )
                )

            # as によるキャスト（潜在的な問題）
            if re.search(r"\bas\s+(u|i)(8|16|32|64|128|size)\b", stripped):
                # 数値リテラルへのキャストは許可
                if not re.search(r"\d+\s+as\s+", stripped):
                    issues.append(
                        Issue(
                            level="info",
                            line=i,
                            message="Numeric cast with 'as' detected",
                            suggestion="Consider using try_into() for "
                            "checked conversion",
                        )
                    )

            # 空のimpl検出
            if re.search(r"impl\s+\w+.*\{\s*\}", stripped):
                issues.append(
                    Issue(
                        level="style",
                        line=i,
                        message="Empty impl block detected",
                        suggestion="Remove empty impl blocks or "
                        "add implementation",
                    )
                )

            # allow属性の乱用
            if re.search(r"#\[allow\(", stripped):
                issues.append(
                    Issue(
                        level="info",
                        line=i,
                        message="Lint suppression with #[allow(...)]",
                        suggestion="Ensure lint suppression is justified",
                    )
                )

            # dead_code許可
            if re.search(r"#\[allow\(dead_code\)\]", stripped):
                issues.append(
                    Issue(
                        level="style",
                        line=i,
                        message="dead_code suppression detected",
                        suggestion="Remove unused code or "
                        "add #[cfg(test)] for test utilities",
                    )
                )

        return issues

    def _run_clippy(
        self,
        cargo_root: Path,
        file_path: Path,
    ) -> list[Issue]:
        """cargo clippyを実行"""
        issues: list[Issue] = []

        try:
            cmd = [
                "cargo",
                "clippy",
                "--message-format=json",
                "--quiet",
            ]

            if self.config.deny_warnings:
                cmd.append("--")
                cmd.append("-D")
                cmd.append("warnings")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=cargo_root,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return issues

        # JSON Lines形式の出力をパース
        file_name = file_path.name
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            try:
                data = json.loads(line)
                if data.get("reason") != "compiler-message":
                    continue

                message = data.get("message", {})
                if not message:
                    continue

                level = message.get("level", "")
                text = message.get("message", "")
                code_info = message.get("code")
                code = code_info.get("code", "") if code_info else ""

                # スパン情報からファイルと行番号を取得
                spans = message.get("spans", [])
                primary_span = None
                for span in spans:
                    if span.get("is_primary"):
                        primary_span = span
                        break

                if not primary_span:
                    continue

                span_file = primary_span.get("file_name", "")
                # ファイル名が一致する場合のみ追加
                if file_name not in span_file:
                    continue

                line_num = primary_span.get("line_start", 1)
                issue_level = self._clippy_level_to_level(level)

                message_text = f"[{code}] {text}" if code else text
                issues.append(
                    Issue(
                        level=issue_level,
                        line=line_num,
                        message=message_text,
                    )
                )
            except (json.JSONDecodeError, KeyError, TypeError):
                continue

        return issues

    def _run_cargo_check(
        self,
        cargo_root: Path,
        file_path: Path,
    ) -> list[Issue]:
        """cargo checkを実行"""
        issues: list[Issue] = []

        try:
            cmd = [
                "cargo",
                "check",
                "--message-format=json",
                "--quiet",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=cargo_root,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return issues

        # JSON Lines形式の出力をパース
        file_name = file_path.name
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            try:
                data = json.loads(line)
                if data.get("reason") != "compiler-message":
                    continue

                message = data.get("message", {})
                if not message:
                    continue

                level = message.get("level", "")
                text = message.get("message", "")

                spans = message.get("spans", [])
                primary_span = None
                for span in spans:
                    if span.get("is_primary"):
                        primary_span = span
                        break

                if not primary_span:
                    continue

                span_file = primary_span.get("file_name", "")
                if file_name not in span_file:
                    continue

                line_num = primary_span.get("line_start", 1)
                issue_level = self._clippy_level_to_level(level)

                issues.append(
                    Issue(
                        level=issue_level,
                        line=line_num,
                        message=text,
                    )
                )
            except (json.JSONDecodeError, KeyError, TypeError):
                continue

        return issues

    def _clippy_level_to_level(self, level: str) -> str:
        """clippy/cargoのレベルを変換"""
        if level == "error":
            return "bug"
        elif level == "warning":
            return "warning"
        elif level == "note":
            return "info"
        elif level == "help":
            return "info"
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
        in_char = False
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
            if char == "r" and i + 1 < len(code) and code[i + 1] == '"':
                in_raw_string = True
                i += 2
                continue

            # raw文字列終了
            if in_raw_string and char == '"':
                in_raw_string = False
                i += 1
                continue

            if in_raw_string:
                i += 1
                continue

            # 文字列処理
            if char == '"' and not in_char:
                if in_string:
                    in_string = False
                else:
                    in_string = True
                i += 1
                continue

            # 文字リテラル処理
            if char == "'" and not in_string:
                # ライフタイム記法との区別
                if i + 1 < len(code) and code[i + 1].isalpha():
                    # ライフタイム（'a, 'static等）
                    i += 1
                    while i < len(code) and (
                        code[i].isalnum() or code[i] == "_"
                    ):
                        i += 1
                    continue
                else:
                    in_char = not in_char
                    i += 1
                    continue

            if in_string or in_char:
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

        # fn キーワードによる関数定義
        for match in re.finditer(
            r"\bfn\s+(\w+)\s*(?:<[^>]*>)?\s*\(", code
        ):
            functions.append(match.group(1))

        return list(set(functions))

    def get_structs(self, code: str) -> list[str]:
        """コード内の構造体名を取得"""
        structs = []

        for match in re.finditer(r"\bstruct\s+(\w+)", code):
            structs.append(match.group(1))

        return structs

    def get_enums(self, code: str) -> list[str]:
        """コード内の列挙型名を取得"""
        enums = []

        for match in re.finditer(r"\benum\s+(\w+)", code):
            enums.append(match.group(1))

        return enums

    def get_traits(self, code: str) -> list[str]:
        """コード内のトレイト名を取得"""
        traits = []

        for match in re.finditer(r"\btrait\s+(\w+)", code):
            traits.append(match.group(1))

        return traits

    def get_impls(self, code: str) -> list[dict[str, str]]:
        """impl情報を取得"""
        impls = []

        # impl Trait for Type
        for match in re.finditer(
            r"\bimpl\s+(\w+)\s+for\s+(\w+)", code
        ):
            impls.append({
                "trait": match.group(1),
                "type": match.group(2),
            })

        # impl Type
        for match in re.finditer(
            r"\bimpl(?:\s*<[^>]*>)?\s+(\w+)\s*(?:<[^>]*>)?\s*\{",
            code,
        ):
            type_name = match.group(1)
            # impl Trait for Typeのパターンと重複しないようチェック
            if not re.search(
                rf"\bimpl\s+\w+\s+for\s+{type_name}\b",
                code[max(0, match.start() - 50):match.start()],
            ):
                impls.append({
                    "trait": None,
                    "type": type_name,
                })

        return impls

    def get_uses(self, code: str) -> list[str]:
        """use文のインポートパスを取得"""
        uses = []

        for match in re.finditer(r"\buse\s+([^;]+);", code):
            path = match.group(1).strip()
            uses.append(path)

        return uses

    def get_mods(self, code: str) -> list[str]:
        """モジュール宣言を取得"""
        mods = []

        for match in re.finditer(r"\bmod\s+(\w+)", code):
            mods.append(match.group(1))

        return mods
