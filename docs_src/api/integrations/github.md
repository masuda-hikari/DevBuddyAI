# GitHub連携 (github)

GitHub API連携モジュール。

## GitHubIntegration

::: devbuddy.integrations.github.GitHubIntegration
    options:
      show_source: true
      members:
        - __init__
        - get_pr_diff
        - post_review_comment
        - create_review

## 使用例

### PR差分取得

```python
from devbuddy.integrations.github import GitHubIntegration

gh = GitHubIntegration(token="your_github_token")

# PR差分を取得
diff = gh.get_pr_diff(
    owner="masuda-hikari",
    repo="DevBuddyAI",
    pr_number=123
)

print(diff)
```

### レビューコメント投稿

```python
gh.post_review_comment(
    owner="masuda-hikari",
    repo="DevBuddyAI",
    pr_number=123,
    body="AIレビュー結果:\n- バグ発見: Line 45",
    path="src/main.py",
    line=45
)
```

### レビュー作成

```python
gh.create_review(
    owner="masuda-hikari",
    repo="DevBuddyAI",
    pr_number=123,
    event="COMMENT",
    body="DevBuddyAI自動レビュー完了"
)
```

## 環境変数

| 変数名 | 説明 |
|--------|------|
| GITHUB_TOKEN | GitHub Personal Access Token |

## 必要な権限

- `repo` - プライベートリポジトリアクセス
- `pull_request:write` - PRコメント権限

## GitHub Action連携

```yaml
name: DevBuddyAI Review

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: DevBuddyAI Review
        env:
          DEVBUDDY_API_KEY: ${{ secrets.DEVBUDDY_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          pip install devbuddy-ai
          devbuddy review --diff HEAD~1 --format markdown
```
