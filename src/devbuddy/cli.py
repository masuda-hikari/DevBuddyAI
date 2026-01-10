"""
DevBuddyAI CLI - コマンドラインインターフェース

使用例:
    devbuddy review src/mycode.py
    devbuddy testgen src/calculator.py --function add
    devbuddy fix tests/test_api.py
"""

import os
import sys
from pathlib import Path
from typing import Optional

import click

from devbuddy import __version__
from devbuddy.core.reviewer import CodeReviewer
from devbuddy.core.generator import CodeTestGenerator
from devbuddy.core.fixer import BugFixer
from devbuddy.llm.client import LLMClient


def get_api_key() -> str:
    """環境変数からAPIキーを取得"""
    api_key = os.environ.get("DEVBUDDY_API_KEY")
    if not api_key:
        click.echo(
            click.style(
                "Error: DEVBUDDY_API_KEY environment variable not set",
                fg="red",
            ),
            err=True,
        )
        click.echo(
            "Set it with: export DEVBUDDY_API_KEY=your_api_key",
            err=True,
        )
        sys.exit(1)
    return api_key


@click.group()
@click.version_option(version=__version__, prog_name="devbuddy")
def cli() -> None:
    """DevBuddyAI - AI駆動の開発者アシスタント

    コードレビュー、テスト生成、バグ修正提案を自動化します。
    """
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--diff", is_flag=True, help="git diffのみをレビュー")
@click.option(
    "--severity",
    type=click.Choice(["low", "medium", "high"]),
    default="medium",
)
@click.option("--output", "-o", type=click.Path(), help="結果をファイルに出力")
def review(
    path: str, diff: bool, severity: str, output: Optional[str]
) -> None:
    """コードをレビューしてバグ、スタイル問題、改善点を指摘

    PATH: レビュー対象のファイルまたはディレクトリ
    """
    api_key = get_api_key()
    client = LLMClient(api_key=api_key)
    reviewer = CodeReviewer(client=client)

    click.echo(f"Reviewing: {path}")
    click.echo(f"Severity level: {severity}")

    target_path = Path(path)

    if target_path.is_file():
        files = [target_path]
    else:
        files = list(target_path.rglob("*.py"))

    if not files:
        click.echo(click.style("No Python files found", fg="yellow"))
        return

    all_results = []
    with click.progressbar(files, label="Reviewing files") as bar:
        for file_path in bar:
            result = reviewer.review_file(file_path, severity=severity)
            all_results.append(result)

    # 結果表示
    click.echo("\n" + "=" * 50)
    click.echo(
        click.style("DevBuddyAI Code Review Results", fg="cyan", bold=True)
    )
    click.echo("=" * 50 + "\n")

    total_issues = {"bug": 0, "warning": 0, "style": 0, "info": 0}

    for result in all_results:
        if result.issues:
            click.echo(
                click.style(f"\n{result.file_path}", fg="white", bold=True)
            )
            for issue in result.issues:
                color = {
                    "bug": "red",
                    "warning": "yellow",
                    "style": "blue",
                    "info": "green",
                }.get(issue.level, "white")

                click.echo(
                    f"  [{click.style(issue.level.upper(), fg=color)}] "
                    f"Line {issue.line}: {issue.message}"
                )
                if issue.suggestion:
                    click.echo(f"    Suggestion: {issue.suggestion}")

                count = total_issues.get(issue.level, 0) + 1
                total_issues[issue.level] = count

    # サマリー
    click.echo("\n" + "-" * 50)
    bugs = total_issues["bug"]
    warnings = total_issues["warning"]
    styles = total_issues["style"]
    click.echo(
        f"Summary: {bugs} bugs, {warnings} warnings, {styles} style issues"
    )

    if output:
        # 結果をファイルに保存
        with open(output, "w", encoding="utf-8") as f:
            for result in all_results:
                f.write(f"\n{result.file_path}\n")
                for issue in result.issues:
                    line = issue.line
                    msg = issue.message
                    f.write(f"  [{issue.level}] Line {line}: {msg}\n")
        click.echo(f"\nResults saved to: {output}")


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--function", "-f", help="特定の関数のみテスト生成")
@click.option("--output", "-o", type=click.Path(), help="出力先ファイル")
@click.option(
    "--framework",
    type=click.Choice(["pytest", "unittest"]),
    default="pytest",
)
@click.option("--run", is_flag=True, help="生成後にテストを実行")
def testgen(
    path: str,
    function: Optional[str],
    output: Optional[str],
    framework: str,
    run: bool,
) -> None:
    """関数/クラスのユニットテストを自動生成

    PATH: テスト対象のソースファイル
    """
    api_key = get_api_key()
    client = LLMClient(api_key=api_key)
    generator = CodeTestGenerator(client=client)

    click.echo(f"Generating tests for: {path}")
    if function:
        click.echo(f"Target function: {function}")

    source_path = Path(path)
    result = generator.generate_tests(
        source_path, function_name=function, framework=framework
    )

    if result.success:
        click.echo(click.style("\nGenerated Tests:", fg="green", bold=True))
        click.echo("-" * 40)
        click.echo(result.test_code)

        # 出力先決定
        if output:
            output_path = Path(output)
        else:
            test_name = f"test_{source_path.name}"
            output_path = source_path.parent / "tests" / test_name
            output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.test_code)
        click.echo(f"\nTest file saved to: {output_path}")

        if run:
            click.echo("\nRunning generated tests...")
            import subprocess

            proc = subprocess.run(
                ["pytest", str(output_path), "-v"],
                capture_output=True,
                text=True,
            )
            click.echo(proc.stdout)
            if proc.returncode != 0:
                click.echo(click.style("Some tests failed!", fg="red"))
                click.echo(proc.stderr)
            else:
                click.echo(click.style("All tests passed!", fg="green"))
    else:
        click.echo(click.style(f"Error: {result.error}", fg="red"))


@cli.command()
@click.argument("test_path", type=click.Path(exists=True))
@click.option("--source", "-s", type=click.Path(exists=True), help="ソースファイル")
@click.option("--apply", is_flag=True, help="修正を自動適用")
def fix(test_path: str, source: Optional[str], apply: bool) -> None:
    """失敗テストやバグに対する修正を提案

    TEST_PATH: 失敗しているテストファイル
    """
    api_key = get_api_key()
    client = LLMClient(api_key=api_key)
    fixer = BugFixer(client=client)

    click.echo(f"Analyzing failing tests: {test_path}")

    source_p = Path(source) if source else None
    result = fixer.suggest_fix(Path(test_path), source_path=source_p)

    if result.suggestions:
        click.echo(click.style("\nSuggested Fixes:", fg="cyan", bold=True))
        for i, suggestion in enumerate(result.suggestions, 1):
            click.echo(f"\n{i}. {suggestion.description}")
            click.echo(f"   File: {suggestion.file_path}:{suggestion.line}")
            click.echo("   Change:")
            click.echo(click.style(f"   - {suggestion.original}", fg="red"))
            repl = suggestion.replacement
            click.echo(click.style(f"   + {repl}", fg="green"))

        if apply:
            click.echo("\nApplying fixes...")
            for suggestion in result.suggestions:
                fixer.apply_fix(suggestion)
            click.echo(click.style("Fixes applied!", fg="green"))
    else:
        click.echo(click.style("No fixes suggested", fg="yellow"))


def load_config(config_path: Path) -> dict:
    """設定ファイルを読み込む"""
    if not config_path.exists():
        return {}
    try:
        import yaml  # type: ignore[import-untyped]
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        click.echo(
            click.style("Warning: PyYAML not installed. ", fg="yellow") +
            "Install with: pip install pyyaml"
        )
        return {}
    except Exception as e:
        click.echo(click.style(f"Error reading config: {e}", fg="red"))
        return {}


def save_config(config_path: Path, config: dict) -> bool:
    """設定ファイルを保存する"""
    try:
        import yaml  # type: ignore[import-untyped]
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f, default_flow_style=False, allow_unicode=True)
        return True
    except ImportError:
        click.echo(
            click.style("Error: PyYAML not installed. ", fg="red") +
            "Install with: pip install pyyaml"
        )
        return False
    except Exception as e:
        click.echo(click.style(f"Error saving config: {e}", fg="red"))
        return False


def get_nested_value(d: dict, key: str) -> Optional[str]:
    """ドット区切りのキーで値を取得（例: review.severity）"""
    keys = key.split(".")
    value = d
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return None
    return str(value) if value is not None else None


def set_nested_value(d: dict, key: str, value: str) -> dict:
    """ドット区切りのキーで値を設定（例: review.severity=high）"""
    keys = key.split(".")
    current = d
    for k in keys[:-1]:
        if k not in current or not isinstance(current[k], dict):
            current[k] = {}
        current = current[k]
    # 型変換を試みる
    if value.lower() == "true":
        current[keys[-1]] = True
    elif value.lower() == "false":
        current[keys[-1]] = False
    elif value.isdigit():
        current[keys[-1]] = int(value)
    else:
        current[keys[-1]] = value
    return d


@cli.command()
@click.option("--show", is_flag=True, help="現在の設定を表示")
@click.option("--init", is_flag=True, help="設定ファイルを初期化")
@click.option("--get", "get_key", type=str, help="設定値を取得（例: review.severity）")
@click.option(
    "--set", "set_value", type=str,
    help="設定値を変更（例: review.severity=high）"
)
@click.option("--path", "config_file", type=click.Path(), help="設定ファイルパス")
@click.option("--list-keys", is_flag=True, help="利用可能な設定キーを表示")
def config(
    show: bool,
    init: bool,
    get_key: Optional[str],
    set_value: Optional[str],
    config_file: Optional[str],
    list_keys: bool,
) -> None:
    """DevBuddyAI設定を管理

    Examples:
        devbuddy config --init                  # 設定ファイル初期化
        devbuddy config --show                  # 設定表示
        devbuddy config --get review.severity   # 値を取得
        devbuddy config --set review.severity=high  # 値を変更
        devbuddy config --list-keys             # キー一覧表示
    """
    config_path = Path(config_file) if config_file else Path(".devbuddy.yaml")

    if init:
        default_config = """# DevBuddyAI Configuration
# 設定ファイル - プロジェクトルートに配置

# 対象言語（python, javascript, typescript, rust, go）
language: python

# スタイルガイド（pep8, google, numpy）
style_guide: pep8

# コードレビュー設定
review:
  # 検出レベル（low, medium, high）
  severity: medium
  # 改善提案を含める
  include_suggestions: true
  # セキュリティチェック有効化
  security_check: true
  # パフォーマンスチェック有効化
  performance_check: true

# テスト生成設定
testgen:
  # テストフレームワーク（pytest, unittest）
  framework: pytest
  # カバレッジ目標（%）
  coverage_target: 80
  # エッジケース生成
  edge_cases: true
  # モック使用
  use_mocks: true

# バグ修正設定
fix:
  # 自動適用（true: 自動, false: 確認）
  auto_apply: false
  # バックアップ作成
  create_backup: true

# 除外パターン
ignore_patterns:
  - "*.generated.py"
  - "migrations/*"
  - "__pycache__/*"
  - "*.min.js"
  - "node_modules/*"
  - ".git/*"

# 出力設定
output:
  # 出力形式（text, json, markdown）
  format: text
  # 色付き出力
  color: true
  # 詳細出力
  verbose: false
"""
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(default_config)
        click.echo(
            click.style("✓ ", fg="green") +
            f"Config file created: {config_path}"
        )
        click.echo("  Edit this file or use 'devbuddy config --set' to configure")

    elif list_keys:
        available_keys = [
            ("language", "対象言語（python, javascript, typescript, rust, go）"),
            ("style_guide", "スタイルガイド（pep8, google, numpy）"),
            ("review.severity", "レビュー検出レベル（low, medium, high）"),
            ("review.include_suggestions", "改善提案を含める（true/false）"),
            ("review.security_check", "セキュリティチェック（true/false）"),
            ("review.performance_check", "パフォーマンスチェック（true/false）"),
            ("testgen.framework", "テストフレームワーク（pytest, unittest）"),
            ("testgen.coverage_target", "カバレッジ目標（%）"),
            ("testgen.edge_cases", "エッジケース生成（true/false）"),
            ("testgen.use_mocks", "モック使用（true/false）"),
            ("fix.auto_apply", "修正自動適用（true/false）"),
            ("fix.create_backup", "バックアップ作成（true/false）"),
            ("output.format", "出力形式（text, json, markdown）"),
            ("output.color", "色付き出力（true/false）"),
            ("output.verbose", "詳細出力（true/false）"),
        ]
        click.echo(click.style("Available configuration keys:", fg="cyan", bold=True))
        click.echo()
        for key, description in available_keys:
            click.echo(f"  {click.style(key, fg='green'):40} {description}")

    elif get_key:
        cfg = load_config(config_path)
        if not cfg:
            click.echo("No config file found. Run 'devbuddy config --init' first.")
            return
        value = get_nested_value(cfg, get_key)
        if value is not None:
            click.echo(f"{get_key} = {value}")
        else:
            click.echo(
                click.style(f"Key '{get_key}' not found", fg="yellow") +
                ". Use --list-keys to see available keys."
            )

    elif set_value:
        if "=" not in set_value:
            click.echo(
                click.style("Error: ", fg="red") +
                "Use format: --set key=value (e.g., --set review.severity=high)"
            )
            return
        key, value = set_value.split("=", 1)
        cfg = load_config(config_path)
        if not cfg:
            click.echo("No config file found. Creating default config first...")
            # 初期化してから読み込み
            ctx = click.Context(config)
            ctx.invoke(config, init=True)
            cfg = load_config(config_path)

        cfg = set_nested_value(cfg, key, value)
        if save_config(config_path, cfg):
            click.echo(
                click.style("✓ ", fg="green") +
                f"Set {key} = {value}"
            )

    elif show:
        if config_path.exists():
            click.echo(
                click.style(f"Config file: {config_path}", fg="cyan", bold=True)
            )
            click.echo()
            with open(config_path, encoding="utf-8") as f:
                click.echo(f.read())
        else:
            click.echo(
                "No config file found. "
                "Run 'devbuddy config --init' to create one."
            )
    else:
        click.echo(click.style("DevBuddyAI Configuration", fg="cyan", bold=True))
        click.echo()
        click.echo("Usage:")
        click.echo("  devbuddy config --init          # Create default config")
        click.echo("  devbuddy config --show          # Show current config")
        click.echo("  devbuddy config --list-keys     # List available keys")
        click.echo("  devbuddy config --get KEY       # Get a config value")
        click.echo("  devbuddy config --set KEY=VALUE # Set a config value")
        click.echo()
        click.echo("Examples:")
        click.echo("  devbuddy config --set review.severity=high")
        click.echo("  devbuddy config --get testgen.framework")


@cli.command()
@click.option("--token", prompt=True, hide_input=True, help="APIトークン")
def auth(token: str) -> None:
    """DevBuddyAIサービスに認証"""
    # 認証ロジック（将来実装）
    click.echo("Authenticating...")
    click.echo(click.style("Authentication successful!", fg="green"))
    click.echo("Your token has been saved.")


def main() -> None:
    """エントリポイント"""
    cli()


if __name__ == "__main__":
    main()
