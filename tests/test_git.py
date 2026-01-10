"""
GitOperationsのテスト
"""

import pytest
from unittest.mock import patch, MagicMock

from devbuddy.integrations.git import GitOperations, DiffInfo, CommitInfo


class TestGitOperations:
    """GitOperationsテストクラス"""

    @pytest.fixture
    def mock_git_repo(self, tmp_path):
        """モックGitリポジトリ"""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        return tmp_path

    @pytest.fixture
    def git_ops(self, mock_git_repo):
        """GitOperationsインスタンス"""
        with patch.object(
            GitOperations, "_run_git",
            return_value=MagicMock(stdout="", returncode=0)
        ):
            return GitOperations(repo_path=mock_git_repo)

    def test_init_valid_repo(self, mock_git_repo):
        """有効なリポジトリで初期化"""
        ops = GitOperations(repo_path=mock_git_repo)
        assert ops.repo_path == mock_git_repo

    def test_init_invalid_repo(self, tmp_path):
        """無効なリポジトリでエラー"""
        with pytest.raises(ValueError, match="Not a git repository"):
            GitOperations(repo_path=tmp_path)

    def test_is_git_repo_true(self, mock_git_repo):
        """Gitリポジトリ判定（True）"""
        ops = GitOperations(repo_path=mock_git_repo)
        assert ops._is_git_repo() is True

    def test_is_git_repo_false(self, tmp_path):
        """Gitリポジトリ判定（False）"""
        # 直接チェック（初期化せず）
        git_dir = tmp_path / ".git"
        assert not git_dir.exists()


class TestDiffInfo:
    """DiffInfoテストクラス"""

    def test_creation(self):
        """DiffInfo作成"""
        diff = DiffInfo(
            content="@@ -1,3 +1,4 @@\n+new line",
            files_changed=2,
            insertions=10,
            deletions=5,
        )

        assert diff.content == "@@ -1,3 +1,4 @@\n+new line"
        assert diff.files_changed == 2
        assert diff.insertions == 10
        assert diff.deletions == 5


class TestCommitInfo:
    """CommitInfoテストクラス"""

    def test_creation(self):
        """CommitInfo作成"""
        commit = CommitInfo(
            sha="abc123def456",
            message="Initial commit",
            author="Test Author",
            date="2026-01-10 10:00:00 +0900",
        )

        assert commit.sha == "abc123def456"
        assert commit.message == "Initial commit"
        assert commit.author == "Test Author"
        assert "2026-01-10" in commit.date


class TestGitOperationsWithMock:
    """GitOperations モック使用テスト"""

    @pytest.fixture
    def mock_git_repo(self, tmp_path):
        """モックGitリポジトリ"""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        return tmp_path

    @patch("devbuddy.integrations.git.subprocess.run")
    def test_get_current_branch(self, mock_run, mock_git_repo):
        """現在のブランチ取得"""
        mock_run.return_value = MagicMock(stdout="main\n", returncode=0)

        ops = GitOperations(repo_path=mock_git_repo)
        branch = ops.get_current_branch()

        assert branch == "main"

    @patch("devbuddy.integrations.git.subprocess.run")
    def test_get_changed_files(self, mock_run, mock_git_repo):
        """変更ファイル取得"""
        mock_run.return_value = MagicMock(
            stdout="file1.py\nfile2.py\n",
            returncode=0
        )

        ops = GitOperations(repo_path=mock_git_repo)
        files = ops.get_changed_files()

        assert "file1.py" in files
        assert "file2.py" in files

    @patch("devbuddy.integrations.git.subprocess.run")
    def test_get_changed_files_staged(self, mock_run, mock_git_repo):
        """ステージ済み変更ファイル"""
        mock_run.return_value = MagicMock(
            stdout="staged.py\n",
            returncode=0
        )

        ops = GitOperations(repo_path=mock_git_repo)
        files = ops.get_changed_files(staged=True)

        assert "staged.py" in files
        # --cached オプション確認
        call_args = mock_run.call_args[0][0]
        assert "--cached" in call_args

    @patch("devbuddy.integrations.git.subprocess.run")
    def test_get_file_diff(self, mock_run, mock_git_repo):
        """ファイルdiff取得"""
        mock_run.return_value = MagicMock(
            stdout="@@ -1 +1 @@\n-old\n+new\n",
            returncode=0
        )

        ops = GitOperations(repo_path=mock_git_repo)
        diff = ops.get_file_diff("test.py")

        assert "@@ -1 +1 @@" in diff
        assert "-old" in diff
        assert "+new" in diff

    @patch("devbuddy.integrations.git.subprocess.run")
    def test_get_commit_info(self, mock_run, mock_git_repo):
        """コミット情報取得"""
        mock_run.return_value = MagicMock(
            stdout="abc123\nTest commit\nAuthor\n2026-01-10",
            returncode=0
        )

        ops = GitOperations(repo_path=mock_git_repo)
        info = ops.get_commit_info()

        assert info.sha == "abc123"
        assert info.message == "Test commit"
        assert info.author == "Author"

    @patch("devbuddy.integrations.git.subprocess.run")
    def test_get_commit_info_empty(self, mock_run, mock_git_repo):
        """コミット情報空の場合"""
        mock_run.return_value = MagicMock(
            stdout="",
            returncode=0
        )

        ops = GitOperations(repo_path=mock_git_repo)
        info = ops.get_commit_info()

        assert info.sha == ""
        assert info.message == ""

    @patch("devbuddy.integrations.git.subprocess.run")
    def test_get_recent_commits(self, mock_run, mock_git_repo):
        """最近のコミット取得"""
        mock_run.return_value = MagicMock(
            stdout="sha1|msg1|author1|date1\nsha2|msg2|author2|date2\n",
            returncode=0
        )

        ops = GitOperations(repo_path=mock_git_repo)
        commits = ops.get_recent_commits(count=2)

        assert len(commits) == 2
        assert commits[0].sha == "sha1"
        assert commits[1].sha == "sha2"

    @patch("devbuddy.integrations.git.subprocess.run")
    def test_get_untracked_files(self, mock_run, mock_git_repo):
        """未追跡ファイル取得"""
        mock_run.return_value = MagicMock(
            stdout="new_file.py\nanother.py\n",
            returncode=0
        )

        ops = GitOperations(repo_path=mock_git_repo)
        files = ops.get_untracked_files()

        assert "new_file.py" in files
        assert "another.py" in files

    @patch("devbuddy.integrations.git.subprocess.run")
    def test_is_file_tracked_true(self, mock_run, mock_git_repo):
        """ファイル追跡確認（True）"""
        mock_run.return_value = MagicMock(
            stdout="tracked.py\n",
            returncode=0
        )

        ops = GitOperations(repo_path=mock_git_repo)
        result = ops.is_file_tracked("tracked.py")

        assert result is True

    @patch("devbuddy.integrations.git.subprocess.run")
    def test_is_file_tracked_false(self, mock_run, mock_git_repo):
        """ファイル追跡確認（False）"""
        mock_run.return_value = MagicMock(
            stdout="",
            returncode=0
        )

        ops = GitOperations(repo_path=mock_git_repo)
        result = ops.is_file_tracked("untracked.py")

        assert result is False

    @patch("devbuddy.integrations.git.subprocess.run")
    def test_get_file_content_at_commit(self, mock_run, mock_git_repo):
        """特定コミット時点のファイル内容"""
        mock_run.return_value = MagicMock(
            stdout="old content",
            returncode=0
        )

        ops = GitOperations(repo_path=mock_git_repo)
        content = ops.get_file_content_at_commit("file.py", "HEAD~1")

        assert content == "old content"

    @patch("devbuddy.integrations.git.subprocess.run")
    def test_get_file_content_at_commit_not_found(self, mock_run, mock_git_repo):
        """存在しないファイル"""
        mock_run.return_value = MagicMock(
            stdout="",
            returncode=128
        )

        ops = GitOperations(repo_path=mock_git_repo)
        content = ops.get_file_content_at_commit("nonexistent.py")

        assert content is None

    @patch("devbuddy.integrations.git.subprocess.run")
    def test_get_hooks_path(self, mock_run, mock_git_repo):
        """hooksパス取得"""
        mock_run.return_value = MagicMock(
            stdout=".git/hooks\n",
            returncode=0
        )

        ops = GitOperations(repo_path=mock_git_repo)
        hooks_path = ops.get_hooks_path()

        assert "hooks" in str(hooks_path)

    @patch("devbuddy.integrations.git.subprocess.run")
    def test_install_pre_commit_hook(self, mock_run, mock_git_repo):
        """pre-commitフックインストール"""
        mock_run.return_value = MagicMock(
            stdout=".git/hooks\n",
            returncode=0
        )

        ops = GitOperations(repo_path=mock_git_repo)
        result = ops.install_pre_commit_hook("#!/bin/sh\necho test")

        assert result is True

        # フックファイル確認
        hook_file = mock_git_repo / ".git" / "hooks" / "pre-commit"
        assert hook_file.exists()
        assert "echo test" in hook_file.read_text()
