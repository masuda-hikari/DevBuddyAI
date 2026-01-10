"""
CLIのテスト
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from devbuddy.cli import cli


class TestCLI:
    """CLIテストクラス"""

    @pytest.fixture
    def runner(self):
        """CLIランナー"""
        return CliRunner()

    def test_cli_version(self, runner):
        """バージョン表示"""
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "devbuddy" in result.output

    def test_cli_help(self, runner):
        """ヘルプ表示"""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "review" in result.output
        assert "testgen" in result.output
        assert "fix" in result.output

    def test_review_command_help(self, runner):
        """reviewコマンドヘルプ"""
        result = runner.invoke(cli, ["review", "--help"])

        assert result.exit_code == 0
        assert "--severity" in result.output
        assert "--diff" in result.output

    def test_testgen_command_help(self, runner):
        """testgenコマンドヘルプ"""
        result = runner.invoke(cli, ["testgen", "--help"])

        assert result.exit_code == 0
        assert "--function" in result.output
        assert "--framework" in result.output

    def test_config_init(self, runner, tmp_path):
        """設定ファイル初期化"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "--init"])

            assert result.exit_code == 0
            assert "created" in result.output

    def test_config_show_no_file(self, runner, tmp_path):
        """設定ファイルなしで表示"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "--show"])

            assert result.exit_code == 0
            assert "No config file found" in result.output

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": ""})
    def test_review_no_api_key(self, runner, tmp_path):
        """APIキーなしでreview"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # テスト用ファイル作成
            with open("test.py", "w") as f:
                f.write("x = 1")

            result = runner.invoke(cli, ["review", "test.py"])

            assert result.exit_code == 1
            assert "DEVBUDDY_API_KEY" in result.output

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.CodeReviewer")
    def test_review_with_mock(self, mock_reviewer_class, runner, tmp_path):
        """モックを使ったreviewテスト"""
        # モックセットアップ
        mock_reviewer = MagicMock()
        mock_reviewer.review_file.return_value = MagicMock(
            issues=[],
            file_path=tmp_path / "test.py",
            success=True,
        )
        mock_reviewer_class.return_value = mock_reviewer

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("test.py", "w") as f:
                f.write("x = 1")

            result = runner.invoke(cli, ["review", "test.py"])

            assert result.exit_code == 0

    def test_fix_command_help(self, runner):
        """fixコマンドヘルプ"""
        result = runner.invoke(cli, ["fix", "--help"])

        assert result.exit_code == 0
        assert "--source" in result.output
        assert "--apply" in result.output

    def test_auth_command(self, runner):
        """authコマンド"""
        result = runner.invoke(cli, ["auth"], input="test-token\n")

        assert result.exit_code == 0
        assert "successful" in result.output

    def test_config_show_with_file(self, runner, tmp_path):
        """設定ファイルありで表示"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # 設定ファイルを作成
            with open(".devbuddy.yaml", "w") as f:
                f.write("language: python\n")

            result = runner.invoke(cli, ["config", "--show"])

            assert result.exit_code == 0
            assert "language: python" in result.output

    def test_config_no_options(self, runner, tmp_path):
        """オプションなしでconfig"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config"])

            assert result.exit_code == 0
            assert "--show" in result.output or "--init" in result.output

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.CodeReviewer")
    def test_review_directory(self, mock_reviewer_class, runner, tmp_path):
        """ディレクトリをreview"""
        mock_reviewer = MagicMock()
        mock_reviewer.review_file.return_value = MagicMock(
            issues=[],
            file_path=tmp_path / "test.py",
            success=True,
        )
        mock_reviewer_class.return_value = mock_reviewer

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # 複数ファイル作成
            with open("file1.py", "w") as f:
                f.write("x = 1")
            with open("file2.py", "w") as f:
                f.write("y = 2")

            result = runner.invoke(cli, ["review", "."])

            assert result.exit_code == 0

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.CodeReviewer")
    def test_review_no_python_files(self, mock_reviewer_class, runner, tmp_path):
        """Pythonファイルなしでreview"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Python以外のファイル
            with open("readme.txt", "w") as f:
                f.write("text")

            result = runner.invoke(cli, ["review", "."])

            assert result.exit_code == 0
            assert "No Python files" in result.output

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.CodeReviewer")
    def test_review_with_issues(self, mock_reviewer_class, runner, tmp_path):
        """問題ありのreview結果"""
        mock_issue = MagicMock()
        mock_issue.level = "bug"
        mock_issue.line = 10
        mock_issue.message = "Potential bug"
        mock_issue.suggestion = "Fix it"

        mock_reviewer = MagicMock()
        mock_reviewer.review_file.return_value = MagicMock(
            issues=[mock_issue],
            file_path=tmp_path / "test.py",
            success=True,
        )
        mock_reviewer_class.return_value = mock_reviewer

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("test.py", "w") as f:
                f.write("x = 1")

            result = runner.invoke(cli, ["review", "test.py"])

            assert result.exit_code == 0
            assert "BUG" in result.output

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.CodeReviewer")
    def test_review_with_output_file(self, mock_reviewer_class, runner, tmp_path):
        """結果をファイルに出力"""
        mock_issue = MagicMock()
        mock_issue.level = "warning"
        mock_issue.line = 5
        mock_issue.message = "Warning message"
        mock_issue.suggestion = None

        mock_reviewer = MagicMock()
        mock_reviewer.review_file.return_value = MagicMock(
            issues=[mock_issue],
            file_path="test.py",
            success=True,
        )
        mock_reviewer_class.return_value = mock_reviewer

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("test.py", "w") as f:
                f.write("x = 1")

            result = runner.invoke(
                cli, ["review", "test.py", "-o", "output.txt"]
            )

            assert result.exit_code == 0
            assert "saved to" in result.output

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": ""})
    def test_testgen_no_api_key(self, runner, tmp_path):
        """APIキーなしでtestgen"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("test.py", "w") as f:
                f.write("def foo(): pass")

            result = runner.invoke(cli, ["testgen", "test.py"])

            assert result.exit_code == 1
            assert "DEVBUDDY_API_KEY" in result.output

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.CodeTestGenerator")
    def test_testgen_success(self, mock_gen_class, runner, tmp_path):
        """テスト生成成功"""
        mock_gen = MagicMock()
        mock_gen.generate_tests.return_value = MagicMock(
            success=True,
            test_code="def test_foo(): pass",
            error=None,
        )
        mock_gen_class.return_value = mock_gen

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("calculator.py", "w") as f:
                f.write("def add(a, b): return a + b")

            result = runner.invoke(cli, ["testgen", "calculator.py"])

            assert result.exit_code == 0
            assert "Generated Tests" in result.output

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.CodeTestGenerator")
    def test_testgen_with_output(self, mock_gen_class, runner, tmp_path):
        """出力ファイル指定でtestgen"""
        mock_gen = MagicMock()
        mock_gen.generate_tests.return_value = MagicMock(
            success=True,
            test_code="def test_foo(): pass",
            error=None,
        )
        mock_gen_class.return_value = mock_gen

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("calc.py", "w") as f:
                f.write("def add(a, b): return a + b")

            result = runner.invoke(
                cli, ["testgen", "calc.py", "-o", "my_tests.py"]
            )

            assert result.exit_code == 0
            assert "my_tests.py" in result.output

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.CodeTestGenerator")
    def test_testgen_failure(self, mock_gen_class, runner, tmp_path):
        """テスト生成失敗"""
        mock_gen = MagicMock()
        mock_gen.generate_tests.return_value = MagicMock(
            success=False,
            test_code="",
            error="API error",
        )
        mock_gen_class.return_value = mock_gen

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("test.py", "w") as f:
                f.write("x = 1")

            result = runner.invoke(cli, ["testgen", "test.py"])

            assert result.exit_code == 0
            assert "API error" in result.output

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.CodeTestGenerator")
    def test_testgen_with_function(self, mock_gen_class, runner, tmp_path):
        """関数指定でtestgen"""
        mock_gen = MagicMock()
        mock_gen.generate_tests.return_value = MagicMock(
            success=True,
            test_code="def test_add(): pass",
            error=None,
        )
        mock_gen_class.return_value = mock_gen

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("calc.py", "w") as f:
                f.write("def add(a, b): return a + b")

            result = runner.invoke(
                cli, ["testgen", "calc.py", "-f", "add"]
            )

            assert result.exit_code == 0

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": ""})
    def test_fix_no_api_key(self, runner, tmp_path):
        """APIキーなしでfix"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("test.py", "w") as f:
                f.write("def test_foo(): assert False")

            result = runner.invoke(cli, ["fix", "test.py"])

            assert result.exit_code == 1
            assert "DEVBUDDY_API_KEY" in result.output

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.BugFixer")
    def test_fix_with_suggestions(self, mock_fixer_class, runner, tmp_path):
        """修正提案ありでfix"""
        mock_suggestion = MagicMock()
        mock_suggestion.description = "Fix the bug"
        mock_suggestion.file_path = "test.py"
        mock_suggestion.line = 5
        mock_suggestion.original = "old code"
        mock_suggestion.replacement = "new code"

        mock_fixer = MagicMock()
        mock_fixer.suggest_fix.return_value = MagicMock(
            suggestions=[mock_suggestion]
        )
        mock_fixer_class.return_value = mock_fixer

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("test.py", "w") as f:
                f.write("def test_foo(): assert False")

            result = runner.invoke(cli, ["fix", "test.py"])

            assert result.exit_code == 0
            assert "Suggested Fixes" in result.output

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.BugFixer")
    def test_fix_no_suggestions(self, mock_fixer_class, runner, tmp_path):
        """修正提案なしでfix"""
        mock_fixer = MagicMock()
        mock_fixer.suggest_fix.return_value = MagicMock(suggestions=[])
        mock_fixer_class.return_value = mock_fixer

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("test.py", "w") as f:
                f.write("def test_foo(): pass")

            result = runner.invoke(cli, ["fix", "test.py"])

            assert result.exit_code == 0
            assert "No fixes suggested" in result.output

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.BugFixer")
    def test_fix_with_apply(self, mock_fixer_class, runner, tmp_path):
        """--applyオプションでfix"""
        mock_suggestion = MagicMock()
        mock_suggestion.description = "Fix the bug"
        mock_suggestion.file_path = "test.py"
        mock_suggestion.line = 5
        mock_suggestion.original = "old"
        mock_suggestion.replacement = "new"

        mock_fixer = MagicMock()
        mock_fixer.suggest_fix.return_value = MagicMock(
            suggestions=[mock_suggestion]
        )
        mock_fixer_class.return_value = mock_fixer

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("test.py", "w") as f:
                f.write("def test_foo(): assert False")

            result = runner.invoke(cli, ["fix", "test.py", "--apply"])

            assert result.exit_code == 0
            assert "applied" in result.output

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.BugFixer")
    def test_fix_with_source_option(self, mock_fixer_class, runner, tmp_path):
        """--source オプションでfix"""
        mock_fixer = MagicMock()
        mock_fixer.suggest_fix.return_value = MagicMock(suggestions=[])
        mock_fixer_class.return_value = mock_fixer

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("test_file.py", "w") as f:
                f.write("def test_foo(): assert False")
            with open("source.py", "w") as f:
                f.write("def foo(): return 1")

            result = runner.invoke(
                cli, ["fix", "test_file.py", "-s", "source.py"]
            )

            assert result.exit_code == 0
