# PyPI公開手順ガイド

## 概要
DevBuddyAIをPyPIに公開するための手順書

## 前提条件
- PyPIアカウント（https://pypi.org）
- GitHubリポジトリ: masuda-hikari/DevBuddyAI

## 方法1: Trusted Publisher（推奨）

### Step 1: PyPIでTrusted Publisher設定

1. https://pypi.org にログイン
2. 「Publishing」→「Add a new pending publisher」
3. 以下を入力:
   - PyPI Project Name: `devbuddy-ai`
   - Owner: `masuda-hikari`
   - Repository name: `DevBuddyAI`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
4. 「Add」をクリック

### Step 2: GitHubでリリース作成

1. GitHubリポジトリページへ移動
2. 「Releases」→「Create a new release」
3. Tag: `v0.1.0`
4. Title: `DevBuddyAI v0.1.0 - Initial Release`
5. Description:
```
## DevBuddyAI v0.1.0

AIを活用した開発者支援ツールの初回リリース

### 機能
- コードレビュー自動化
- テスト生成
- GitHub連携

### インストール
pip install devbuddy-ai
```
6. 「Publish release」をクリック

→ GitHub Actionsが自動でPyPIに公開

## 方法2: 手動公開（APIトークン使用）

### Step 1: APIトークン取得

1. https://pypi.org/manage/account/token/ にアクセス
2. 「Add API token」をクリック
3. Token name: `devbuddy-ai-publish`
4. Scope: `Entire account`（初回）または `Project: devbuddy-ai`
5. 「Create token」→トークンをコピー

### Step 2: ローカル設定

`~/.pypirc` を作成:
```ini
[pypi]
username = __token__
password = pypi-xxxxxxxxxxxxxxxx
```

### Step 3: アップロード

```bash
cd O:\Dev\Work\DevBuddyAI
python -m build
python -m twine upload dist/*
```

## TestPyPIでの事前テスト

### TestPyPI Trusted Publisher設定

1. https://test.pypi.org にログイン
2. 同様にTrusted Publisher設定
   - Workflow name: `publish-test.yml`（別ワークフロー推奨）

### 手動TestPyPIアップロード

```bash
python -m twine upload --repository testpypi dist/*
```

### TestPyPIからインストールテスト

```bash
pip install --index-url https://test.pypi.org/simple/ devbuddy-ai
```

## 公開後の確認

1. https://pypi.org/project/devbuddy-ai/ を確認
2. `pip install devbuddy-ai` で動作確認
3. `devbuddy --version` を実行

## トラブルシューティング

### エラー: HTTPError 403 Forbidden
- APIトークンの権限を確認
- Trusted Publisher設定の環境名を確認

### エラー: Package already exists
- バージョン番号を更新（pyproject.toml）
- 既存パッケージは削除不可（新バージョンのみ）

---
作成日: 2026-01-09
