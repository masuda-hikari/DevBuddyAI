"""
CodeTestGenerator - AIテスト生成エンジン

関数/クラスからユニットテストを自動生成。
自己検証ループにより、生成テストの品質を保証。
"""

import ast
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from devbuddy.llm.client import LLMClient
from devbuddy.llm.prompts import PromptTemplates
from devbuddy.core.licensing import LicenseManager, UsageLimitError


@dataclass
class FunctionInfo:
    """関数情報"""

    name: str
    args: list[str]
    return_type: Optional[str]
    docstring: Optional[str]
    source: str
    line_start: int
    line_end: int


@dataclass
class TestVerificationReport:
    """テスト検証レポート"""

    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    coverage_percent: Optional[float] = None
    failed_tests: list[str] = field(default_factory=list)
    error_messages: list[str] = field(default_factory=list)


@dataclass
class GenerationResult:
    """テスト生成結果"""

    success: bool
    test_code: str = ""
    error: Optional[str] = None
    test_count: int = 0
    verified: bool = False
    attempts: int = 1
    verification_report: Optional[TestVerificationReport] = None


class CodeTestGenerator:
    """AIテスト生成エンジン"""

    __test__ = False  # pytestがテストクラスと誤認識しないようにする

    def __init__(
        self,
        client: LLMClient,
        license_manager: Optional[LicenseManager] = None,
        skip_license_check: bool = False,
    ):
        self.client = client
        self.prompts = PromptTemplates()
        self.max_retry = 3
        self._license_manager = license_manager
        self._skip_license_check = skip_license_check

    @property
    def license_manager(self) -> LicenseManager:
        """ライセンスマネージャーを取得（遅延初期化）"""
        if self._license_manager is None:
            self._license_manager = LicenseManager()
        return self._license_manager

    def generate_tests(
        self,
        source_path: Path,
        function_name: Optional[str] = None,
        framework: str = "pytest",
    ) -> GenerationResult:
        """テストを生成

        Args:
            source_path: ソースファイルパス
            function_name: 対象関数名（Noneなら全関数）
            framework: テストフレームワーク (pytest/unittest)

        Returns:
            GenerationResult: 生成結果
        """
        # ライセンスチェック
        if not self._skip_license_check:
            try:
                self.license_manager.check_testgen_limit()
            except UsageLimitError as e:
                return GenerationResult(
                    success=False, error=str(e)
                )

        try:
            with open(source_path, encoding="utf-8") as f:
                source_code = f.read()
        except Exception as e:
            return GenerationResult(
                success=False, error=f"Failed to read file: {e}"
            )

        # 関数情報を抽出
        functions = self._extract_functions(source_code)

        if function_name:
            functions = [f for f in functions if f.name == function_name]
            if not functions:
                return GenerationResult(
                    success=False,
                    error=f"Function '{function_name}' not found",
                )

        # テスト生成
        module_name = source_path.stem
        prompt = self.prompts.test_generation(
            functions=functions,
            module_name=module_name,
            framework=framework,
        )

        try:
            test_code = self.client.complete(prompt)
            test_code = self._clean_test_code(test_code)
        except Exception as e:
            return GenerationResult(success=False, error=str(e))

        # テスト数をカウント
        test_count = test_code.count("def test_")

        # 利用量を記録
        if not self._skip_license_check:
            self.license_manager.record_testgen()

        return GenerationResult(
            success=True,
            test_code=test_code,
            test_count=test_count,
        )

    def generate_and_verify(
        self,
        source_path: Path,
        function_name: Optional[str] = None,
        framework: str = "pytest",
        measure_coverage: bool = False,
    ) -> GenerationResult:
        """テストを生成し、実行して検証

        失敗した場合は修正を試行（自己検証ループ）

        Args:
            source_path: ソースファイルパス
            function_name: 対象関数名（Noneなら全関数）
            framework: テストフレームワーク (pytest/unittest)
            measure_coverage: カバレッジを測定するか

        Returns:
            GenerationResult: 生成・検証結果
        """
        result = GenerationResult(success=False)

        for attempt in range(self.max_retry):
            result = self.generate_tests(source_path, function_name, framework)
            result.attempts = attempt + 1

            if not result.success:
                return result

            # テストを一時ファイルに書き出して実行
            temp_name = f"_temp_test_{source_path.stem}.py"
            test_path = source_path.parent / temp_name
            try:
                with open(test_path, "w", encoding="utf-8") as f:
                    f.write(result.test_code)

                # テスト実行コマンドを構築
                cmd = ["pytest", str(test_path), "-v", "--tb=short"]
                if measure_coverage:
                    cmd.extend([
                        f"--cov={source_path.parent}",
                        "--cov-report=term-missing"
                    ])

                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                # 検証レポートを解析
                report = self._parse_test_output(proc.stdout + proc.stderr)
                result.verification_report = report

                if proc.returncode == 0:
                    result.verified = True
                    return result

                # 失敗した場合、AIに修正を依頼
                if attempt < self.max_retry - 1:
                    # より詳細なエラー情報を提供
                    error_context = self._build_error_context(
                        test_code=result.test_code,
                        output=proc.stdout + proc.stderr,
                        report=report,
                        attempt=attempt + 1,
                    )
                    fix_prompt = self.prompts.fix_failing_tests(
                        test_code=result.test_code,
                        error_output=error_context,
                    )
                    result.test_code = self.client.complete(fix_prompt)
                    result.test_code = self._clean_test_code(result.test_code)

            except subprocess.TimeoutExpired:
                return GenerationResult(
                    success=False,
                    error="Test execution timed out",
                    attempts=attempt + 1,
                )
            except Exception as e:
                return GenerationResult(
                    success=False,
                    error=str(e),
                    attempts=attempt + 1,
                )
            finally:
                if test_path.exists():
                    test_path.unlink()

        return result

    def _parse_test_output(self, output: str) -> TestVerificationReport:
        """pytestの出力を解析してレポートを生成"""
        report = TestVerificationReport()

        # テスト結果のサマリーを解析
        # 例: "5 passed, 2 failed, 1 error in 0.53s"
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

        # カバレッジの解析
        # 例: "TOTAL                   100     20    80%"
        coverage_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
        if coverage_match:
            report.coverage_percent = float(coverage_match.group(1))

        # 失敗したテスト名を抽出
        # 例: "FAILED test_example.py::test_func - AssertionError"
        failed_matches = re.findall(
            r"FAILED\s+[\w.]+::(\w+)", output
        )
        report.failed_tests = failed_matches

        # エラーメッセージを抽出
        error_blocks = re.findall(
            r"(E\s+.+?)(?=\n[^\s]|\Z)",
            output,
            re.MULTILINE
        )
        report.error_messages = [e.strip() for e in error_blocks[:5]]

        return report

    def _build_error_context(
        self,
        test_code: str,
        output: str,
        report: TestVerificationReport,
        attempt: int,
    ) -> str:
        """AIへの修正依頼用のエラーコンテキストを構築"""
        context_parts = [
            f"=== 自己検証ループ: 試行 {attempt}/{self.max_retry} ===",
            "",
            f"失敗テスト数: {report.failed}",
            f"エラー数: {report.errors}",
            "",
        ]

        if report.failed_tests:
            context_parts.append("失敗したテスト:")
            for test_name in report.failed_tests:
                context_parts.append(f"  - {test_name}")
            context_parts.append("")

        if report.error_messages:
            context_parts.append("エラーメッセージ:")
            for msg in report.error_messages:
                context_parts.append(f"  {msg}")
            context_parts.append("")

        context_parts.append("=== 完全な出力 ===")
        context_parts.append(output)

        return "\n".join(context_parts)

    def _extract_functions(self, source_code: str) -> list[FunctionInfo]:
        """ソースコードから関数情報を抽出"""
        functions: list[FunctionInfo] = []

        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return functions

        lines = source_code.split("\n")

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 引数情報
                args = []
                for arg in node.args.args:
                    arg_str = arg.arg
                    if arg.annotation:
                        arg_str += f": {ast.unparse(arg.annotation)}"
                    args.append(arg_str)

                # 戻り値型
                return_type = None
                if node.returns:
                    return_type = ast.unparse(node.returns)

                # docstring
                docstring = ast.get_docstring(node)

                # ソースコード
                start_line = node.lineno - 1
                end_line = node.end_lineno
                source = "\n".join(lines[start_line:end_line])

                functions.append(
                    FunctionInfo(
                        name=node.name,
                        args=args,
                        return_type=return_type,
                        docstring=docstring,
                        source=source,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                    )
                )

        return functions

    def _clean_test_code(self, code: str) -> str:
        """生成されたテストコードをクリーンアップ"""
        # マークダウンのコードブロックを除去
        if "```python" in code:
            start = code.index("```python") + len("```python")
            end = code.rindex("```")
            code = code[start:end]
        elif "```" in code:
            start = code.index("```") + 3
            end = code.rindex("```")
            code = code[start:end]

        return code.strip()
