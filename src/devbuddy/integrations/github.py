"""
GitHubIntegration - GitHub連携

PRへの自動コメント、Issue作成等を担当。
"""

import os
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class PRComment:
    """PRコメント"""

    body: str
    path: Optional[str] = None  # ファイルパス（ファイル別コメントの場合）
    line: Optional[int] = None  # 行番号（行コメントの場合）
    side: str = "RIGHT"  # LEFT or RIGHT (diff側)


@dataclass
class ReviewSummary:
    """レビューサマリー"""

    body: str
    event: str = "COMMENT"  # COMMENT, APPROVE, REQUEST_CHANGES


class GitHubIntegration:
    """GitHub連携クラス"""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")

        if not self.token:
            raise ValueError(
                "GitHub token is required. "
                "Set GITHUB_TOKEN environment variable."
            )

        self._client: Any = None

    @property
    def client(self) -> Any:
        """PyGitHubクライアントを遅延初期化"""
        if self._client is None:
            try:
                from github import Github
            except ImportError:
                raise ImportError(
                    "PyGithub is required. Install with: pip install PyGithub"
                )
            self._client = Github(self.token)
        return self._client

    def get_pr_diff(self, repo_name: str, pr_number: int) -> str:
        """PRのdiffを取得

        Args:
            repo_name: リポジトリ名（owner/repo形式）
            pr_number: PR番号

        Returns:
            str: diff内容
        """
        repo = self.client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        # diffを取得
        files = pr.get_files()
        diff_parts = []

        for file in files:
            diff_parts.append(f"--- a/{file.filename}")
            diff_parts.append(f"+++ b/{file.filename}")
            if file.patch:
                diff_parts.append(file.patch)
            diff_parts.append("")

        return "\n".join(diff_parts)

    def get_pr_files(self, repo_name: str, pr_number: int) -> list[dict]:
        """PRの変更ファイルリストを取得

        Returns:
            list[dict]: ファイル情報リスト
        """
        repo = self.client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        files = []
        for file in pr.get_files():
            files.append({
                "filename": file.filename,
                "status": file.status,  # added, removed, modified
                "additions": file.additions,
                "deletions": file.deletions,
                "patch": file.patch,
            })

        return files

    def post_review_comment(
        self,
        repo_name: str,
        pr_number: int,
        comment: PRComment,
        commit_sha: Optional[str] = None,
    ) -> bool:
        """PRにレビューコメントを投稿

        Args:
            repo_name: リポジトリ名
            pr_number: PR番号
            comment: コメント内容
            commit_sha: コミットSHA（省略時は最新）

        Returns:
            bool: 成功/失敗
        """
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)

            if commit_sha is None:
                commits = list(pr.get_commits())
                commit_sha = commits[-1].sha if commits else None

            if comment.path and comment.line and commit_sha:
                # ファイル・行指定コメント
                pr.create_review_comment(
                    body=comment.body,
                    commit=repo.get_commit(commit_sha),
                    path=comment.path,
                    line=comment.line,
                    side=comment.side,
                )
            else:
                # 一般コメント
                pr.create_issue_comment(comment.body)

            return True
        except Exception:
            return False

    def submit_review(
        self,
        repo_name: str,
        pr_number: int,
        summary: ReviewSummary,
        comments: Optional[list[PRComment]] = None,
    ) -> bool:
        """レビューを提出

        Args:
            repo_name: リポジトリ名
            pr_number: PR番号
            summary: レビューサマリー
            comments: 個別コメントリスト

        Returns:
            bool: 成功/失敗
        """
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)

            commits = list(pr.get_commits())
            commit = commits[-1] if commits else None

            if not commit:
                return False

            # レビューコメントを準備
            review_comments = []
            if comments:
                for comment in comments:
                    if comment.path and comment.line:
                        review_comments.append({
                            "path": comment.path,
                            "line": comment.line,
                            "body": comment.body,
                            "side": comment.side,
                        })

            # レビューを作成
            pr.create_review(
                commit=commit,
                body=summary.body,
                event=summary.event,
                comments=review_comments if review_comments else None,
            )

            return True
        except Exception:
            return False

    def get_pr_comments(self, repo_name: str, pr_number: int) -> list[dict]:
        """PRのコメントを取得"""
        repo = self.client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        comments = []
        for comment in pr.get_issue_comments():
            comments.append({
                "id": comment.id,
                "user": comment.user.login,
                "body": comment.body,
                "created_at": comment.created_at.isoformat(),
            })

        return comments

    def create_check_run(
        self,
        repo_name: str,
        head_sha: str,
        name: str = "DevBuddyAI Review",
        status: str = "completed",
        conclusion: str = "neutral",
        summary: str = "",
        details: str = "",
    ) -> bool:
        """チェックランを作成

        Args:
            repo_name: リポジトリ名
            head_sha: コミットSHA
            name: チェック名
            status: ステータス（queued, in_progress, completed）
            conclusion: 結論（success, failure, neutral, etc.）
            summary: サマリー
            details: 詳細テキスト

        Returns:
            bool: 成功/失敗
        """
        try:
            repo = self.client.get_repo(repo_name)

            repo.create_check_run(
                name=name,
                head_sha=head_sha,
                status=status,
                conclusion=conclusion if status == "completed" else None,
                output={
                    "title": name,
                    "summary": summary,
                    "text": details,
                },
            )

            return True
        except Exception:
            return False
