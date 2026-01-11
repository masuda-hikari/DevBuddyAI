"""Go Analyzerのテスト"""

from devbuddy.analyzers.go_analyzer import GoAnalyzer, GoAnalysisConfig


class TestGoAnalyzerPatterns:
    """パターンベース解析のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = GoAnalyzer()

    def test_detect_panic(self):
        """panic()の検出"""
        code = """
package main

func main() {
    if err != nil {
        panic("something went wrong")
    }
}
"""
        issues = self.analyzer.analyze(code)
        assert any("panic()" in i.message for i in issues)
        has_panic_warn = any(
            i.level == "warning" for i in issues if "panic" in i.message
        )
        assert has_panic_warn

    def test_detect_recover(self):
        """recover()の検出"""
        code = """
package main

func main() {
    defer func() {
        if r := recover(); r != nil {
            fmt.Println("Recovered:", r)
        }
    }()
}
"""
        issues = self.analyzer.analyze(code)
        assert any("recover()" in i.message for i in issues)

    def test_detect_fmt_print(self):
        """fmt.Print*の検出"""
        code = """
package main

import "fmt"

func main() {
    fmt.Println("Hello")
    fmt.Printf("Value: %d", 42)
}
"""
        issues = self.analyzer.analyze(code)
        assert any("fmt.Print" in i.message for i in issues)

    def test_detect_error_ignore(self):
        """エラー無視の検出"""
        code = """
package main

func main() {
    _ = err
}
"""
        issues = self.analyzer.analyze(code)
        assert any("Error being ignored" in i.message for i in issues)

    def test_detect_defer_error_ignore(self):
        """defer内のエラー無視検出"""
        code = """
package main

func main() {
    f, _ := os.Open("file.txt")
    defer f.Close()
}
"""
        issues = self.analyzer.analyze(code)
        assert any("Deferred function" in i.message for i in issues)

    def test_detect_todo(self):
        """TODO/FIXMEの検出"""
        code = """
package main

func main() {
    // TODO: Implement this function
    // FIXME: Fix this bug
}
"""
        issues = self.analyzer.analyze(code)
        assert any("TODO/FIXME" in i.message for i in issues)

    def test_detect_time_sleep(self):
        """time.Sleepの検出"""
        code = """
package main

import "time"

func main() {
    time.Sleep(time.Second)
}
"""
        issues = self.analyzer.analyze(code)
        assert any("time.Sleep" in i.message for i in issues)

    def test_detect_global_variable(self):
        """グローバル変数の検出"""
        code = """
package main

var globalConfig = "default"

func main() {}
"""
        issues = self.analyzer.analyze(code)
        assert any("Global variable" in i.message for i in issues)

    def test_detect_unsafe(self):
        """unsafeパッケージの検出"""
        code = """
package main

import "unsafe"

func main() {
    ptr := unsafe.Pointer(&x)
}
"""
        issues = self.analyzer.analyze(code)
        assert any("unsafe" in i.message for i in issues)
        has_unsafe_warn = any(
            i.level == "warning" for i in issues if "unsafe" in i.message
        )
        assert has_unsafe_warn

    def test_detect_reflect(self):
        """reflectパッケージの検出"""
        code = """
package main

import "reflect"

func main() {
    t := reflect.TypeOf(x)
}
"""
        issues = self.analyzer.analyze(code)
        assert any("Reflection" in i.message for i in issues)

    def test_detect_goto(self):
        """goto文の検出"""
        code = """
package main

func main() {
    goto label
label:
    fmt.Println("jumped")
}
"""
        issues = self.analyzer.analyze(code)
        assert any("goto" in i.message for i in issues)

    def test_detect_non_standard_err_name(self):
        """非標準エラー変数名の検出"""
        code = """
package main

func main() {
    result, err1 := doSomething()
    result2, err2 := doSomethingElse()
}
"""
        issues = self.analyzer.analyze(code)
        assert any("Non-standard error" in i.message for i in issues)

    def test_detect_empty_interface(self):
        """interface{}の検出"""
        code = """
package main

func process(data interface{}) {
}
"""
        issues = self.analyzer.analyze(code)
        assert any("interface{}" in i.message for i in issues)


class TestGoAnalyzerSyntaxCheck:
    """構文チェックのテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = GoAnalyzer()

    def test_valid_syntax(self):
        """有効な構文"""
        code = """
package main

func main() {
    x := 5
    fmt.Println(x)
}
"""
        valid, error = self.analyzer.check_syntax(code)
        assert valid is True
        assert error is None

    def test_unclosed_brace(self):
        """閉じられていない括弧"""
        code = """
package main

func main() {
    x := 5
"""
        valid, error = self.analyzer.check_syntax(code)
        assert valid is False
        assert "Unclosed" in error or "bracket" in error.lower()

    def test_mismatched_brackets(self):
        """不一致の括弧"""
        code = """
package main

func main() {
    arr := [1, 2, 3)
}
"""
        valid, error = self.analyzer.check_syntax(code)
        assert valid is False
        assert "Mismatch" in error or "bracket" in error.lower()

    def test_string_handling(self):
        """文字列内の括弧を無視"""
        code = """
package main

func main() {
    s := "This has { unbalanced ( brackets"
}
"""
        valid, error = self.analyzer.check_syntax(code)
        assert valid is True

    def test_raw_string_handling(self):
        """raw文字列の処理"""
        code = """
package main

func main() {
    s := `Raw string with { brackets (`
}
"""
        valid, error = self.analyzer.check_syntax(code)
        assert valid is True

    def test_comment_handling(self):
        """コメント内の括弧を無視"""
        code = """
package main

func main() {
    // This comment has { unbalanced ( brackets
    /* Multi-line { comment ( */
}
"""
        valid, error = self.analyzer.check_syntax(code)
        assert valid is True


class TestGoAnalyzerGetFunctions:
    """関数取得のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = GoAnalyzer()

    def test_get_simple_functions(self):
        """単純な関数の取得"""
        code = """
package main

func main() {}
func helper() {}
func calculate(x int) int { return x * 2 }
"""
        functions = self.analyzer.get_functions(code)
        assert "main" in functions
        assert "helper" in functions
        assert "calculate" in functions

    def test_get_exported_functions(self):
        """エクスポート関数の取得"""
        code = """
package mypackage

func PublicFunc() {}
func privateFunc() {}
"""
        functions = self.analyzer.get_functions(code)
        assert "PublicFunc" in functions
        assert "privateFunc" in functions


class TestGoAnalyzerGetTypes:
    """型取得のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = GoAnalyzer()

    def test_get_structs(self):
        """構造体の取得"""
        code = """
package main

type Point struct {
    X int
    Y int
}

type Config struct {
    Name string
}
"""
        structs = self.analyzer.get_structs(code)
        assert "Point" in structs
        assert "Config" in structs

    def test_get_interfaces(self):
        """インターフェースの取得"""
        code = """
package main

type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}
"""
        interfaces = self.analyzer.get_interfaces(code)
        assert "Reader" in interfaces
        assert "Writer" in interfaces

    def test_get_types(self):
        """型の取得（struct + interface）"""
        code = """
package main

type Point struct {
    X int
}

type Reader interface {
    Read() error
}
"""
        types = self.analyzer.get_types(code)
        assert "Point" in types
        assert "Reader" in types


class TestGoAnalyzerGetImports:
    """import取得のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = GoAnalyzer()

    def test_get_single_import(self):
        """単一importの取得"""
        code = """
package main

import "fmt"
"""
        imports = self.analyzer.get_imports(code)
        assert "fmt" in imports

    def test_get_group_imports(self):
        """グループimportの取得"""
        code = """
package main

import (
    "fmt"
    "os"
    "path/filepath"
)
"""
        imports = self.analyzer.get_imports(code)
        assert "fmt" in imports
        assert "os" in imports
        assert "path/filepath" in imports


class TestGoAnalyzerGetPackages:
    """パッケージ取得のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = GoAnalyzer()

    def test_get_package(self):
        """パッケージ名の取得"""
        code = """
package mypackage

func Hello() {}
"""
        packages = self.analyzer.get_packages(code)
        assert "mypackage" in packages


class TestGoAnalyzerGetConsts:
    """定数取得のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = GoAnalyzer()

    def test_get_single_const(self):
        """単一constの取得"""
        code = """
package main

const MaxSize = 100
const Name = "app"
"""
        consts = self.analyzer.get_consts(code)
        assert "MaxSize" in consts
        assert "Name" in consts

    def test_get_group_consts(self):
        """グループconstの取得"""
        code = """
package main

const (
    StatusOK = 200
    StatusNotFound = 404
    StatusError = 500
)
"""
        consts = self.analyzer.get_consts(code)
        assert "StatusOK" in consts
        assert "StatusNotFound" in consts
        assert "StatusError" in consts


class TestGoAnalyzerGetMethods:
    """メソッド取得のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = GoAnalyzer()

    def test_get_value_receiver_method(self):
        """値レシーバメソッドの取得"""
        code = """
package main

type Point struct {
    X, Y int
}

func (p Point) String() string {
    return fmt.Sprintf("(%d, %d)", p.X, p.Y)
}
"""
        methods = self.analyzer.get_methods(code)
        assert any(
            m.get("receiver") == "Point" and m.get("method") == "String"
            for m in methods
        )

    def test_get_pointer_receiver_method(self):
        """ポインタレシーバメソッドの取得"""
        code = """
package main

type Counter struct {
    count int
}

func (c *Counter) Increment() {
    c.count++
}
"""
        methods = self.analyzer.get_methods(code)
        assert any(
            m.get("receiver") == "Counter" and m.get("method") == "Increment"
            for m in methods
        )


class TestGoAnalyzerConfig:
    """設定のテスト"""

    def test_default_config(self):
        """デフォルト設定"""
        config = GoAnalysisConfig()
        assert config.use_go_vet is True
        assert config.use_staticcheck is False
        assert config.use_golangci_lint is False
        assert config.timeout == 120

    def test_custom_config(self):
        """カスタム設定"""
        config = GoAnalysisConfig(
            use_go_vet=False,
            use_staticcheck=True,
            use_golangci_lint=True,
            timeout=60,
        )
        analyzer = GoAnalyzer(config)
        assert analyzer.config.use_go_vet is False
        assert analyzer.config.use_staticcheck is True
        assert analyzer.config.use_golangci_lint is True
        assert analyzer.config.timeout == 60


class TestGoAnalyzerEdgeCases:
    """エッジケースのテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = GoAnalyzer()

    def test_empty_code(self):
        """空のコード"""
        code = ""
        issues = self.analyzer.analyze(code)
        assert isinstance(issues, list)

    def test_whitespace_only(self):
        """空白のみのコード"""
        code = "   \n\n   \t\t   "
        issues = self.analyzer.analyze(code)
        assert isinstance(issues, list)

    def test_valid_code_no_issues(self):
        """問題のないコード（パターン検出対象なし）"""
        code = """
package main

func add(a, b int) int {
    return a + b
}
"""
        issues = self.analyzer.analyze(code)
        # このコードには検出対象のパターンがない
        assert isinstance(issues, list)

    def test_complex_code(self):
        """複雑なコード"""
        code = """
package main

import (
    "fmt"
    "sync"
)

type Server struct {
    mu    sync.Mutex
    conns int
}

func NewServer() *Server {
    return &Server{}
}

func (s *Server) AddConnection() {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.conns++
}

func (s *Server) GetConnections() int {
    s.mu.Lock()
    defer s.mu.Unlock()
    return s.conns
}

func main() {
    server := NewServer()
    server.AddConnection()
}
"""
        # 解析が例外を投げないことを確認
        issues = self.analyzer.analyze(code)
        assert isinstance(issues, list)

        # 構造体、関数、メソッドが取得できる
        structs = self.analyzer.get_structs(code)
        assert "Server" in structs

        functions = self.analyzer.get_functions(code)
        assert "NewServer" in functions
        assert "main" in functions

        methods = self.analyzer.get_methods(code)
        has_add_conn = any(
            m.get("receiver") == "Server"
            and m.get("method") == "AddConnection"
            for m in methods
        )
        assert has_add_conn

        imports = self.analyzer.get_imports(code)
        assert "fmt" in imports
        assert "sync" in imports


class TestGoAnalyzerExternalTools:
    """外部ツール連携のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        config = GoAnalysisConfig(
            use_go_vet=True,
            use_staticcheck=True,
            use_golangci_lint=True,
            timeout=30,
        )
        self.analyzer = GoAnalyzer(config)

    def test_run_go_vet_no_file(self):
        """存在しないファイルでのgo vet実行"""
        from pathlib import Path
        issues = self.analyzer._run_go_vet(Path("/nonexistent/file.go"))
        assert issues == []

    def test_run_staticcheck_no_file(self):
        """存在しないファイルでのstaticcheck実行"""
        from pathlib import Path
        issues = self.analyzer._run_staticcheck(Path("/nonexistent/file.go"))
        assert issues == []

    def test_run_golangci_lint_no_file(self):
        """存在しないファイルでのgolangci-lint実行"""
        from pathlib import Path
        issues = self.analyzer._run_golangci_lint(Path("/nonexistent/file.go"))
        assert issues == []

    def test_config_all_enabled(self):
        """全外部ツール有効時の設定確認"""
        assert self.analyzer.config.use_go_vet is True
        assert self.analyzer.config.use_staticcheck is True
        assert self.analyzer.config.use_golangci_lint is True


class TestGoAnalyzerMagicNumber:
    """マジックナンバー検出のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = GoAnalyzer()

    def test_detect_magic_number(self):
        """マジックナンバーの検出"""
        code = """
package main

func main() {
    threshold := 42
    limit := 100
}
"""
        issues = self.analyzer.analyze(code)
        magic_issues = [i for i in issues if "Magic number" in i.message]
        assert len(magic_issues) >= 1

    def test_no_magic_number_small(self):
        """小さい数値は検出しない"""
        code = """
package main

func main() {
    x := 0
    y := 1
    z := 2
}
"""
        issues = self.analyzer.analyze(code)
        # 0, 1, 2 はマジックナンバーとして検出しない
        magic_issues = [i for i in issues if "Magic number" in i.message]
        assert len(magic_issues) == 0


class TestGoAnalyzerLineNumber:
    """行番号検出の精度テスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = GoAnalyzer()

    def test_issue_line_number(self):
        """問題の行番号が正しい"""
        code = """package main

func main() {
    panic("test")
}
"""
        issues = self.analyzer.analyze(code)
        panic_issues = [i for i in issues if "panic()" in i.message]
        assert len(panic_issues) == 1
        # panic は4行目にある
        assert panic_issues[0].line == 4
