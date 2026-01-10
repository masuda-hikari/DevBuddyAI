"""JavaScriptAnalyzerのテスト"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from devbuddy.analyzers.js_analyzer import JavaScriptAnalyzer, JSAnalysisConfig


class TestJavaScriptAnalyzer:
    """JavaScriptAnalyzerクラスのテスト"""

    def test_init_default_config(self):
        """デフォルト設定での初期化"""
        analyzer = JavaScriptAnalyzer()
        assert analyzer.config.use_eslint is True
        assert analyzer.config.use_tsc is False

    def test_init_custom_config(self):
        """カスタム設定での初期化"""
        config = JSAnalysisConfig(use_eslint=False, use_tsc=True, strict_mode=True)
        analyzer = JavaScriptAnalyzer(config)
        assert analyzer.config.use_eslint is False
        assert analyzer.config.use_tsc is True
        assert analyzer.config.strict_mode is True

    def test_is_typescript_ts_file(self):
        """TypeScriptファイル判定 - .ts"""
        analyzer = JavaScriptAnalyzer()
        assert analyzer._is_typescript(Path("file.ts")) is True

    def test_is_typescript_tsx_file(self):
        """TypeScriptファイル判定 - .tsx"""
        analyzer = JavaScriptAnalyzer()
        assert analyzer._is_typescript(Path("file.tsx")) is True

    def test_is_typescript_js_file(self):
        """TypeScriptファイル判定 - .js"""
        analyzer = JavaScriptAnalyzer()
        assert analyzer._is_typescript(Path("file.js")) is False


class TestPatternAnalysis:
    """パターンベース解析のテスト"""

    def test_detect_console_log(self):
        """console.logの検出"""
        analyzer = JavaScriptAnalyzer()
        code = "console.log('test');"
        issues = analyzer._analyze_patterns(code)
        assert len(issues) == 1
        assert issues[0].level == "info"
        assert "console.log" in issues[0].message

    def test_detect_console_debug(self):
        """console.debugの検出"""
        analyzer = JavaScriptAnalyzer()
        code = "console.debug('debug info');"
        issues = analyzer._analyze_patterns(code)
        assert len(issues) == 1
        assert "console.log" in issues[0].message

    def test_detect_debugger(self):
        """debugger文の検出"""
        analyzer = JavaScriptAnalyzer()
        code = "function test() {\n  debugger;\n}"
        issues = analyzer._analyze_patterns(code)
        assert any(i.level == "warning" and "debugger" in i.message for i in issues)

    def test_detect_eval(self):
        """eval()の検出"""
        analyzer = JavaScriptAnalyzer()
        code = "const result = eval(userInput);"
        issues = analyzer._analyze_patterns(code)
        assert any(i.level == "bug" and "eval" in i.message for i in issues)

    def test_detect_non_strict_equality(self):
        """非厳密等価演算子の検出"""
        analyzer = JavaScriptAnalyzer()
        code = "if (x == 5) {}"
        issues = analyzer._analyze_patterns(code)
        assert any(i.level == "style" and "==" in i.message for i in issues)

    def test_allow_null_comparison(self):
        """null比較での==は許可"""
        analyzer = JavaScriptAnalyzer()
        code = "if (x == null) {}"
        issues = analyzer._analyze_patterns(code)
        # null比較は警告しない
        assert not any("Non-strict equality" in i.message for i in issues)

    def test_detect_var_keyword(self):
        """var キーワードの検出"""
        analyzer = JavaScriptAnalyzer()
        code = "var x = 5;"
        issues = analyzer._analyze_patterns(code)
        assert any(i.level == "style" and "var" in i.message for i in issues)

    def test_detect_empty_catch(self):
        """空のcatchブロックの検出"""
        analyzer = JavaScriptAnalyzer()
        code = "try { foo(); } catch (e) {}"
        issues = analyzer._analyze_patterns(code)
        has_catch_warn = any(
            i.level == "warning" and "catch" in i.message.lower()
            for i in issues
        )
        assert has_catch_warn

    def test_detect_todo_comment(self):
        """TODO/FIXMEコメントの検出"""
        analyzer = JavaScriptAnalyzer()
        code = "// TODO: implement this"
        issues = analyzer._analyze_patterns(code)
        assert any(i.level == "info" and "TODO" in i.message for i in issues)

    def test_detect_innerhtml(self):
        """innerHTML代入の検出"""
        analyzer = JavaScriptAnalyzer()
        code = "element.innerHTML = userInput;"
        issues = analyzer._analyze_patterns(code)
        assert any(i.level == "warning" and "innerHTML" in i.message for i in issues)

    def test_detect_sql_injection(self):
        """SQLインジェクションの検出"""
        analyzer = JavaScriptAnalyzer()
        code = "db.query(`SELECT * FROM users WHERE id = ${userId}`);"
        issues = analyzer._analyze_patterns(code)
        assert any(i.level == "bug" and "SQL injection" in i.message for i in issues)

    def test_detect_any_type(self):
        """TypeScript any型の検出"""
        analyzer = JavaScriptAnalyzer()
        code = "function test(data: any): void {}"
        issues = analyzer._analyze_patterns(code)
        assert any(i.level == "style" and "any" in i.message for i in issues)

    def test_line_numbers_correct(self):
        """行番号が正しいか"""
        analyzer = JavaScriptAnalyzer()
        code = "const x = 1;\nconsole.log(x);\nconst y = 2;"
        issues = analyzer._analyze_patterns(code)
        console_issue = next((i for i in issues if "console.log" in i.message), None)
        assert console_issue is not None
        assert console_issue.line == 2


class TestSyntaxCheck:
    """構文チェックのテスト"""

    def test_valid_syntax(self):
        """正常な構文"""
        analyzer = JavaScriptAnalyzer()
        code = "function test() { return 42; }"
        valid, error = analyzer.check_syntax(code)
        assert valid is True
        assert error is None

    def test_unclosed_bracket(self):
        """閉じられていない括弧"""
        analyzer = JavaScriptAnalyzer()
        code = "function test() { return 42;"
        valid, error = analyzer.check_syntax(code)
        assert valid is False
        assert "Unclosed" in error

    def test_mismatched_brackets(self):
        """括弧の不一致"""
        analyzer = JavaScriptAnalyzer()
        code = "function test() { return [1, 2}; }"
        valid, error = analyzer.check_syntax(code)
        assert valid is False
        assert "Mismatched" in error

    def test_brackets_in_string(self):
        """文字列内の括弧は無視"""
        analyzer = JavaScriptAnalyzer()
        code = 'const s = "{ [";'
        valid, error = analyzer.check_syntax(code)
        assert valid is True


class TestGetFunctions:
    """関数名取得のテスト"""

    def test_get_function_declaration(self):
        """function宣言"""
        analyzer = JavaScriptAnalyzer()
        code = "function calculateSum(a, b) { return a + b; }"
        functions = analyzer.get_functions(code)
        assert "calculateSum" in functions

    def test_get_arrow_function(self):
        """アロー関数"""
        analyzer = JavaScriptAnalyzer()
        code = "const multiply = (a, b) => a * b;"
        functions = analyzer.get_functions(code)
        assert "multiply" in functions

    def test_get_multiple_functions(self):
        """複数の関数"""
        analyzer = JavaScriptAnalyzer()
        code = """
function foo() {}
const bar = () => {};
let baz = function() {};
"""
        functions = analyzer.get_functions(code)
        assert "foo" in functions
        assert "bar" in functions


class TestGetClasses:
    """クラス名取得のテスト"""

    def test_get_class(self):
        """クラス宣言"""
        analyzer = JavaScriptAnalyzer()
        code = "class MyClass {}"
        classes = analyzer.get_classes(code)
        assert "MyClass" in classes

    def test_get_class_extends(self):
        """継承クラス"""
        analyzer = JavaScriptAnalyzer()
        code = "class Child extends Parent {}"
        classes = analyzer.get_classes(code)
        assert "Child" in classes

    def test_get_multiple_classes(self):
        """複数のクラス"""
        analyzer = JavaScriptAnalyzer()
        code = """
class First {}
class Second {}
"""
        classes = analyzer.get_classes(code)
        assert "First" in classes
        assert "Second" in classes


class TestGetExports:
    """エクスポート取得のテスト"""

    def test_get_export_default(self):
        """export default"""
        analyzer = JavaScriptAnalyzer()
        code = "export default function myFunc() {}"
        exports = analyzer.get_exports(code)
        assert "myFunc" in exports

    def test_get_export_const(self):
        """export const"""
        analyzer = JavaScriptAnalyzer()
        code = "export const API_KEY = 'xxx';"
        exports = analyzer.get_exports(code)
        assert "API_KEY" in exports

    def test_get_export_braces(self):
        """export { ... }"""
        analyzer = JavaScriptAnalyzer()
        code = "export { foo, bar };"
        exports = analyzer.get_exports(code)
        assert "foo" in exports
        assert "bar" in exports


class TestGetImports:
    """インポート取得のテスト"""

    def test_get_named_import(self):
        """named import"""
        analyzer = JavaScriptAnalyzer()
        code = "import { useState } from 'react';"
        imports = analyzer.get_imports(code)
        assert any(i["name"] == "useState" and i["source"] == "react" for i in imports)

    def test_get_default_import(self):
        """default import"""
        analyzer = JavaScriptAnalyzer()
        code = "import React from 'react';"
        imports = analyzer.get_imports(code)
        assert any(i["name"] == "React" and i["source"] == "react" for i in imports)

    def test_get_namespace_import(self):
        """namespace import"""
        analyzer = JavaScriptAnalyzer()
        code = "import * as utils from './utils';"
        imports = analyzer.get_imports(code)
        assert any(i["name"] == "utils" and i["source"] == "./utils" for i in imports)


class TestESLintIntegration:
    """ESLint統合のテスト"""

    def test_eslint_not_found(self):
        """ESLintが見つからない場合"""
        analyzer = JavaScriptAnalyzer()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("const x = 1;")
            f.flush()
            file_path = Path(f.name)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            issues = analyzer._run_eslint(file_path)
            assert issues == []

        file_path.unlink()

    def test_eslint_timeout(self):
        """ESLintタイムアウト"""
        analyzer = JavaScriptAnalyzer()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("const x = 1;")
            f.flush()
            file_path = Path(f.name)

        import subprocess

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 60)
            issues = analyzer._run_eslint(file_path)
            assert issues == []

        file_path.unlink()

    def test_eslint_json_parse(self):
        """ESLint JSON出力のパース"""
        analyzer = JavaScriptAnalyzer()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("const x = 1;")
            f.flush()
            file_path = Path(f.name)

        mock_result = MagicMock()
        eslint_output = (
            '[{"messages": [{"severity": 2, "line": 1, '
            '"ruleId": "no-unused-vars", "message": "x is not used"}]}]'
        )
        mock_result.stdout = eslint_output

        with patch("subprocess.run", return_value=mock_result):
            issues = analyzer._run_eslint(file_path)
            assert len(issues) == 1
            assert issues[0].level == "bug"
            assert "no-unused-vars" in issues[0].message

        file_path.unlink()

    def test_eslint_severity_to_level(self):
        """ESLint severity変換"""
        analyzer = JavaScriptAnalyzer()
        assert analyzer._eslint_severity_to_level(2) == "bug"
        assert analyzer._eslint_severity_to_level(1) == "warning"
        assert analyzer._eslint_severity_to_level(0) == "info"


class TestTSCIntegration:
    """TypeScriptコンパイラ統合のテスト"""

    def test_tsc_not_found(self):
        """tscが見つからない場合"""
        analyzer = JavaScriptAnalyzer()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
            f.write("const x: number = 1;")
            f.flush()
            file_path = Path(f.name)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            issues = analyzer._run_tsc(file_path)
            assert issues == []

        file_path.unlink()

    def test_tsc_output_parse(self):
        """tsc出力のパース"""
        analyzer = JavaScriptAnalyzer()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
            f.write("const x: number = 'string';")
            f.flush()
            file_path = Path(f.name)

        mock_result = MagicMock()
        tsc_error = (
            f"{file_path}(1,7): error TS2322: "
            "Type 'string' is not assignable to type 'number'."
        )
        mock_result.stdout = tsc_error

        with patch("subprocess.run", return_value=mock_result):
            issues = analyzer._run_tsc(file_path)
            assert len(issues) == 1
            assert issues[0].level == "bug"
            assert "TS2322" in issues[0].message

        file_path.unlink()


class TestAnalyze:
    """analyzeメソッドの統合テスト"""

    def test_analyze_code_only(self):
        """コードのみの解析（ファイルなし）"""
        analyzer = JavaScriptAnalyzer()
        code = """
console.log('debug');
var x = 5;
"""
        issues = analyzer.analyze(code)
        assert len(issues) >= 2  # console.log と var

    def test_analyze_with_file(self):
        """ファイル付き解析"""
        config = JSAnalysisConfig(use_eslint=False)  # ESLintは無効化
        analyzer = JavaScriptAnalyzer(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("eval('alert(1)');")
            f.flush()
            file_path = Path(f.name)

        issues = analyzer.analyze("eval('alert(1)');", file_path)
        assert any("eval" in i.message for i in issues)

        file_path.unlink()
