"""
GitOperations - Git操作

ローカルGitリポジトリとの連携を担当。
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class DiffInfo:
    """diff情報"""

    content: str
    files_changed: int
    insertions: int
    deletions: int


@dataclass
class CommitInfo:
    """コミット情報"""

    sha: str
    message: str
    author: str
    date: str


class GitOperations:
    """Git操作クラス"""

    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path.cwd()

        if not self._is_git_repo():
            raise ValueError(f"Not a git repository: {self.repo_path}")

    def _is_git_repo(self) -> bool:
        """Gitリポジトリかどうかを確認"""
        git_dir = self.repo_path / ".git"
        return git_dir.exists()

    def _run_git(
        self,
        args: list[str],
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """gitコマンドを実行"""
        return subprocess.run(
            ["git"] + args,
            cwd=self.repo_path,
            capture_output=capture_output,
            text=True,
            timeout=30,
        )

    def get_diff(
        self,
        staged: bool = False,
        commit: Optional[str] = None,
    ) -> DiffInfo:
        """diffを取得

        Args:
            staged: ステージ済み変更のみ
            commit: 特定コミットとの比較

        Returns:
            DiffInfo: diff情報
        """
        args = ["diff"]
        if staged:
            args.append("--cached")
        if commit:
            args.append(commit)

        result = self._run_git(args)
        content = result.stdout

        # 統計情報を取得
        stat_args = args + ["--stat"]
        stat_result = self._run_git(stat_args)

        # 統計をパース
        lines = stat_result.stdout.strip().split("\n")
        files_changed = 0
        insertions = 0
        deletions = 0

        if lines:
            last_line = lines[-1]
            # "3 files changed, 10 insertions(+), 5 deletions(-)"
            if "file" in last_line:
                parts = last_line.split(",")
                for part in parts:
                    part = part.strip()
                    if "file" in part:
                        files_changed = int(part.split()[0])
                    elif "insertion" in part:
                        insertions = int(part.split()[0])
                    elif "deletion" in part:
                        deletions = int(part.split()[0])

        return DiffInfo(
            content=content,
            files_changed=files_changed,
            insertions=insertions,
            deletions=deletions,
        )

    def get_changed_files(
        self,
        staged: bool = False,
        commit: Optional[str] = None,
    ) -> list[str]:
        """変更されたファイルリストを取得"""
        args = ["diff", "--name-only"]
        if staged:
            args.append("--cached")
        if commit:
            args.append(commit)

        result = self._run_git(args)
        files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
        return files

    def get_file_diff(
        self,
        file_path: str,
        staged: bool = False,
    ) -> str:
        """特定ファイルのdiffを取得"""
        args = ["diff"]
        if staged:
            args.append("--cached")
        args.append("--")
        args.append(file_path)

        result = self._run_git(args)
        return result.stdout

    def get_current_branch(self) -> str:
        """現在のブランチ名を取得"""
        result = self._run_git(["branch", "--show-current"])
        return result.stdout.strip()

    def get_commit_info(self, commit: str = "HEAD") -> CommitInfo:
        """コミット情報を取得"""
        format_str = "%H%n%s%n%an%n%ai"
        result = self._run_git(["log", "-1", f"--format={format_str}", commit])

        lines = result.stdout.strip().split("\n")
        if len(lines) >= 4:
            return CommitInfo(
                sha=lines[0],
                message=lines[1],
                author=lines[2],
                date=lines[3],
            )

        return CommitInfo(sha="", message="", author="", date="")

    def get_recent_commits(self, count: int = 10) -> list[CommitInfo]:
        """最近のコミットリストを取得"""
        format_str = "%H|%s|%an|%ai"
        result = self._run_git(["log", f"-{count}", f"--format={format_str}"])

        commits = []
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                parts = line.split("|", 3)
                if len(parts) >= 4:
                    commits.append(
                        CommitInfo(
                            sha=parts[0],
                            message=parts[1],
                            author=parts[2],
                            date=parts[3],
                        )
                    )

        return commits

    def get_file_content_at_commit(
        self,
        file_path: str,
        commit: str = "HEAD",
    ) -> Optional[str]:
        """特定コミット時点のファイル内容を取得"""
        result = self._run_git(["show", f"{commit}:{file_path}"])

        if result.returncode == 0:
            return result.stdout
        return None

    def get_blame(self, file_path: str) -> list[dict]:
        """ファイルのblame情報を取得"""
        result = self._run_git([
            "blame",
            "--line-porcelain",
            file_path,
        ])

        blame_info = []
        current = {}

        for line in result.stdout.split("\n"):
            if line.startswith("\t"):
                current["line_content"] = line[1:]
                blame_info.append(current)
                current = {}
            elif line:
                parts = line.split(" ", 1)
                if len(parts) == 2:
                    key = parts[0].replace("-", "_")
                    current[key] = parts[1]

        return blame_info

    def get_untracked_files(self) -> list[str]:
        """未追跡ファイルリストを取得"""
        result = self._run_git(["ls-files", "--others", "--exclude-standard"])
        files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
        return files

    def is_file_tracked(self, file_path: str) -> bool:
        """ファイルが追跡されているかチェック"""
        result = self._run_git(["ls-files", file_path])
        return bool(result.stdout.strip())

    def get_hooks_path(self) -> Path:
        """hooksディレクトリのパスを取得"""
        result = self._run_git(["rev-parse", "--git-path", "hooks"])
        return self.repo_path / result.stdout.strip()

    def install_pre_commit_hook(self, script: str) -> bool:
        """pre-commitフックをインストール"""
        hooks_path = self.get_hooks_path()
        hook_file = hooks_path / "pre-commit"

        try:
            hooks_path.mkdir(parents=True, exist_ok=True)
            with open(hook_file, "w", encoding="utf-8") as f:
                f.write(script)
            hook_file.chmod(0o755)
            return True
        except Exception:
            return False
