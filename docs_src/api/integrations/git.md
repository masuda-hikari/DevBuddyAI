# Git操作 (git)

ローカルGit操作モジュール。

## GitOperations

::: devbuddy.integrations.git.GitOperations
    options:
      show_source: true
      members:
        - __init__
        - get_diff
        - get_staged_diff
        - get_changed_files
        - get_commit_info

## 使用例

### 差分取得

```python
from devbuddy.integrations.git import GitOperations

git = GitOperations(repo_path=".")

# HEAD~1からの差分
diff = git.get_diff("HEAD~1")
print(diff)
```

### ステージ済み差分

```python
# git diff --staged と同等
staged_diff = git.get_staged_diff()
print(staged_diff)
```

### 変更ファイル一覧

```python
files = git.get_changed_files("HEAD~1")
for file in files:
    print(file)
```

### コミット情報

```python
info = git.get_commit_info("HEAD")
print(f"Author: {info['author']}")
print(f"Message: {info['message']}")
print(f"Date: {info['date']}")
```

## CLI連携

```bash
# HEAD~1からの変更をレビュー
devbuddy review --diff HEAD~1

# ステージ済みの変更をレビュー
devbuddy review --staged

# 特定コミット間の変更をレビュー
devbuddy review --diff abc123..def456
```

## エラーハンドリング

```python
from devbuddy.integrations.git import GitOperations, GitError

try:
    git = GitOperations(repo_path="/not/a/repo")
except GitError as e:
    print(f"Git error: {e}")
```
