# DevBuddyAI 貢献ガイド

DevBuddyAI への貢献に興味を持っていただきありがとうございます！このドキュメントでは、貢献の方法について説明します。

## 貢献の種類

### バグ報告

バグを発見した場合は、[GitHub Issues](https://github.com/masuda-hikari/DevBuddyAI/issues) で報告してください。

報告に含めるべき情報：
- DevBuddyAI のバージョン（`devbuddy --version`）
- Python のバージョン
- OS 情報
- 再現手順
- 期待される動作
- 実際の動作
- エラーメッセージ（ある場合）

### 機能リクエスト

新機能の提案は [GitHub Discussions](https://github.com/masuda-hikari/DevBuddyAI/discussions) で行ってください。

提案に含めるべき情報：
- 解決したい問題
- 提案する解決策
- 代替案（検討した場合）

### コード貢献

#### 開発環境のセットアップ

```bash
# リポジトリをクローン
git clone https://github.com/masuda-hikari/DevBuddyAI.git
cd DevBuddyAI

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 開発依存関係をインストール
pip install -e ".[dev]"
```

#### コーディング規約

- **スタイル**: PEP 8 に準拠（flake8 で検証）
- **型ヒント**: 全ての public 関数に型アノテーションを付ける（mypy で検証）
- **ドキュメント**: 全ての public 関数に docstring を記述
- **コメント**: 日本語で記述

#### テスト

```bash
# テスト実行
pytest

# カバレッジ付きで実行
pytest --cov=src/devbuddy --cov-report=html

# 特定のテストを実行
pytest tests/test_reviewer.py -v
```

テスト要件：
- 新機能には必ずテストを追加
- テストカバレッジ 80% 以上を維持
- 全テストが合格すること

#### 静的解析

```bash
# flake8（リント）
flake8 src/devbuddy tests

# mypy（型チェック）
mypy src/devbuddy

# black（フォーマット）- 任意
black src/devbuddy tests

# isort（インポート整理）- 任意
isort src/devbuddy tests
```

#### プルリクエストの手順

1. **Issue を作成**（大きな変更の場合）
2. **ブランチを作成**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **変更を実装**
4. **テストを追加・実行**
5. **静的解析を実行**
6. **コミット**
   ```bash
   git commit -m "機能: 新機能の説明"
   ```
7. **プッシュ**
   ```bash
   git push origin feature/your-feature-name
   ```
8. **プルリクエストを作成**

#### コミットメッセージの形式

```
<タイプ>: <説明>

[本文（任意）]
```

タイプ：
- `機能`: 新機能
- `修正`: バグ修正
- `改善`: 既存機能の改善
- `ドキュメント`: ドキュメントの変更
- `テスト`: テストの追加・修正
- `リファクタリング`: コードの整理（機能変更なし）
- `その他`: 上記以外

例：
```
機能: Python 3.12 の新構文サポートを追加

- match 文のパターンマッチング検出を追加
- type 文の型エイリアス検出を追加
```

### ドキュメント貢献

ドキュメントの改善も歓迎します：
- タイポの修正
- 説明の明確化
- 使用例の追加
- 翻訳

## コードオブコンダクト

### 私たちの約束

オープンで歓迎的な環境を育むために、貢献者およびメンテナーとして、年齢、体格、障害、民族、性自認および表現、経験のレベル、国籍、外見、人種、宗教、または性的アイデンティティおよび指向に関係なく、プロジェクトおよびコミュニティへの参加をハラスメントのない体験にすることを約束します。

### 私たちの基準

ポジティブな環境を作成することに貢献する行動の例：
- 歓迎的で包括的な言葉を使用する
- 異なる視点や経験を尊重する
- 建設的な批判を優雅に受け入れる
- コミュニティにとって最善なことに焦点を当てる
- 他のコミュニティメンバーに対する共感を示す

受け入れられない行動の例：
- 性的な言語やイメージの使用、および不要な性的注目や誘い
- 荒らし、侮辱的/軽蔑的なコメント、および個人的または政治的な攻撃
- 公的または私的なハラスメント
- 明示的な許可なく、住所や電子アドレスなど他者の個人情報を公開すること
- 専門的な環境で不適切と合理的に考えられる他の行為

## 質問・サポート

- **一般的な質問**: [GitHub Discussions](https://github.com/masuda-hikari/DevBuddyAI/discussions)
- **バグ報告**: [GitHub Issues](https://github.com/masuda-hikari/DevBuddyAI/issues)
- **セキュリティ問題**: security@devbuddy.ai（公開しないでください）

## ライセンス

貢献したコードは [MIT License](../LICENSE) の下でライセンスされます。

---

ご貢献をお待ちしております！
