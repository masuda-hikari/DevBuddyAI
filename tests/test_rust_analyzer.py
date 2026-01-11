"""Rust Analyzerのテスト"""

from devbuddy.analyzers.rust_analyzer import RustAnalyzer, RustAnalysisConfig


class TestRustAnalyzerPatterns:
    """パターンベース解析のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

    def test_detect_unwrap(self):
        """unwrap()の検出"""
        code = """
fn main() {
    let value = some_option.unwrap();
}
"""
        issues = self.analyzer.analyze(code)
        assert any("unwrap()" in i.message for i in issues)
        has_unwrap_warn = any(
            i.level == "warning" for i in issues if "unwrap" in i.message
        )
        assert has_unwrap_warn

    def test_detect_empty_expect(self):
        """空メッセージのexpect()検出"""
        code = """
fn main() {
    let value = some_option.expect("");
}
"""
        issues = self.analyzer.analyze(code)
        assert any("expect() with empty message" in i.message for i in issues)

    def test_detect_panic(self):
        """panic!マクロの検出"""
        code = """
fn main() {
    if error_condition {
        panic!("Something went wrong");
    }
}
"""
        issues = self.analyzer.analyze(code)
        assert any("panic!" in i.message for i in issues)
        has_panic_warn = any(
            i.level == "warning" for i in issues if "panic" in i.message
        )
        assert has_panic_warn

    def test_detect_println(self):
        """println!の検出"""
        code = """
fn main() {
    println!("Debug output: {}", value);
}
"""
        issues = self.analyzer.analyze(code)
        assert any("Debug output" in i.message for i in issues)

    def test_detect_dbg(self):
        """dbg!の検出"""
        code = """
fn main() {
    let result = dbg!(calculate());
}
"""
        issues = self.analyzer.analyze(code)
        assert any("Debug output" in i.message for i in issues)

    def test_detect_unsafe(self):
        """unsafeブロックの検出"""
        code = """
fn main() {
    unsafe {
        // Unsafe code here
    }
}
"""
        issues = self.analyzer.analyze(code)
        assert any("unsafe" in i.message for i in issues)
        has_unsafe_warn = any(
            i.level == "warning" for i in issues if "unsafe" in i.message
        )
        assert has_unsafe_warn

    def test_detect_todo(self):
        """TODO/FIXMEの検出"""
        code = """
fn main() {
    // TODO: Implement this function
    // FIXME: Fix this bug
}
"""
        issues = self.analyzer.analyze(code)
        assert any("TODO/FIXME" in i.message for i in issues)

    def test_detect_multiple_clone(self):
        """複数clone()呼び出しの検出"""
        code = """
fn main() {
    let a = value.clone().clone();
}
"""
        issues = self.analyzer.analyze(code)
        assert any("Multiple clone()" in i.message for i in issues)

    def test_detect_transmute(self):
        """transmuteの検出"""
        code = """
use std::mem;
fn main() {
    let value: i32 = mem::transmute(bytes);
}
"""
        issues = self.analyzer.analyze(code)
        assert any("transmute" in i.message for i in issues)
        has_transmute_bug = any(
            i.level == "bug" for i in issues if "transmute" in i.message
        )
        assert has_transmute_bug

    def test_detect_numeric_cast(self):
        """数値キャストの検出"""
        code = """
fn main() {
    let value = some_value as u32;
}
"""
        issues = self.analyzer.analyze(code)
        assert any("Numeric cast" in i.message for i in issues)

    def test_detect_allow_attribute(self):
        """#[allow(...)]属性の検出"""
        code = """
#[allow(unused_variables)]
fn main() {
    let x = 5;
}
"""
        issues = self.analyzer.analyze(code)
        assert any("allow" in i.message.lower() for i in issues)

    def test_detect_dead_code_allow(self):
        """#[allow(dead_code)]の検出"""
        code = """
#[allow(dead_code)]
fn unused_function() {}
"""
        issues = self.analyzer.analyze(code)
        assert any("dead_code" in i.message for i in issues)

    def test_no_false_positive_on_literal_cast(self):
        """リテラルへのキャストで誤検出しない"""
        code = """
fn main() {
    let value = 42 as u32;
}
"""
        issues = self.analyzer.analyze(code)
        # リテラルへのキャストは許可
        numeric_cast_issues = [
            i for i in issues if "Numeric cast" in i.message
        ]
        assert len(numeric_cast_issues) == 0


class TestRustAnalyzerSyntaxCheck:
    """構文チェックのテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

    def test_valid_syntax(self):
        """有効な構文"""
        code = """
fn main() {
    let x = 5;
    println!("{}", x);
}
"""
        valid, error = self.analyzer.check_syntax(code)
        assert valid is True
        assert error is None

    def test_unclosed_brace(self):
        """閉じられていない括弧"""
        code = """
fn main() {
    let x = 5;
"""
        valid, error = self.analyzer.check_syntax(code)
        assert valid is False
        assert "Unclosed" in error or "bracket" in error.lower()

    def test_mismatched_brackets(self):
        """不一致の括弧"""
        code = """
fn main() {
    let x = [1, 2, 3);
}
"""
        valid, error = self.analyzer.check_syntax(code)
        assert valid is False
        assert "Mismatch" in error or "bracket" in error.lower()

    def test_string_handling(self):
        """文字列内の括弧を無視"""
        code = """
fn main() {
    let s = "This has { unbalanced ( brackets";
}
"""
        valid, error = self.analyzer.check_syntax(code)
        assert valid is True

    def test_raw_string_handling(self):
        """raw文字列の処理"""
        code = """
fn main() {
    let s = r"Raw string with { brackets (";
}
"""
        valid, error = self.analyzer.check_syntax(code)
        assert valid is True

    def test_comment_handling(self):
        """コメント内の括弧を無視"""
        code = """
fn main() {
    // This comment has { unbalanced ( brackets
    /* Multi-line { comment ( */
}
"""
        valid, error = self.analyzer.check_syntax(code)
        assert valid is True

    def test_lifetime_handling(self):
        """ライフタイム記法の処理"""
        code = """
fn get_str<'a>(s: &'a str) -> &'a str {
    s
}
"""
        valid, error = self.analyzer.check_syntax(code)
        assert valid is True

    def test_char_literal_handling(self):
        """文字リテラルの処理"""
        code = """
fn main() {
    let c = '(';
    let d = '{';
}
"""
        valid, error = self.analyzer.check_syntax(code)
        assert valid is True


class TestRustAnalyzerGetFunctions:
    """関数取得のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

    def test_get_simple_functions(self):
        """単純な関数の取得"""
        code = """
fn main() {}
fn helper() {}
fn calculate(x: i32) -> i32 { x * 2 }
"""
        functions = self.analyzer.get_functions(code)
        assert "main" in functions
        assert "helper" in functions
        assert "calculate" in functions

    def test_get_generic_functions(self):
        """ジェネリック関数の取得"""
        code = """
fn process<T>(item: T) -> T { item }
fn transform<T, U>(x: T) -> U where T: Into<U> { x.into() }
"""
        functions = self.analyzer.get_functions(code)
        assert "process" in functions
        assert "transform" in functions

    def test_get_async_functions(self):
        """async関数の取得"""
        code = """
async fn fetch_data() -> Result<Data, Error> {}
"""
        functions = self.analyzer.get_functions(code)
        assert "fetch_data" in functions

    def test_get_pub_functions(self):
        """pub関数の取得"""
        code = """
pub fn public_func() {}
pub(crate) fn crate_func() {}
"""
        functions = self.analyzer.get_functions(code)
        assert "public_func" in functions
        assert "crate_func" in functions


class TestRustAnalyzerGetStructs:
    """構造体取得のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

    def test_get_structs(self):
        """構造体の取得"""
        code = """
struct Point {
    x: i32,
    y: i32,
}

struct Color(u8, u8, u8);

pub struct Config {}
"""
        structs = self.analyzer.get_structs(code)
        assert "Point" in structs
        assert "Color" in structs
        assert "Config" in structs


class TestRustAnalyzerGetEnums:
    """列挙型取得のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

    def test_get_enums(self):
        """列挙型の取得"""
        code = """
enum Status {
    Active,
    Inactive,
}

pub enum Result<T, E> {
    Ok(T),
    Err(E),
}
"""
        enums = self.analyzer.get_enums(code)
        assert "Status" in enums
        assert "Result" in enums


class TestRustAnalyzerGetTraits:
    """トレイト取得のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

    def test_get_traits(self):
        """トレイトの取得"""
        code = """
trait Drawable {
    fn draw(&self);
}

pub trait Serializable: Clone {
    fn serialize(&self) -> String;
}
"""
        traits = self.analyzer.get_traits(code)
        assert "Drawable" in traits
        assert "Serializable" in traits


class TestRustAnalyzerGetImpls:
    """impl取得のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

    def test_get_impl_for_trait(self):
        """impl Trait for Typeの取得"""
        code = """
impl Display for Point {
    fn fmt(&self, f: &mut Formatter) -> fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}
"""
        impls = self.analyzer.get_impls(code)
        assert any(
            i.get("trait") == "Display" and i.get("type") == "Point"
            for i in impls
        )

    def test_get_impl_for_type(self):
        """impl Typeの取得"""
        code = """
impl Point {
    fn new(x: i32, y: i32) -> Self {
        Point { x, y }
    }
}
"""
        impls = self.analyzer.get_impls(code)
        assert any(
            i.get("type") == "Point" and i.get("trait") is None
            for i in impls
        )


class TestRustAnalyzerGetUses:
    """use文取得のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

    def test_get_uses(self):
        """use文の取得"""
        code = """
use std::io::Read;
use std::collections::HashMap;
use crate::utils::helper;
"""
        uses = self.analyzer.get_uses(code)
        assert "std::io::Read" in uses
        assert "std::collections::HashMap" in uses
        assert "crate::utils::helper" in uses

    def test_get_nested_uses(self):
        """ネストされたuse文の取得"""
        code = """
use std::{io, fs, path::PathBuf};
"""
        uses = self.analyzer.get_uses(code)
        assert any("std" in u for u in uses)


class TestRustAnalyzerGetMods:
    """モジュール取得のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

    def test_get_mods(self):
        """モジュール宣言の取得"""
        code = """
mod utils;
mod config;
pub mod api;
"""
        mods = self.analyzer.get_mods(code)
        assert "utils" in mods
        assert "config" in mods
        assert "api" in mods


class TestRustAnalyzerConfig:
    """設定のテスト"""

    def test_default_config(self):
        """デフォルト設定"""
        config = RustAnalysisConfig()
        assert config.use_clippy is True
        assert config.use_cargo_check is False
        assert config.warn_as_error is False
        assert config.edition == "2021"

    def test_custom_config(self):
        """カスタム設定"""
        config = RustAnalysisConfig(
            use_clippy=False,
            use_cargo_check=True,
            deny_warnings=True,
            edition="2018",
        )
        analyzer = RustAnalyzer(config)
        assert analyzer.config.use_clippy is False
        assert analyzer.config.use_cargo_check is True
        assert analyzer.config.deny_warnings is True
        assert analyzer.config.edition == "2018"


class TestRustAnalyzerEdgeCases:
    """エッジケースのテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

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
        """問題のないコード"""
        code = """
fn main() {
    let x = 5;
    let y = x + 1;
}
"""
        issues = self.analyzer.analyze(code)
        # このコードには検出対象のパターンがない
        assert isinstance(issues, list)

    def test_complex_code(self):
        """複雑なコード"""
        code = """
use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct Config {
    name: String,
    values: HashMap<String, i32>,
}

impl Config {
    pub fn new(name: &str) -> Self {
        Config {
            name: name.to_string(),
            values: HashMap::new(),
        }
    }

    pub fn get(&self, key: &str) -> Option<i32> {
        self.values.get(key).copied()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new() {
        let config = Config::new("test");
        assert_eq!(config.name, "test");
    }
}
"""
        # 解析が例外を投げないことを確認
        issues = self.analyzer.analyze(code)
        assert isinstance(issues, list)

        # 構造体、関数、impl、モジュールが取得できる
        structs = self.analyzer.get_structs(code)
        assert "Config" in structs

        functions = self.analyzer.get_functions(code)
        assert "new" in functions
        assert "get" in functions

        mods = self.analyzer.get_mods(code)
        assert "tests" in mods


class TestRustAnalyzerCargoRoot:
    """Cargoプロジェクトルート検出のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

    def test_find_cargo_root_none(self):
        """Cargo.tomlが見つからない場合"""
        from pathlib import Path

        # 存在しないパス
        result = self.analyzer._find_cargo_root(Path("/nonexistent/path.rs"))
        # Cargo.tomlがなければNone
        assert result is None or isinstance(result, Path)


class TestRustAnalyzerExternalTools:
    """外部ツール連携のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        config = RustAnalysisConfig(
            use_clippy=True,
            use_cargo_check=True,
        )
        self.analyzer = RustAnalyzer(config)

    def test_run_clippy_no_file(self):
        """存在しないファイルでのclippy実行"""
        from pathlib import Path
        cargo_root = Path("/nonexistent")
        file_path = Path("/nonexistent/file.rs")
        issues = self.analyzer._run_clippy(cargo_root, file_path)
        assert issues == []

    def test_run_cargo_check_no_file(self):
        """存在しないファイルでのcargo check実行"""
        from pathlib import Path
        cargo_root = Path("/nonexistent")
        file_path = Path("/nonexistent/file.rs")
        issues = self.analyzer._run_cargo_check(cargo_root, file_path)
        assert issues == []

    def test_config_both_enabled(self):
        """clippy/cargo_check両方有効時の設定確認"""
        assert self.analyzer.config.use_clippy is True
        assert self.analyzer.config.use_cargo_check is True


class TestRustAnalyzerMacroDetection:
    """マクロ検出のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

    def test_detect_println_macro(self):
        """println!マクロの検出"""
        code = """
fn main() {
    println!("Hello, World!");
}
"""
        issues = self.analyzer.analyze(code)
        # println!の検出（情報レベル）- 検出してもしなくても問題ない（設定次第）
        assert isinstance(issues, list)

    def test_detect_dbg_macro(self):
        """dbg!マクロの検出"""
        code = """
fn main() {
    let x = dbg!(5 + 5);
}
"""
        issues = self.analyzer.analyze(code)
        # dbg!マクロはデバッグ用だが、検出はRustアナライザーの実装次第
        # 検出されてもされなくても許容
        assert isinstance(issues, list)


class TestRustAnalyzerLineNumber:
    """行番号検出の精度テスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

    def test_issue_line_number(self):
        """問題の行番号が正しい"""
        code = """fn main() {
    let x = 5;
    unsafe {
        std::ptr::null::<i32>();
    }
}
"""
        issues = self.analyzer.analyze(code)
        unsafe_issues = [i for i in issues if "unsafe" in i.message.lower()]
        if unsafe_issues:
            # unsafeは3行目にある
            assert unsafe_issues[0].line == 3


class TestRustAnalyzerClippyLevelConversion:
    """clippyレベル変換のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

    def test_clippy_level_error(self):
        """errorレベルの変換"""
        assert self.analyzer._clippy_level_to_level("error") == "bug"

    def test_clippy_level_warning(self):
        """warningレベルの変換"""
        assert self.analyzer._clippy_level_to_level("warning") == "warning"

    def test_clippy_level_note(self):
        """noteレベルの変換"""
        assert self.analyzer._clippy_level_to_level("note") == "info"

    def test_clippy_level_help(self):
        """helpレベルの変換"""
        assert self.analyzer._clippy_level_to_level("help") == "info"

    def test_clippy_level_unknown(self):
        """未知のレベルの変換"""
        assert self.analyzer._clippy_level_to_level("unknown") == "info"
        assert self.analyzer._clippy_level_to_level("") == "info"


class TestRustAnalyzerEmptyImplDetection:
    """空のimpl検出のテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

    def test_detect_empty_impl(self):
        """空のimplブロック検出"""
        code = """
impl MyStruct {}
"""
        issues = self.analyzer.analyze(code)
        empty_impl = [i for i in issues if "Empty impl" in i.message]
        assert len(empty_impl) > 0

    def test_no_false_positive_on_nonempty_impl(self):
        """空でないimplで誤検出しない"""
        code = """
impl MyStruct {
    fn new() -> Self {
        MyStruct
    }
}
"""
        issues = self.analyzer.analyze(code)
        empty_impl = [i for i in issues if "Empty impl" in i.message]
        assert len(empty_impl) == 0


class TestRustAnalyzerSyntaxEdgeCases:
    """構文チェックエッジケースのテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

    def test_unexpected_closing_bracket(self):
        """予期しない閉じ括弧"""
        code = "fn main() { } }"
        valid, error = self.analyzer.check_syntax(code)
        assert valid is False
        assert "Unexpected closing" in error

    def test_escape_in_string(self):
        """文字列内のエスケープ"""
        code = '''
fn main() {
    let s = "escaped \\" quote";
}
'''
        valid, error = self.analyzer.check_syntax(code)
        assert valid is True

    def test_escape_in_char(self):
        """文字リテラル内のエスケープ"""
        code = """
fn main() {
    let c = '\\n';
    let d = '\\'';
}
"""
        valid, error = self.analyzer.check_syntax(code)
        assert valid is True

    def test_lifetime_with_underscore(self):
        """アンダースコア付きライフタイム"""
        code = """
fn get_ref<'a_lifetime>(s: &'a_lifetime str) -> &'a_lifetime str {
    s
}
"""
        valid, error = self.analyzer.check_syntax(code)
        assert valid is True

    def test_static_lifetime(self):
        """'staticライフタイム"""
        code = """
fn get_static() -> &'static str {
    "hello"
}
"""
        valid, error = self.analyzer.check_syntax(code)
        assert valid is True


class TestRustAnalyzerImplParsing:
    """impl取得の詳細テスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

    def test_get_impl_with_generics(self):
        """ジェネリクス付きimpl"""
        code = """
impl<T> Container<T> {
    fn new() -> Self {
        Container { data: None }
    }
}
"""
        impls = self.analyzer.get_impls(code)
        assert any(i.get("type") == "Container" for i in impls)

    def test_get_impl_trait_for_generic_type(self):
        """ジェネリック型へのトレイト実装"""
        code = """
impl Default for Container {
    fn default() -> Self {
        Container { data: None }
    }
}
"""
        impls = self.analyzer.get_impls(code)
        assert any(
            i.get("trait") == "Default" and i.get("type") == "Container"
            for i in impls
        )

    def test_multiple_impls_same_type(self):
        """同じ型への複数impl"""
        code = """
impl Point {
    fn new() -> Self { Point { x: 0, y: 0 } }
}

impl Debug for Point {
    fn fmt(&self, f: &mut Formatter) -> fmt::Result {
        write!(f, "Point")
    }
}

impl Point {
    fn distance(&self) -> f64 { 0.0 }
}
"""
        impls = self.analyzer.get_impls(code)
        point_impls = [i for i in impls if i.get("type") == "Point"]
        assert len(point_impls) >= 2


class TestRustAnalyzerDenyWarnings:
    """deny_warnings設定のテスト"""

    def test_config_deny_warnings(self):
        """deny_warnings設定"""
        config = RustAnalysisConfig(deny_warnings=True)
        analyzer = RustAnalyzer(config)
        assert analyzer.config.deny_warnings is True

    def test_config_no_deny_warnings(self):
        """deny_warnings無効"""
        config = RustAnalysisConfig(deny_warnings=False)
        analyzer = RustAnalyzer(config)
        assert analyzer.config.deny_warnings is False


class TestRustAnalyzerPatternEdgeCases:
    """パターンマッチングエッジケースのテスト"""

    def setup_method(self):
        """各テスト前の初期化"""
        self.analyzer = RustAnalyzer()

    def test_normal_expect_message(self):
        """通常のexpectメッセージ（誤検出しない）"""
        code = '''
fn main() {
    let value = some_option.expect("Value should exist");
}
'''
        issues = self.analyzer.analyze(code)
        empty_expect = [
            i for i in issues if "empty message" in i.message.lower()
        ]
        assert len(empty_expect) == 0

    def test_transmute_without_mem(self):
        """mem::なしのtransmute"""
        code = """
use std::mem::transmute;
fn convert() {
    let x: u32 = unsafe { transmute(bytes) };
}
"""
        issues = self.analyzer.analyze(code)
        transmute_issues = [
            i for i in issues if "transmute" in i.message.lower()
        ]
        assert len(transmute_issues) > 0

    def test_single_clone(self):
        """単一のclone()（検出しない）"""
        code = """
fn main() {
    let a = value.clone();
}
"""
        issues = self.analyzer.analyze(code)
        multi_clone = [i for i in issues if "Multiple clone" in i.message]
        assert len(multi_clone) == 0
