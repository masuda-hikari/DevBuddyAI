# 貢献ガイド

DevBuddyAIへの貢献をお待ちしています。

## 開発環境セットアップ

```bash
git clone https://github.com/masuda-hikari/DevBuddyAI.git
cd DevBuddyAI
pip install -e ".[dev]"
```

## 開発フロー

1. Issueを作成または既存のIssueを確認
2. フォーク → ブランチ作成
3. 実装 → テスト追加
4. PR作成

## コード品質基準

### 必須チェック

```bash
# flake8
python -m flake8 src/devbuddy

# mypy
python -m mypy src/devbuddy

# pytest
python -m pytest tests/ -v
```

### 基準

- flake8: 0 errors
- mypy: 0 errors
- テストカバレッジ: 80%以上

## コミットメッセージ

```
[種別] 簡潔な説明

詳細な説明（任意）
```

種別:
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `test`: テスト追加
- `refactor`: リファクタリング

## PRガイドライン

1. タイトルは明確に
2. 変更内容を説明
3. テスト追加
4. ドキュメント更新

## ライセンス

MITライセンスに同意の上、貢献してください。
