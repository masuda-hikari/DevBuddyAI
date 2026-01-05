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
