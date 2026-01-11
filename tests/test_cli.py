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
    def test_review_no_python_files(
        self, mock_reviewer_class, runner, tmp_path
    ):
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
    def test_review_with_output_file(
        self, mock_reviewer_class, runner, tmp_path
    ):
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
                cli, ["testgen", "calc.py", "-fn", "add"]
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

    def test_config_list_keys(self, runner, tmp_path):
        """--list-keysオプション"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "--list-keys"])

            assert result.exit_code == 0
            assert "language" in result.output
            assert "review.severity" in result.output
            assert "testgen.framework" in result.output

    def test_config_get_existing_key(self, runner, tmp_path):
        """存在するキーの取得"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # YAMLファイル作成
            with open(".devbuddy.yaml", "w") as f:
                f.write("language: python\nreview:\n  severity: high\n")

            result = runner.invoke(cli, ["config", "--get", "review.severity"])

            assert result.exit_code == 0
            assert "review.severity = high" in result.output

    def test_config_get_nonexistent_key(self, runner, tmp_path):
        """存在しないキーの取得"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open(".devbuddy.yaml", "w") as f:
                f.write("language: python\n")

            result = runner.invoke(cli, ["config", "--get", "nonexistent"])

            assert result.exit_code == 0
            assert "not found" in result.output

    def test_config_get_no_file(self, runner, tmp_path):
        """設定ファイルなしで--get"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "--get", "language"])

            assert result.exit_code == 0
            assert "No config file" in result.output

    def test_config_set_value(self, runner, tmp_path):
        """値の設定"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # 先に設定ファイルを作成
            runner.invoke(cli, ["config", "--init"])

            result = runner.invoke(
                cli, ["config", "--set", "review.severity=high"]
            )

            assert result.exit_code == 0
            assert "Set review.severity = high" in result.output

    def test_config_set_invalid_format(self, runner, tmp_path):
        """不正なフォーマットで--set"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "--set", "invalid"])

            assert result.exit_code == 0
            assert "key=value" in result.output

    def test_config_set_creates_file(self, runner, tmp_path):
        """設定ファイルがない場合に作成"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli, ["config", "--set", "language=rust"]
            )

            assert result.exit_code == 0

    def test_config_custom_path(self, runner, tmp_path):
        """カスタム設定ファイルパス"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli, ["config", "--init", "--path", "custom.yaml"]
            )

            assert result.exit_code == 0
            assert "custom.yaml" in result.output

    def test_config_init_content(self, runner, tmp_path):
        """初期化された設定ファイルの内容確認"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["config", "--init"])

            with open(".devbuddy.yaml", encoding="utf-8") as f:
                content = f.read()

            assert "language: python" in content
            assert "review:" in content
            assert "testgen:" in content
            assert "ignore_patterns:" in content


class TestLicenseCommands:
    """ライセンスコマンドのテスト"""

    @pytest.fixture
    def runner(self):
        """CLIランナー"""
        return CliRunner()

    def test_license_status(self, runner, tmp_path):
        """ライセンス状態表示"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["license", "status"])

            assert result.exit_code == 0
            assert "License Status" in result.output

    @patch("devbuddy.cli.LicenseManager")
    def test_license_status_with_active(
        self, mock_manager_class, runner, tmp_path
    ):
        """アクティブライセンスの状態表示"""
        from devbuddy.core.licensing import Plan

        mock_license = MagicMock()
        mock_license.plan = Plan.PRO
        mock_license.email = "test@example.com"
        mock_license.expires_at = None
        mock_license.is_valid = True
        mock_license.is_expired.return_value = False

        mock_manager = MagicMock()
        mock_manager.get_license.return_value = mock_license
        mock_manager.get_usage_summary.return_value = {
            "month": "2026-01",
            "reviews": 10,
            "testgens": 5,
            "fixes": 2,
            "max_file_lines": 2000,
            "features": {
                "private_repos": True,
                "github_integration": True,
                "priority_support": False,
            },
        }
        mock_manager_class.return_value = mock_manager

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["license", "status"])

            assert result.exit_code == 0
            assert "PRO" in result.output

    def test_license_usage(self, runner, tmp_path):
        """利用状況表示"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["license", "usage"])

            assert result.exit_code == 0
            assert "Usage" in result.output

    @patch("devbuddy.cli.LicenseManager")
    def test_license_activate_success(
        self, mock_manager_class, runner, tmp_path
    ):
        """ライセンスアクティベート成功"""
        from devbuddy.core.licensing import Plan

        mock_license = MagicMock()
        mock_license.plan = Plan.PRO
        mock_license.email = "test@example.com"
        mock_license.get_limits.return_value = MagicMock(
            reviews_per_month=500,
            max_file_lines=2000,
            private_repos=True,
            github_integration=True,
        )

        mock_manager = MagicMock()
        mock_manager.activate.return_value = mock_license
        mock_manager_class.return_value = mock_manager

        with runner.isolated_filesystem(temp_dir=tmp_path):
            key = "DB-PRO-test"
            result = runner.invoke(
                cli,
                ["license", "activate", "--key", key, "--email", "t@t.com"]
            )

            assert result.exit_code == 0
            assert "activated" in result.output

    @patch("devbuddy.cli.LicenseManager")
    def test_license_activate_failure(
        self, mock_manager_class, runner, tmp_path
    ):
        """ライセンスアクティベート失敗"""
        from devbuddy.core.licensing import LicenseError

        mock_manager = MagicMock()
        mock_manager.activate.side_effect = LicenseError("Invalid key")
        mock_manager_class.return_value = mock_manager

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli,
                ["license", "activate", "--key", "inv", "--email", "t@t.com"]
            )

            assert result.exit_code == 0
            assert "failed" in result.output

    @patch("devbuddy.cli.LicenseManager")
    def test_license_deactivate(self, mock_manager_class, runner, tmp_path):
        """ライセンス無効化"""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                cli, ["license", "deactivate"], input="y\n"
            )

            assert result.exit_code == 0
            assert "deactivated" in result.output


class TestBillingCommands:
    """課金コマンドのテスト"""

    @pytest.fixture
    def runner(self):
        """CLIランナー"""
        return CliRunner()

    def test_billing_plans(self, runner, tmp_path):
        """プラン一覧表示"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["billing", "plans"])

            assert result.exit_code == 0
            assert "FREE" in result.output
            assert "PRO" in result.output or "Pro" in result.output

    def test_billing_status_free(self, runner, tmp_path):
        """無料プランの課金状態"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["billing", "status"])

            assert result.exit_code == 0
            assert "Billing Status" in result.output

    @patch.dict("os.environ", {"STRIPE_API_KEY": ""})
    def test_billing_upgrade_no_stripe_key(self, runner, tmp_path):
        """Stripeキーなしでアップグレード"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            email = "test@example.com"
            result = runner.invoke(
                cli,
                ["billing", "upgrade", "pro", "--email", email]
            )

            assert result.exit_code == 0
            has_key = "STRIPE_API_KEY" in result.output
            has_stripe = "Stripe" in result.output
            assert has_key or has_stripe

    @patch("devbuddy.cli.LicenseManager")
    def test_billing_cancel_free_plan(
        self, mock_manager_class, runner, tmp_path
    ):
        """無料プランでキャンセル"""
        from devbuddy.core.licensing import Plan

        mock_license = MagicMock()
        mock_license.plan = Plan.FREE

        mock_manager = MagicMock()
        mock_manager.get_license.return_value = mock_license
        mock_manager_class.return_value = mock_manager

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["billing", "cancel"], input="y\n")

            assert result.exit_code == 0
            assert "有料プランに加入していません" in result.output


class TestServerCommands:
    """サーバーコマンドのテスト"""

    @pytest.fixture
    def runner(self):
        """CLIランナー"""
        return CliRunner()

    def test_server_info(self, runner, tmp_path):
        """サーバー情報表示"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["server", "info"])

            assert result.exit_code == 0
            assert "Server Configuration" in result.output

    @patch.dict("os.environ", {"STRIPE_API_KEY": "sk_test_123"})
    def test_server_info_with_key(self, runner, tmp_path):
        """Stripeキーありでサーバー情報表示"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["server", "info"])

            assert result.exit_code == 0
            assert "sk_test" in result.output


class TestReviewFormats:
    """レビュー出力形式のテスト"""

    @pytest.fixture
    def runner(self):
        """CLIランナー"""
        return CliRunner()

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.CodeReviewer")
    def test_review_json_format(
        self, mock_reviewer_class, runner, tmp_path
    ):
        """JSON形式でのレビュー出力"""
        from devbuddy.core.models import ReviewResult

        mock_reviewer = MagicMock()
        mock_result = ReviewResult(
            file_path=str(tmp_path / "test.py"),
            issues=[],
            success=True,
        )
        mock_reviewer.review_file.return_value = mock_result
        mock_reviewer_class.return_value = mock_reviewer

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("test.py", "w") as f:
                f.write("x = 1")

            result = runner.invoke(cli, ["review", "test.py", "-f", "json"])

            assert result.exit_code == 0

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.CodeReviewer")
    def test_review_markdown_format(
        self, mock_reviewer_class, runner, tmp_path
    ):
        """Markdown形式でのレビュー出力"""
        from devbuddy.core.models import ReviewResult

        mock_reviewer = MagicMock()
        fp = str(tmp_path / "test.py")
        mock_result = ReviewResult(file_path=fp, issues=[], success=True)
        mock_reviewer.review_file.return_value = mock_result
        mock_reviewer_class.return_value = mock_reviewer

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("test.py", "w") as f:
                f.write("x = 1")

            cmd = ["review", "test.py", "-f", "markdown"]
            result = runner.invoke(cli, cmd)

            assert result.exit_code == 0


class TestTestgenFormats:
    """テスト生成出力形式のテスト"""

    @pytest.fixture
    def runner(self):
        """CLIランナー"""
        return CliRunner()

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.CodeTestGenerator")
    def test_testgen_json_format(self, mock_gen_class, runner, tmp_path):
        """JSON形式でのテスト生成出力"""
        from devbuddy.core.generator import GenerationResult

        mock_gen = MagicMock()
        mock_result = GenerationResult(
            success=True,
            test_code="def test_foo(): pass",
            test_count=1,
        )
        mock_gen.generate_tests.return_value = mock_result
        mock_gen_class.return_value = mock_gen

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("calc.py", "w") as f:
                f.write("def add(a, b): return a + b")

            result = runner.invoke(cli, ["testgen", "calc.py", "-f", "json"])

            assert result.exit_code == 0


class TestFixFormats:
    """修正提案出力形式のテスト"""

    @pytest.fixture
    def runner(self):
        """CLIランナー"""
        return CliRunner()

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.BugFixer")
    def test_fix_json_format(self, mock_fixer_class, runner, tmp_path):
        """JSON形式での修正提案出力"""
        from devbuddy.core.fixer import FixResult

        mock_fixer = MagicMock()
        mock_result = FixResult(success=True, suggestions=[])
        mock_fixer.suggest_fix.return_value = mock_result
        mock_fixer_class.return_value = mock_fixer

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("test.py", "w") as f:
                f.write("def test_foo(): pass")

            result = runner.invoke(cli, ["fix", "test.py", "-f", "json"])

            assert result.exit_code == 0

    @patch.dict("os.environ", {"DEVBUDDY_API_KEY": "test-key"})
    @patch("devbuddy.cli.BugFixer")
    def test_fix_with_output_file(self, mock_fixer_class, runner, tmp_path):
        """結果をファイルに出力"""
        mock_fixer = MagicMock()
        mock_fixer.suggest_fix.return_value = MagicMock(suggestions=[])
        mock_fixer_class.return_value = mock_fixer

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with open("test.py", "w") as f:
                f.write("def test_foo(): pass")

            result = runner.invoke(
                cli, ["fix", "test.py", "-o", "result.txt"]
            )

            assert result.exit_code == 0
            assert "saved to" in result.output
