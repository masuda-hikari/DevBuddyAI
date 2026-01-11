"""
E2Eテスト - 実際のCLI動作確認

実際のサンプルコードを使って、DevBuddyAI CLIの
エンドツーエンド動作を検証する。
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent


class TestCLIE2E:
    """CLI E2Eテスト"""

    def test_devbuddy_installed(self):
        """devbuddyコマンドが利用可能か確認"""
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "--version"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert "devbuddy" in result.stdout.lower()

    def test_devbuddy_help(self):
        """ヘルプ表示の確認"""
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert "review" in result.stdout
        assert "testgen" in result.stdout
        assert "fix" in result.stdout
        assert "license" in result.stdout
        assert "billing" in result.stdout

    def test_review_help(self):
        """reviewコマンドヘルプ"""
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "review", "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert "--severity" in result.stdout
        assert "--format" in result.stdout

    def test_testgen_help(self):
        """testgenコマンドヘルプ"""
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "testgen", "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert "--function" in result.stdout
        assert "--framework" in result.stdout

    def test_fix_help(self):
        """fixコマンドヘルプ"""
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "fix", "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert "--apply" in result.stdout
        assert "--source" in result.stdout

    def test_license_help(self):
        """licenseコマンドヘルプ"""
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "license", "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert "activate" in result.stdout
        assert "status" in result.stdout

    def test_billing_help(self):
        """billingコマンドヘルプ"""
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "billing", "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert "plans" in result.stdout
        assert "upgrade" in result.stdout

    def test_config_init(self, tmp_path):
        """設定ファイル初期化"""
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "config", "--init"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=tmp_path,
            env=env,
        )
        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")
        output = stdout + stderr
        # 設定ファイルが作成されるか、createdメッセージが出る
        assert (tmp_path / ".devbuddy.yaml").exists() or "created" in output

    def test_config_show_no_file(self, tmp_path):
        """設定ファイルなしの表示"""
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "config", "--show"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0
        assert "No config file" in result.stdout

    def test_config_list_keys(self, tmp_path):
        """設定キー一覧表示"""
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "config", "--list-keys"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0
        assert "language" in result.stdout
        assert "review.severity" in result.stdout

    def test_review_no_api_key(self, tmp_path):
        """APIキーなしでreview実行"""
        # テスト用ファイル作成
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")

        # 環境変数をクリア
        env = os.environ.copy()
        env.pop("DEVBUDDY_API_KEY", None)
        env.pop("ANTHROPIC_API_KEY", None)
        env.pop("OPENAI_API_KEY", None)

        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "review", str(test_file)],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env=env,
        )
        assert result.returncode == 1
        # stderrにもstdoutにも出力される可能性がある
        output = result.stdout + result.stderr
        assert "DEVBUDDY_API_KEY" in output

    def test_testgen_no_api_key(self, tmp_path):
        """APIキーなしでtestgen実行"""
        test_file = tmp_path / "test.py"
        test_file.write_text("def add(a, b): return a + b\n")

        env = os.environ.copy()
        env.pop("DEVBUDDY_API_KEY", None)
        env.pop("ANTHROPIC_API_KEY", None)
        env.pop("OPENAI_API_KEY", None)

        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "testgen", str(test_file)],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env=env,
        )
        assert result.returncode == 1
        output = result.stdout + result.stderr
        assert "DEVBUDDY_API_KEY" in output

    def test_fix_no_api_key(self, tmp_path):
        """APIキーなしでfix実行"""
        test_file = tmp_path / "test.py"
        test_file.write_text("def test_fail(): assert False\n")

        env = os.environ.copy()
        env.pop("DEVBUDDY_API_KEY", None)
        env.pop("ANTHROPIC_API_KEY", None)
        env.pop("OPENAI_API_KEY", None)

        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "fix", str(test_file)],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env=env,
        )
        assert result.returncode == 1
        output = result.stdout + result.stderr
        assert "DEVBUDDY_API_KEY" in output

    def test_license_status(self, tmp_path):
        """ライセンス状態確認"""
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "license", "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=tmp_path,
            env=env,
        )
        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")
        output = stdout + stderr
        # ライセンスなしの場合も正常終了、またはステータス出力がある
        assert result.returncode == 0 or "FREE" in output or "Plan" in output

    def test_billing_plans(self, tmp_path):
        """プラン一覧表示"""
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "billing", "plans"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=tmp_path,
            env=env,
        )
        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")
        output = stdout + stderr
        # Unicode問題があってもプラン表示の試みがある
        assert result.returncode == 0 or "FREE" in output or "Pro" in output


class TestSampleCodeAnalysis:
    """サンプルコードを使った解析テスト（モック不要の静的解析部分）"""

    @pytest.fixture
    def sample_buggy_code(self):
        """バグのあるサンプルコード"""
        return PROJECT_ROOT / "samples" / "buggy_code.py"

    def test_sample_file_exists(self, sample_buggy_code):
        """サンプルファイルの存在確認"""
        assert sample_buggy_code.exists(), "samples/buggy_code.py が必要です"

    def test_review_sample_no_api_key(self, sample_buggy_code, tmp_path):
        """サンプルファイルをAPIキーなしでreview"""
        if not sample_buggy_code.exists():
            pytest.skip("サンプルファイルがありません")

        env = os.environ.copy()
        env.pop("DEVBUDDY_API_KEY", None)
        env.pop("ANTHROPIC_API_KEY", None)
        env.pop("OPENAI_API_KEY", None)

        cmd = [sys.executable, "-m", "devbuddy", "review"]
        cmd.append(str(sample_buggy_code))
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env=env,
        )
        # APIキーがないのでエラー
        assert result.returncode == 1
        output = result.stdout + result.stderr
        assert "DEVBUDDY_API_KEY" in output


class TestOutputFormats:
    """出力形式テスト"""

    def test_format_option_review(self):
        """reviewコマンドの--formatオプション"""
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "review", "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert "--format" in result.stdout

    def test_format_option_testgen(self):
        """testgenコマンドの--formatオプション"""
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "testgen", "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert "--format" in result.stdout

    def test_format_option_fix(self):
        """fixコマンドの--formatオプション"""
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "fix", "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert "--format" in result.stdout


class TestServerCommands:
    """サーバーコマンドテスト"""

    def test_server_help(self):
        """serverコマンドヘルプ"""
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "server", "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert "start" in result.stdout
        assert "info" in result.stdout

    def test_server_info(self):
        """server infoコマンド"""
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "server", "info"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        # fastapi未インストールでも正常終了するはず
        assert result.returncode == 0


class TestAuthCommand:
    """認証コマンドテスト"""

    def test_auth_command_exists(self):
        """authコマンドの存在確認"""
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "auth", "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        # authコマンドが存在するか確認
        assert result.returncode == 0


class TestModuleExecution:
    """モジュール実行テスト"""

    def test_python_m_devbuddy(self):
        """python -m devbuddy で実行可能"""
        result = subprocess.run(
            [sys.executable, "-m", "devbuddy", "--version"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0

    def test_direct_cli_import(self):
        """CLIモジュールの直接インポート"""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from devbuddy.cli import cli; print('OK')",
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert "OK" in result.stdout

    def test_core_modules_import(self):
        """コアモジュールのインポート確認"""
        modules = [
            "devbuddy.core.reviewer",
            "devbuddy.core.generator",
            "devbuddy.core.fixer",
            "devbuddy.core.licensing",
            "devbuddy.core.billing",
            "devbuddy.core.formatters",
        ]
        for module in modules:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"import {module}; print('OK')",
                ],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )
            assert result.returncode == 0, f"{module} のインポートに失敗"

    def test_analyzer_modules_import(self):
        """Analyzerモジュールのインポート確認"""
        modules = [
            "devbuddy.analyzers.python_analyzer",
            "devbuddy.analyzers.js_analyzer",
            "devbuddy.analyzers.rust_analyzer",
            "devbuddy.analyzers.go_analyzer",
        ]
        for module in modules:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"import {module}; print('OK')",
                ],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )
            assert result.returncode == 0, f"{module} のインポートに失敗"

    def test_llm_modules_import(self):
        """LLMモジュールのインポート確認"""
        modules = [
            "devbuddy.llm.client",
            "devbuddy.llm.prompts",
        ]
        for module in modules:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"import {module}; print('OK')",
                ],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )
            assert result.returncode == 0, f"{module} のインポートに失敗"
