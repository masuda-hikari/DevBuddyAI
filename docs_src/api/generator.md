# テスト生成 (generator)

AIテスト生成エンジン。

## CodeTestGenerator

::: devbuddy.core.generator.CodeTestGenerator
    options:
      show_source: true
      members:
        - __init__
        - generate_tests
        - generate_and_verify

## 使用例

### 基本的なテスト生成

```python
from pathlib import Path
from devbuddy.llm.client import LLMClient
from devbuddy.core.generator import CodeTestGenerator

client = LLMClient()
generator = CodeTestGenerator(client)

result = generator.generate_tests(
    Path("src/calculator.py"),
    function_name="add",
    framework="pytest"
)

if result.success:
    print(f"Generated {result.test_count} tests")
    print(result.test_code)
else:
    print(f"Error: {result.error}")
```

### 自己検証付きテスト生成

```python
# テストを生成→実行→失敗時は自動修正（最大3回）
result = generator.generate_and_verify(
    Path("src/calculator.py"),
    framework="pytest"
)

if result.verified:
    print("All generated tests passed!")
    print(result.test_code)
```

## データモデル

### FunctionInfo

```python
@dataclass
class FunctionInfo:
    name: str                    # 関数名
    args: list[str]              # 引数リスト
    return_type: Optional[str]   # 戻り値型
    docstring: Optional[str]     # docstring
    source: str                  # ソースコード
    line_start: int              # 開始行
    line_end: int                # 終了行
```

### GenerationResult

```python
@dataclass
class GenerationResult:
    success: bool              # 生成成功
    test_code: str = ""        # 生成されたテストコード
    error: Optional[str] = None  # エラーメッセージ
    test_count: int = 0        # テスト数
    verified: bool = False     # 検証済みフラグ
```

## 自己検証ループ

```
生成 → 実行 → 失敗 → 修正 → 再実行
         │             │
       成功 ←─────────┘
```

最大3回のリトライで、AIが失敗原因を分析して修正を試行します。
