"""
サンプルコード - クリーンな実装例

DevBuddyAIが生成すべき理想的なコード品質を示す。
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class User:
    """ユーザーデータクラス"""

    id: str
    name: str
    age: int
    email: Optional[str] = None


def calculate_average(numbers: list[float]) -> float:
    """リストの平均を計算

    Args:
        numbers: 数値のリスト

    Returns:
        平均値。空リストの場合は0.0

    Examples:
        >>> calculate_average([1, 2, 3])
        2.0
        >>> calculate_average([])
        0.0
    """
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def process_user_data(data: dict[str, str | int]) -> str:
    """ユーザーデータを処理

    Args:
        data: ユーザー情報を含む辞書

    Returns:
        フォーマットされたユーザー情報

    Raises:
        ValueError: 必須キーが存在しない場合
    """
    name = data.get("name")
    age = data.get("age")

    if name is None or age is None:
        raise ValueError("Missing required fields: 'name' and 'age'")

    return f"{name} is {age} years old"


def safe_evaluate(expression: str) -> float:
    """数式を安全に評価

    Args:
        expression: 評価する数式文字列

    Returns:
        計算結果

    Raises:
        ValueError: 無効な式の場合
    """
    import ast
    import operator

    # 許可する演算子
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }

    def _eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            op = operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op)}")
            return op(_eval(node.left), _eval(node.right))
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")

    try:
        tree = ast.parse(expression, mode="eval")
        return _eval(tree.body)
    except SyntaxError as e:
        raise ValueError(f"Invalid expression: {e}")


def get_config(options: Optional[dict[str, str]] = None) -> dict[str, str]:
    """設定を取得

    Args:
        options: オプション設定（省略時は空辞書を使用）

    Returns:
        タイムスタンプを追加した設定辞書
    """
    from datetime import datetime

    result = dict(options) if options else {}
    result["timestamp"] = datetime.now().isoformat()
    return result


class DataProcessor:
    """データ処理クラス

    Attributes:
        cache: 処理結果のキャッシュ
    """

    def __init__(self) -> None:
        self._cache: list[str] = []

    @property
    def cache(self) -> list[str]:
        """キャッシュのコピーを返す"""
        return self._cache.copy()

    def process(self, data: str) -> Optional[str]:
        """データを処理

        Args:
            data: 処理対象の文字列

        Returns:
            処理結果。エラー時はNone
        """
        try:
            result = self._transform(data)
            self._cache.append(result)
            return result
        except (TypeError, AttributeError) as e:
            # ログ出力が望ましい
            return None

    def _transform(self, data: str) -> str:
        """データを大文字に変換"""
        return str(data).upper()

    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        self._cache.clear()


def divide_numbers(a: float, b: float) -> float:
    """二つの数を割る

    Args:
        a: 被除数
        b: 除数

    Returns:
        商

    Raises:
        ValueError: 除数が0の場合
    """
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b


def find_user(user_id: str) -> Optional[str]:
    """ユーザーを検索

    Args:
        user_id: 検索するユーザーID

    Returns:
        ユーザー名。見つからない場合はNone
    """
    users = {"1": "Alice", "2": "Bob"}
    return users.get(user_id)
