# プロンプト (prompts)

プロンプトテンプレート集。

## PromptTemplates

::: devbuddy.llm.prompts.PromptTemplates
    options:
      show_source: true
      members:
        - code_review
        - diff_review
        - test_generation
        - fix_failing_tests
        - suggest_improvements

## 使用例

### コードレビュー

```python
from devbuddy.llm.prompts import PromptTemplates

prompts = PromptTemplates()

prompt = prompts.code_review(
    code="def add(a, b): return a + b",
    language="python",
    severity="medium"
)

print(prompt)
```

### テスト生成

```python
from devbuddy.core.generator import FunctionInfo

functions = [
    FunctionInfo(
        name="add",
        args=["a: int", "b: int"],
        return_type="int",
        docstring="2つの数値を加算",
        source="def add(a: int, b: int) -> int:\n    return a + b",
        line_start=1,
        line_end=2
    )
]

prompt = prompts.test_generation(
    functions=functions,
    module_name="calculator",
    framework="pytest"
)
```

### 失敗テスト修正

```python
prompt = prompts.fix_failing_tests(
    test_code="def test_add(): assert add(2, 2) == 5",
    error_output="AssertionError: assert 4 == 5"
)
```

## プロンプト構造

各プロンプトは以下の構造を持ちます:

1. **役割設定**: AIの役割を明確化
2. **タスク説明**: 実行すべきタスク
3. **入力データ**: コード、エラー等
4. **出力形式**: 期待する出力フォーマット
5. **制約条件**: 言語、フレームワーク等
