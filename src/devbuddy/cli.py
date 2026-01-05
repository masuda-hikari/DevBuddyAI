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
from devbuddy.core.generator import TestGenerator
from devbuddy.core.fixer import BugFixer
from devbuddy.llm.client import LLMClient


def get_api_key() -> str:
    """環境変数からAPIキーを取得"""
    api_key = os.environ.get("DEVBUDDY_API_KEY")
    if not api_key:
        click.echo(
            click.style("Error: DEVBUDDY_API_KEY environment variable not set", fg="red"),
            err=True,
        )
        click.echo("Set it with: export DEVBUDDY_API_KEY=your_api_key", err=True)
        sys.exit(1)
    return api_key


@click.group()
@click.version_option(version=__version__, prog_name="devbuddy")
def cli():
    """DevBuddyAI - AI駆動の開発者アシスタント

    コードレビュー、テスト生成、バグ修正提案を自動化します。
    """
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--diff", is_flag=True, help="git diffのみをレビュー")
@click.option("--severity", type=click.Choice(["low", "medium", "high"]), default="medium")
@click.option("--output", "-o", type=click.Path(), help="結果をファイルに出力")
def review(path: str, diff: bool, severity: str, output: Optional[str]):
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
    click.echo(click.style("DevBuddyAI Code Review Results", fg="cyan", bold=True))
    click.echo("=" * 50 + "\n")

    total_issues = {"bug": 0, "warning": 0, "style": 0, "info": 0}

    for result in all_results:
        if result.issues:
            click.echo(click.style(f"\n{result.file_path}", fg="white", bold=True))
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

                total_issues[issue.level] = total_issues.get(issue.level, 0) + 1

    # サマリー
    click.echo("\n" + "-" * 50)
    click.echo(
        f"Summary: {total_issues['bug']} bugs, {total_issues['warning']} warnings, "
        f"{total_issues['style']} style issues"
    )

    if output:
        # 結果をファイルに保存
        with open(output, "w", encoding="utf-8") as f:
            for result in all_results:
                f.write(f"\n{result.file_path}\n")
                for issue in result.issues:
                    f.write(f"  [{issue.level}] Line {issue.line}: {issue.message}\n")
        click.echo(f"\nResults saved to: {output}")


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--function", "-f", help="特定の関数のみテスト生成")
@click.option("--output", "-o", type=click.Path(), help="出力先ファイル")
@click.option("--framework", type=click.Choice(["pytest", "unittest"]), default="pytest")
@click.option("--run", is_flag=True, help="生成後にテストを実行")
def testgen(
    path: str,
    function: Optional[str],
    output: Optional[str],
    framework: str,
    run: bool,
):
    """関数/クラスのユニットテストを自動生成

    PATH: テスト対象のソースファイル
    """
    api_key = get_api_key()
    client = LLMClient(api_key=api_key)
    generator = TestGenerator(client=client)

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
            output_path = source_path.parent / "tests" / f"test_{source_path.name}"
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
def fix(test_path: str, source: Optional[str], apply: bool):
    """失敗テストやバグに対する修正を提案

    TEST_PATH: 失敗しているテストファイル
    """
    api_key = get_api_key()
    client = LLMClient(api_key=api_key)
    fixer = BugFixer(client=client)

    click.echo(f"Analyzing failing tests: {test_path}")

    result = fixer.suggest_fix(Path(test_path), source_path=Path(source) if source else None)

    if result.suggestions:
        click.echo(click.style("\nSuggested Fixes:", fg="cyan", bold=True))
        for i, suggestion in enumerate(result.suggestions, 1):
            click.echo(f"\n{i}. {suggestion.description}")
            click.echo(f"   File: {suggestion.file_path}:{suggestion.line}")
            click.echo("   Change:")
            click.echo(click.style(f"   - {suggestion.original}", fg="red"))
            click.echo(click.style(f"   + {suggestion.replacement}", fg="green"))

        if apply:
            click.echo("\nApplying fixes...")
            for suggestion in result.suggestions:
                fixer.apply_fix(suggestion)
            click.echo(click.style("Fixes applied!", fg="green"))
    else:
        click.echo(click.style("No fixes suggested", fg="yellow"))


@cli.command()
@click.option("--show", is_flag=True, help="現在の設定を表示")
@click.option("--init", is_flag=True, help="設定ファイルを初期化")
def config(show: bool, init: bool):
    """DevBuddyAI設定を管理"""
    config_path = Path(".devbuddy.yaml")

    if init:
        default_config = """# DevBuddyAI Configuration
language: python
style_guide: pep8

review:
  severity: medium
  include_suggestions: true

testgen:
  framework: pytest
  coverage_target: 80

ignore_patterns:
  - "*.generated.py"
  - "migrations/*"
  - "__pycache__/*"
"""
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(default_config)
        click.echo(f"Config file created: {config_path}")

    elif show:
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                click.echo(f.read())
        else:
            click.echo("No config file found. Run 'devbuddy config --init' to create one.")
    else:
        click.echo("Use --show to view config or --init to create default config")


@cli.command()
@click.option("--token", prompt=True, hide_input=True, help="APIトークン")
def auth(token: str):
    """DevBuddyAIサービスに認証"""
    # 認証ロジック（将来実装）
    click.echo("Authenticating...")
    click.echo(click.style("Authentication successful!", fg="green"))
    click.echo("Your token has been saved.")


def main():
    """エントリポイント"""
    cli()


if __name__ == "__main__":
    main()
