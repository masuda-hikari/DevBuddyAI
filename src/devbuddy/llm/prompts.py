"""
PromptTemplates - プロンプトテンプレート

各機能で使用するプロンプトを管理。
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from devbuddy.core.generator import FunctionInfo


class PromptTemplates:
    """プロンプトテンプレート集"""

    def code_review(
        self,
        code: str,
        language: str = "python",
        severity: str = "medium",
    ) -> str:
        """コードレビュー用プロンプト"""
        severity_desc = {
            "low": "全ての問題（情報レベルも含む）",
            "medium": "バグ、警告、スタイル問題",
            "high": "バグと重大な警告のみ",
        }.get(severity, "バグ、警告、スタイル問題")

        return f"""あなたは経験豊富なシニアエンジニアです。以下の{language}コードをレビューしてください。

## レビュー観点
- バグ（論理エラー、null参照、ゼロ除算など）
- セキュリティ問題（インジェクション、認証漏れなど）
- パフォーマンス問題
- コーディングスタイル（PEP8準拠、命名規則など）
- ベストプラクティスからの逸脱

## 出力形式
各問題を以下の形式で報告してください：
[LEVEL] Line N: 問題の説明
  Suggestion: 改善提案

LEVELは以下のいずれか:
- BUG: 明確なバグ
- WARNING: 潜在的な問題
- STYLE: スタイル/可読性の問題
- INFO: 情報/提案

## フィルタ条件
{severity_desc}を報告してください。

## レビュー対象コード
```{language}
{code}
```

問題が見つからない場合は「No issues found」と回答してください。
"""

    def diff_review(self, diff: str) -> str:
        """git diff レビュー用プロンプト"""
        return f"""あなたは経験豊富なコードレビュアーです。以下のgit diffをレビューしてください。

## レビュー観点
- 追加されたコードにバグがないか
- 削除により機能が壊れていないか
- 変更の意図が明確か
- テストが必要な変更か

## 出力形式
[LEVEL] Line N: 問題の説明
  Suggestion: 改善提案

## diff
```diff
{diff}
```

変更に問題がない場合は「Changes look good」と回答してください。
"""

    def test_generation(
        self,
        functions: list["FunctionInfo"],
        module_name: str,
        framework: str = "pytest",
    ) -> str:
        """テスト生成用プロンプト"""
        func_descriptions = []
        for func in functions:
            desc = f"""
### 関数: {func.name}
- 引数: {', '.join(func.args) if func.args else 'なし'}
- 戻り値型: {func.return_type or '不明'}
- docstring: {func.docstring or 'なし'}
- ソース:
```python
{func.source}
```
"""
            func_descriptions.append(desc)

        all_funcs = "\n".join(func_descriptions)

        framework_import = {
            "pytest": "import pytest",
            "unittest": "import unittest",
        }.get(framework, "import pytest")

        return f"""あなたは経験豊富なテストエンジニアです。以下の関数に対するユニットテストを生成してください。

## テストフレームワーク
{framework}

## テスト対象モジュール
{module_name}

## 対象関数
{all_funcs}

## 要件
1. 各関数に対して複数のテストケースを作成
2. 正常系と異常系をカバー
3. エッジケース（境界値、空入力、null等）をテスト
4. アサーションは具体的に記述
5. テスト名は内容を明確に表現

## 出力形式
完全なPythonテストファイルを出力してください。
コメントやマークダウンは不要です。コードのみを出力してください。

```python
{framework_import}
from {module_name} import *

# テストコードをここに記述
```
"""

    def fix_failing_tests(
        self,
        test_code: str,
        error_output: str,
    ) -> str:
        """失敗テスト修正用プロンプト"""
        return f"""以下のテストが失敗しています。テストコードを修正してください。

## テストコード
```python
{test_code}
```

## エラー出力
```
{error_output}
```

## 要件
1. テストが通るように修正
2. テストの意図は変えない
3. 必要な場合はモックを追加
4. 修正後の完全なテストコードを出力

修正後のコードのみを出力してください（説明不要）。
"""

    def bug_fix(
        self,
        test_code: str,
        error_output: str,
        source_code: str | None = None,
    ) -> str:
        """バグ修正提案用プロンプト"""
        source_section = ""
        if source_code:
            source_section = f"""
## ソースコード
```python
{source_code}
```
"""

        return f"""以下のテストが失敗しています。バグを特定し、修正を提案してください。

## テストコード
```python
{test_code}
```

## エラー出力
```
{error_output}
```
{source_section}

## 出力形式
各修正提案を以下の形式で出力してください：

FILE: 修正対象ファイルパス
LINE: 行番号
DESCRIPTION: 問題の説明と修正理由
ORIGINAL: 元のコード行
REPLACEMENT: 修正後のコード行

複数の修正がある場合は、それぞれを上記形式で出力してください。
"""

    def explain_code(self, code: str, language: str = "python") -> str:
        """コード説明用プロンプト"""
        return f"""以下の{language}コードを説明してください。

```{language}
{code}
```

## 説明内容
1. コードの目的
2. 主要な処理フロー
3. 使用されているアルゴリズムやパターン
4. 注意点や改善可能な点

簡潔かつ明確に説明してください。
"""

    def suggest_improvements(self, code: str, language: str = "python") -> str:
        """改善提案用プロンプト"""
        return f"""以下の{language}コードの改善点を提案してください。

```{language}
{code}
```

## 観点
1. パフォーマンス最適化
2. 可読性向上
3. 保守性改善
4. エラーハンドリング強化
5. テスタビリティ向上

各提案には具体的なコード例を含めてください。
"""
