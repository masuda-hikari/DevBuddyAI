"""
TestGenerator - AIテスト生成エンジン

関数/クラスからユニットテストを自動生成。
"""

import ast
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from devbuddy.llm.client import LLMClient
from devbuddy.llm.prompts import PromptTemplates


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
class GenerationResult:
    """テスト生成結果"""

    success: bool
    test_code: str = ""
    error: Optional[str] = None
    test_count: int = 0
    verified: bool = False


class TestGenerator:
    """AIテスト生成エンジン"""

    def __init__(self, client: LLMClient):
        self.client = client
        self.prompts = PromptTemplates()
        self.max_retry = 3

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
        try:
            with open(source_path, encoding="utf-8") as f:
                source_code = f.read()
        except Exception as e:
            return GenerationResult(success=False, error=f"Failed to read file: {e}")

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
    ) -> GenerationResult:
        """テストを生成し、実行して検証

        失敗した場合は修正を試行（自己検証ループ）
        """
        for attempt in range(self.max_retry):
            result = self.generate_tests(source_path, function_name, framework)

            if not result.success:
                return result

            # テストを一時ファイルに書き出して実行
            test_path = source_path.parent / f"_temp_test_{source_path.stem}.py"
            try:
                with open(test_path, "w", encoding="utf-8") as f:
                    f.write(result.test_code)

                # テスト実行
                proc = subprocess.run(
                    ["pytest", str(test_path), "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if proc.returncode == 0:
                    result.verified = True
                    return result

                # 失敗した場合、AIに修正を依頼
                if attempt < self.max_retry - 1:
                    fix_prompt = self.prompts.fix_failing_tests(
                        test_code=result.test_code,
                        error_output=proc.stdout + proc.stderr,
                    )
                    result.test_code = self.client.complete(fix_prompt)
                    result.test_code = self._clean_test_code(result.test_code)

            except subprocess.TimeoutExpired:
                return GenerationResult(
                    success=False,
                    error="Test execution timed out",
                )
            except Exception as e:
                return GenerationResult(success=False, error=str(e))
            finally:
                if test_path.exists():
                    test_path.unlink()

        return result

    def _extract_functions(self, source_code: str) -> list[FunctionInfo]:
        """ソースコードから関数情報を抽出"""
        functions = []

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
                source = "\n".join(lines[node.lineno - 1 : node.end_lineno])

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
