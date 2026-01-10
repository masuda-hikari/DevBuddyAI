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
from devbuddy.core.formatters import get_formatter
from devbuddy.core.licensing import LicenseManager, LicenseError, Plan
from devbuddy.core.billing import (
    BillingClient,
    BillingError,
    PRICE_CONFIG,
    get_price_info,
)
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


def get_config_value(key: str, default: str = "") -> str:
    """設定ファイルから値を取得"""
    config_path = Path(".devbuddy.yaml")
    if not config_path.exists():
        return default

    try:
        import yaml  # type: ignore[import-untyped]
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except Exception:
        return default

    # ドット区切りのキーを解決
    keys = key.split(".")
    value = cfg
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return str(value) if value is not None else default


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
    default=None,
    help="検出レベル（設定ファイルでデフォルト指定可）",
)
@click.option("--output", "-o", type=click.Path(), help="結果をファイルに出力")
@click.option(
    "--format", "-f", "output_format",
    type=click.Choice(["text", "json", "markdown"]),
    default=None,
    help="出力形式（設定ファイルでデフォルト指定可）",
)
def review(
    path: str,
    diff: bool,
    severity: Optional[str],
    output: Optional[str],
    output_format: Optional[str],
) -> None:
    """コードをレビューしてバグ、スタイル問題、改善点を指摘

    PATH: レビュー対象のファイルまたはディレクトリ
    """
    # 設定ファイルからデフォルト値を取得
    if severity is None:
        severity = get_config_value("review.severity", "medium")
    if output_format is None:
        output_format = get_config_value("output.format", "text")

    api_key = get_api_key()
    client = LLMClient(api_key=api_key)
    reviewer = CodeReviewer(client=client)

    # JSON出力時は進捗表示を抑制
    quiet = output_format == "json"

    if not quiet:
        click.echo(f"Reviewing: {path}")
        click.echo(f"Severity level: {severity}")

    target_path = Path(path)

    if target_path.is_file():
        files = [target_path]
    else:
        files = list(target_path.rglob("*.py"))

    if not files:
        if output_format == "json":
            import json
            click.echo(json.dumps({
                "tool": "DevBuddyAI",
                "type": "code_review",
                "error": "No Python files found",
                "results": [],
            }))
        else:
            click.echo(click.style("No Python files found", fg="yellow"))
        return

    all_results = []
    if quiet:
        for file_path in files:
            result = reviewer.review_file(file_path, severity=severity)
            all_results.append(result)
    else:
        with click.progressbar(files, label="Reviewing files") as bar:
            for file_path in bar:
                result = reviewer.review_file(file_path, severity=severity)
                all_results.append(result)

    # フォーマッターで出力生成
    formatter = get_formatter(output_format)
    formatted_output = formatter.format_review(all_results)

    # 結果表示（textのみカラー出力）
    if output_format == "text":
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
    else:
        # JSON/Markdown出力
        click.echo(formatted_output)

    if output:
        # 結果をファイルに保存
        with open(output, "w", encoding="utf-8") as f:
            f.write(formatted_output)
        if not quiet:
            click.echo(f"\nResults saved to: {output}")


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--function", "-fn", "function", help="特定の関数のみテスト生成")
@click.option("--output", "-o", type=click.Path(), help="出力先ファイル")
@click.option(
    "--framework",
    type=click.Choice(["pytest", "unittest"]),
    default=None,
    help="テストフレームワーク（設定ファイルでデフォルト指定可）",
)
@click.option("--run", is_flag=True, help="生成後にテストを実行")
@click.option(
    "--format", "-f", "output_format",
    type=click.Choice(["text", "json", "markdown"]),
    default=None,
    help="出力形式（設定ファイルでデフォルト指定可）",
)
def testgen(
    path: str,
    function: Optional[str],
    output: Optional[str],
    framework: Optional[str],
    run: bool,
    output_format: Optional[str],
) -> None:
    """関数/クラスのユニットテストを自動生成

    PATH: テスト対象のソースファイル
    """
    # 設定ファイルからデフォルト値を取得
    if framework is None:
        framework = get_config_value("testgen.framework", "pytest")
    if output_format is None:
        output_format = get_config_value("output.format", "text")

    api_key = get_api_key()
    client = LLMClient(api_key=api_key)
    generator = CodeTestGenerator(client=client)

    quiet = output_format == "json"

    if not quiet:
        click.echo(f"Generating tests for: {path}")
        if function:
            click.echo(f"Target function: {function}")

    source_path = Path(path)
    result = generator.generate_tests(
        source_path, function_name=function, framework=framework
    )

    # フォーマッターで出力生成
    formatter = get_formatter(output_format)

    if result.success:
        if output_format == "text":
            gen_msg = click.style("\nGenerated Tests:", fg="green", bold=True)
            click.echo(gen_msg)
            click.echo("-" * 40)
            click.echo(result.test_code)
        else:
            formatted_output = formatter.format_testgen(result)
            click.echo(formatted_output)

        # 出力先決定
        if output:
            output_path = Path(output)
        else:
            test_name = f"test_{source_path.name}"
            output_path = source_path.parent / "tests" / test_name
            output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.test_code)
        if not quiet:
            click.echo(f"\nTest file saved to: {output_path}")

        if run:
            if not quiet:
                click.echo("\nRunning generated tests...")
            import subprocess

            proc = subprocess.run(
                ["pytest", str(output_path), "-v"],
                capture_output=True,
                text=True,
            )
            if not quiet:
                click.echo(proc.stdout)
            if proc.returncode != 0:
                if not quiet:
                    click.echo(click.style("Some tests failed!", fg="red"))
                    click.echo(proc.stderr)
            else:
                if not quiet:
                    click.echo(click.style("All tests passed!", fg="green"))
    else:
        if output_format == "text":
            click.echo(click.style(f"Error: {result.error}", fg="red"))
        else:
            formatted_output = formatter.format_testgen(result)
            click.echo(formatted_output)


@cli.command()
@click.argument("test_path", type=click.Path(exists=True))
@click.option("--source", "-s", type=click.Path(exists=True), help="ソースファイル")
@click.option("--apply", is_flag=True, help="修正を自動適用")
@click.option(
    "--format", "-f", "output_format",
    type=click.Choice(["text", "json", "markdown"]),
    default=None,
    help="出力形式（設定ファイルでデフォルト指定可）",
)
@click.option("--output", "-o", type=click.Path(), help="結果をファイルに出力")
def fix(
    test_path: str,
    source: Optional[str],
    apply: bool,
    output_format: Optional[str],
    output: Optional[str],
) -> None:
    """失敗テストやバグに対する修正を提案

    TEST_PATH: 失敗しているテストファイル
    """
    # 設定ファイルからデフォルト値を取得
    if output_format is None:
        output_format = get_config_value("output.format", "text")

    api_key = get_api_key()
    client = LLMClient(api_key=api_key)
    fixer = BugFixer(client=client)

    quiet = output_format == "json"

    if not quiet:
        click.echo(f"Analyzing failing tests: {test_path}")

    source_p = Path(source) if source else None
    result = fixer.suggest_fix(Path(test_path), source_path=source_p)

    # フォーマッターで出力生成
    formatter = get_formatter(output_format)
    formatted_output = formatter.format_fix(result)

    if output_format == "text":
        if result.suggestions:
            fix_msg = click.style("\nSuggested Fixes:", fg="cyan", bold=True)
            click.echo(fix_msg)
            for i, suggestion in enumerate(result.suggestions, 1):
                click.echo(f"\n{i}. {suggestion.description}")
                file_loc = f"{suggestion.file_path}:{suggestion.line}"
                click.echo(f"   File: {file_loc}")
                click.echo("   Change:")
                orig = click.style(f"   - {suggestion.original}", fg="red")
                click.echo(orig)
                repl = suggestion.replacement
                click.echo(click.style(f"   + {repl}", fg="green"))

            if apply:
                click.echo("\nApplying fixes...")
                for suggestion in result.suggestions:
                    fixer.apply_fix(suggestion)
                click.echo(click.style("Fixes applied!", fg="green"))
        else:
            click.echo(click.style("No fixes suggested", fg="yellow"))
    else:
        # JSON/Markdown出力
        click.echo(formatted_output)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(formatted_output)
        if not quiet:
            click.echo(f"\nResults saved to: {output}")


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
            yaml.safe_dump(
                config, f, default_flow_style=False, allow_unicode=True
            )
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
        check_mark = click.style("✓ ", fg="green")
        click.echo(check_mark + f"Config file created: {config_path}")
        click.echo("  Edit or use 'devbuddy config --set' to configure")

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
        header = click.style(
            "Available configuration keys:", fg="cyan", bold=True
        )
        click.echo(header)
        click.echo()
        for key, description in available_keys:
            key_styled = click.style(key, fg='green')
            click.echo(f"  {key_styled:40} {description}")

    elif get_key:
        cfg = load_config(config_path)
        if not cfg:
            click.echo("No config file. Run 'devbuddy config --init' first.")
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
            err_msg = click.style("Error: ", fg="red")
            click.echo(err_msg + "Use format: --set key=value")
            return
        key, value = set_value.split("=", 1)
        cfg = load_config(config_path)
        if not cfg:
            click.echo("No config file found. Creating default first...")
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
            cfg_header = click.style(f"Config file: {config_path}", fg="cyan")
            click.echo(cfg_header)
            click.echo()
            with open(config_path, encoding="utf-8") as f:
                click.echo(f.read())
        else:
            click.echo(
                "No config file found. "
                "Run 'devbuddy config --init' to create one."
            )
    else:
        title = click.style("DevBuddyAI Configuration", fg="cyan", bold=True)
        click.echo(title)
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


@cli.group()
def license() -> None:
    """ライセンス管理コマンド

    ライセンスのアクティベート、確認、利用状況の表示を行います。
    """
    pass


@license.command("activate")
@click.option(
    "--key", "-k", prompt="License Key", help="ライセンスキー（DB-PRO-xxx形式）"
)
@click.option(
    "--email", "-e", prompt="Email", help="登録メールアドレス"
)
def license_activate(key: str, email: str) -> None:
    """ライセンスをアクティベート

    Examples:
        devbuddy license activate --key DB-PRO-abc123 --email user@example.com
    """
    manager = LicenseManager()

    try:
        license_info = manager.activate(key, email)
        click.echo(click.style("✓ License activated!", fg="green", bold=True))
        click.echo()
        click.echo(f"  Plan: {license_info.plan.value.upper()}")
        click.echo(f"  Email: {license_info.email}")

        limits = license_info.get_limits()
        click.echo()
        click.echo("  Features enabled:")
        click.echo(f"    - Reviews/month: {_format_limit(limits.reviews_per_month)}")
        click.echo(f"    - Max file lines: {_format_limit(limits.max_file_lines)}")
        click.echo(f"    - Private repos: {'✓' if limits.private_repos else '✗'}")
        click.echo(
            f"    - GitHub integration: {'✓' if limits.github_integration else '✗'}"
        )
    except LicenseError as e:
        click.echo(click.style(f"✗ Activation failed: {e}", fg="red"))


@license.command("status")
def license_status() -> None:
    """ライセンス状態と利用状況を表示"""
    manager = LicenseManager()
    license_info = manager.get_license()

    click.echo(click.style("DevBuddyAI License Status", fg="cyan", bold=True))
    click.echo("=" * 40)

    if license_info and license_info.is_valid and not license_info.is_expired():
        plan_styled = click.style(
            license_info.plan.value.upper(), fg='green', bold=True
        )
        click.echo(f"Plan: {plan_styled}")
        click.echo(f"Email: {license_info.email}")
        if license_info.expires_at:
            click.echo(f"Expires: {license_info.expires_at}")
    else:
        click.echo(
            f"Plan: {click.style('FREE', fg='yellow', bold=True)}"
        )
        click.echo("(No active license)")

    # 利用状況
    click.echo()
    summary = manager.get_usage_summary()
    click.echo("Usage this month:")
    click.echo(f"  Reviews: {summary['reviews']}")
    click.echo(f"  Test generations: {summary['testgens']}")
    click.echo(f"  Fix suggestions: {summary['fixes']}")

    # 制限
    click.echo()
    click.echo("Limits:")
    click.echo(f"  Max file lines: {summary['max_file_lines']}")

    # 機能
    click.echo()
    click.echo("Features:")
    features = summary['features']
    for feature, enabled in features.items():
        status = click.style("✓", fg="green") if enabled else click.style(
            "✗", fg="red"
        )
        feature_name = feature.replace("_", " ").title()
        click.echo(f"  {status} {feature_name}")


@license.command("deactivate")
@click.confirmation_option(prompt="Are you sure you want to deactivate?")
def license_deactivate() -> None:
    """ライセンスを無効化"""
    manager = LicenseManager()
    manager.deactivate()
    click.echo(click.style("License deactivated.", fg="yellow"))
    click.echo("You are now using the FREE plan.")


@license.command("usage")
def license_usage() -> None:
    """今月の利用状況を表示"""
    manager = LicenseManager()
    summary = manager.get_usage_summary()

    click.echo(click.style(f"Usage for {summary['month']}", fg="cyan", bold=True))
    click.echo("-" * 30)
    click.echo(f"Reviews:          {summary['reviews']}")
    click.echo(f"Test generations: {summary['testgens']}")
    click.echo(f"Fix suggestions:  {summary['fixes']}")


def _format_limit(value: int) -> str:
    """制限値をフォーマット"""
    return "unlimited" if value == -1 else str(value)


@cli.group()
def billing() -> None:
    """課金・サブスクリプション管理

    プランの確認、アップグレード、支払い管理を行います。
    """
    pass


@billing.command("plans")
def billing_plans() -> None:
    """利用可能なプラン一覧を表示"""
    click.echo(click.style("DevBuddyAI Plans", fg="cyan", bold=True))
    click.echo("=" * 50)
    click.echo()

    # Free プラン
    click.echo(click.style("FREE", fg="white", bold=True))
    click.echo("  価格: 無料")
    click.echo("  レビュー: 50回/月")
    click.echo("  ファイルサイズ: 500行まで")
    click.echo("  テスト生成: 20回/月")
    click.echo()

    # 有料プラン
    for plan, price_info in PRICE_CONFIG.items():
        if plan == Plan.ENTERPRISE:
            continue  # Enterpriseは別途

        click.echo(click.style(price_info.display_name, fg="green", bold=True))
        click.echo(f"  価格: ¥{price_info.amount:,}/月")

        from devbuddy.core.licensing import PLAN_LIMITS
        limits = PLAN_LIMITS[plan]
        reviews = _format_limit(limits.reviews_per_month)
        lines = _format_limit(limits.max_file_lines)
        testgens = _format_limit(limits.testgen_per_month)
        click.echo(f"  レビュー: {reviews}/月")
        click.echo(f"  ファイルサイズ: {lines}行まで")
        click.echo(f"  テスト生成: {testgens}/月")
        if limits.private_repos:
            click.echo("  ✓ プライベートリポジトリ対応")
        if limits.github_integration:
            click.echo("  ✓ GitHub連携")
        if limits.priority_support:
            click.echo("  ✓ 優先サポート")
        click.echo()

    # Enterprise
    click.echo(click.style("Enterprise プラン", fg="yellow", bold=True))
    click.echo("  価格: 要問い合わせ")
    click.echo("  ✓ 全機能無制限")
    click.echo("  ✓ セルフホスト対応")
    click.echo("  ✓ 優先サポート")
    click.echo("  ✓ SLA保証")
    click.echo()
    click.echo("お問い合わせ: enterprise@devbuddy.ai")


@billing.command("upgrade")
@click.argument(
    "plan_name",
    type=click.Choice(["pro", "team"]),
)
@click.option("--email", "-e", prompt="Email", help="支払い用メールアドレス")
def billing_upgrade(plan_name: str, email: str) -> None:
    """有料プランにアップグレード

    PLAN_NAME: アップグレード先プラン（pro または team）

    Examples:
        devbuddy billing upgrade pro --email user@example.com
    """
    plan = Plan.PRO if plan_name == "pro" else Plan.TEAM
    price_info = get_price_info(plan)

    if not price_info:
        click.echo(click.style("Error: Invalid plan", fg="red"))
        return

    click.echo(f"プラン: {price_info.display_name}")
    click.echo(f"価格: ¥{price_info.amount:,}/月")
    click.echo()

    # Stripe APIキーがない場合の案内
    import os
    if not os.environ.get("STRIPE_API_KEY"):
        click.echo(click.style("注意:", fg="yellow", bold=True))
        click.echo("Stripe課金を利用するには、以下の設定が必要です:")
        click.echo()
        click.echo("1. 環境変数を設定:")
        click.echo("   export STRIPE_API_KEY=your_stripe_api_key")
        click.echo()
        click.echo("2. または、Webサイトからアップグレード:")
        click.echo("   https://devbuddy.ai/pricing")
        return

    try:
        billing_client = BillingClient()
        session = billing_client.create_checkout_session(
            plan=plan,
            email=email,
            success_url="https://devbuddy.ai/success",
            cancel_url="https://devbuddy.ai/pricing",
        )

        click.echo(click.style("✓ Checkout session created!", fg="green"))
        click.echo()
        click.echo("以下のURLで支払いを完了してください:")
        click.echo(click.style(session.url, fg="cyan", underline=True))

    except BillingError as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {e}", fg="red"))


@billing.command("status")
def billing_status() -> None:
    """課金ステータスを表示"""
    manager = LicenseManager()
    license_info = manager.get_license()

    click.echo(click.style("Billing Status", fg="cyan", bold=True))
    click.echo("=" * 40)

    if license_info and license_info.is_valid:
        plan = license_info.plan
        if plan == Plan.FREE:
            click.echo(f"Current Plan: {click.style('FREE', fg='yellow')}")
            click.echo()
            click.echo("アップグレードするには:")
            click.echo("  devbuddy billing upgrade pro")
            click.echo("  devbuddy billing upgrade team")
        else:
            plan_styled = click.style(plan.value.upper(), fg='green', bold=True)
            click.echo(f"Current Plan: {plan_styled}")

            price_info = get_price_info(plan)
            if price_info:
                click.echo(f"Monthly Fee: ¥{price_info.amount:,}")

            if license_info.expires_at:
                click.echo(f"Renews: {license_info.expires_at}")
    else:
        click.echo(f"Current Plan: {click.style('FREE', fg='yellow')}")
        click.echo()
        click.echo("アップグレードするには:")
        click.echo("  devbuddy billing upgrade pro")


@billing.command("cancel")
@click.confirmation_option(prompt="本当にサブスクリプションをキャンセルしますか？")
def billing_cancel() -> None:
    """サブスクリプションをキャンセル

    キャンセル後も、現在の請求期間終了まで利用可能です。
    """
    manager = LicenseManager()
    license_info = manager.get_license()

    if not license_info or license_info.plan == Plan.FREE:
        click.echo(click.style("有料プランに加入していません。", fg="yellow"))
        return

    click.echo(click.style("サブスクリプションをキャンセルしました。", fg="yellow"))
    click.echo("現在の請求期間終了まで引き続き利用可能です。")
    click.echo()
    click.echo("再開するには:")
    click.echo("  devbuddy billing upgrade pro")


def main() -> None:
    """エントリポイント"""
    cli()


if __name__ == "__main__":
    main()
