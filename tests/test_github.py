"""
GitHubIntegrationのテスト
"""

import sys
import pytest
from unittest.mock import patch, MagicMock

from devbuddy.integrations.github import (
    GitHubIntegration,
    PRComment,
    ReviewSummary,
)


class TestPRComment:
    """PRCommentテストクラス"""

    def test_default_creation(self):
        """デフォルト値での作成"""
        comment = PRComment(body="Test comment")

        assert comment.body == "Test comment"
        assert comment.path is None
        assert comment.line is None
        assert comment.side == "RIGHT"

    def test_file_comment(self):
        """ファイル指定コメント"""
        comment = PRComment(
            body="Fix this line",
            path="src/main.py",
            line=42,
            side="LEFT",
        )

        assert comment.path == "src/main.py"
        assert comment.line == 42
        assert comment.side == "LEFT"


class TestReviewSummary:
    """ReviewSummaryテストクラス"""

    def test_default_creation(self):
        """デフォルト値での作成"""
        summary = ReviewSummary(body="LGTM")

        assert summary.body == "LGTM"
        assert summary.event == "COMMENT"

    def test_approve_event(self):
        """承認イベント"""
        summary = ReviewSummary(
            body="Approved with suggestions",
            event="APPROVE",
        )

        assert summary.event == "APPROVE"

    def test_request_changes_event(self):
        """変更リクエストイベント"""
        summary = ReviewSummary(
            body="Please fix these issues",
            event="REQUEST_CHANGES",
        )

        assert summary.event == "REQUEST_CHANGES"


class TestGitHubIntegration:
    """GitHubIntegrationテストクラス"""

    def test_init_with_token(self):
        """トークン指定での初期化"""
        gh = GitHubIntegration(token="ghp_test123")

        assert gh.token == "ghp_test123"

    @patch.dict("os.environ", {"GITHUB_TOKEN": "env_token"})
    def test_init_from_env(self):
        """環境変数からトークン取得"""
        gh = GitHubIntegration()

        assert gh.token == "env_token"

    @patch.dict("os.environ", {"GITHUB_TOKEN": ""})
    def test_init_no_token_raises(self):
        """トークンなしでエラー"""
        with pytest.raises(ValueError, match="GitHub token is required"):
            GitHubIntegration(token="")

    def test_client_lazy_init(self):
        """クライアント遅延初期化"""
        # githubモジュールをモック
        mock_github_module = MagicMock()
        mock_github_class = MagicMock()
        mock_github_module.Github = mock_github_class

        with patch.dict(sys.modules, {"github": mock_github_module}):
            gh = GitHubIntegration(token="test_token")

            # 初期状態ではクライアント未作成
            assert gh._client is None

            # clientプロパティアクセスで初期化
            _ = gh.client

            mock_github_class.assert_called_once_with("test_token")


class TestGitHubIntegrationWithMock:
    """GitHubIntegration モック使用テスト"""

    @pytest.fixture
    def mock_gh(self):
        """モック済みGitHubIntegration"""
        # githubモジュールをモック
        mock_github_module = MagicMock()
        mock_client = MagicMock()
        mock_github_module.Github.return_value = mock_client

        with patch.dict(sys.modules, {"github": mock_github_module}):
            gh = GitHubIntegration(token="test_token")
            gh._client = mock_client

            yield gh, mock_client

    def test_get_pr_diff(self, mock_gh):
        """PRのdiff取得"""
        gh, mock_client = mock_gh

        # モックセットアップ
        mock_file = MagicMock()
        mock_file.filename = "test.py"
        mock_file.patch = "@@ -1 +1 @@\n-old\n+new"

        mock_pr = MagicMock()
        mock_pr.get_files.return_value = [mock_file]

        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_client.get_repo.return_value = mock_repo

        diff = gh.get_pr_diff("owner/repo", 123)

        assert "test.py" in diff
        assert "-old" in diff
        assert "+new" in diff

    def test_get_pr_files(self, mock_gh):
        """PR変更ファイル取得"""
        gh, mock_client = mock_gh

        mock_file = MagicMock()
        mock_file.filename = "changed.py"
        mock_file.status = "modified"
        mock_file.additions = 10
        mock_file.deletions = 5
        mock_file.patch = "diff content"

        mock_pr = MagicMock()
        mock_pr.get_files.return_value = [mock_file]

        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_client.get_repo.return_value = mock_repo

        files = gh.get_pr_files("owner/repo", 123)

        assert len(files) == 1
        assert files[0]["filename"] == "changed.py"
        assert files[0]["status"] == "modified"
        assert files[0]["additions"] == 10

    def test_post_review_comment_general(self, mock_gh):
        """一般コメント投稿"""
        gh, mock_client = mock_gh

        mock_pr = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_client.get_repo.return_value = mock_repo

        comment = PRComment(body="General comment")
        result = gh.post_review_comment("owner/repo", 123, comment)

        assert result is True
        mock_pr.create_issue_comment.assert_called_once_with("General comment")

    def test_post_review_comment_file_line(self, mock_gh):
        """ファイル・行指定コメント投稿"""
        gh, mock_client = mock_gh

        mock_commit = MagicMock()
        mock_commit.sha = "abc123"

        mock_pr = MagicMock()
        mock_pr.get_commits.return_value = [mock_commit]

        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_repo.get_commit.return_value = mock_commit
        mock_client.get_repo.return_value = mock_repo

        comment = PRComment(
            body="Fix this",
            path="src/main.py",
            line=42,
        )
        result = gh.post_review_comment("owner/repo", 123, comment)

        assert result is True
        mock_pr.create_review_comment.assert_called_once()

    def test_post_review_comment_error(self, mock_gh):
        """コメント投稿エラー"""
        gh, mock_client = mock_gh

        mock_client.get_repo.side_effect = Exception("API error")

        comment = PRComment(body="Test")
        result = gh.post_review_comment("owner/repo", 123, comment)

        assert result is False

    def test_submit_review(self, mock_gh):
        """レビュー提出"""
        gh, mock_client = mock_gh

        mock_commit = MagicMock()
        mock_pr = MagicMock()
        mock_pr.get_commits.return_value = [mock_commit]

        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_client.get_repo.return_value = mock_repo

        summary = ReviewSummary(body="LGTM", event="APPROVE")
        result = gh.submit_review("owner/repo", 123, summary)

        assert result is True
        mock_pr.create_review.assert_called_once()

    def test_submit_review_with_comments(self, mock_gh):
        """コメント付きレビュー提出"""
        gh, mock_client = mock_gh

        mock_commit = MagicMock()
        mock_pr = MagicMock()
        mock_pr.get_commits.return_value = [mock_commit]

        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_client.get_repo.return_value = mock_repo

        summary = ReviewSummary(body="See comments", event="REQUEST_CHANGES")
        comments = [
            PRComment(body="Fix 1", path="a.py", line=10),
            PRComment(body="Fix 2", path="b.py", line=20),
        ]
        result = gh.submit_review("owner/repo", 123, summary, comments)

        assert result is True

    def test_submit_review_no_commits(self, mock_gh):
        """コミットなしでレビュー失敗"""
        gh, mock_client = mock_gh

        mock_pr = MagicMock()
        mock_pr.get_commits.return_value = []

        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_client.get_repo.return_value = mock_repo

        summary = ReviewSummary(body="Test")
        result = gh.submit_review("owner/repo", 123, summary)

        assert result is False

    def test_get_pr_comments(self, mock_gh):
        """PRコメント取得"""
        gh, mock_client = mock_gh

        mock_comment = MagicMock()
        mock_comment.id = 1
        mock_comment.user.login = "user1"
        mock_comment.body = "Comment body"
        mock_comment.created_at.isoformat.return_value = "2026-01-10T10:00:00"

        mock_pr = MagicMock()
        mock_pr.get_issue_comments.return_value = [mock_comment]

        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_client.get_repo.return_value = mock_repo

        comments = gh.get_pr_comments("owner/repo", 123)

        assert len(comments) == 1
        assert comments[0]["id"] == 1
        assert comments[0]["user"] == "user1"
        assert comments[0]["body"] == "Comment body"

    def test_create_check_run(self, mock_gh):
        """チェックラン作成"""
        gh, mock_client = mock_gh

        mock_repo = MagicMock()
        mock_client.get_repo.return_value = mock_repo

        result = gh.create_check_run(
            repo_name="owner/repo",
            head_sha="abc123",
            name="DevBuddyAI",
            status="completed",
            conclusion="success",
            summary="All good",
        )

        assert result is True
        mock_repo.create_check_run.assert_called_once()

    def test_create_check_run_error(self, mock_gh):
        """チェックラン作成エラー"""
        gh, mock_client = mock_gh

        mock_client.get_repo.side_effect = Exception("API error")

        result = gh.create_check_run(
            repo_name="owner/repo",
            head_sha="abc123",
        )

        assert result is False
