"""
サンプルコード - バグ/問題を含む例

DevBuddyAIのテスト用サンプル。意図的に問題を含んでいる。
"""

from typing import Optional


def calculate_average(numbers: list) -> float:
    """リストの平均を計算

    問題点:
    - 空リストでゼロ除算
    - 型ヒントが不完全
    """
    total = sum(numbers)
    return total / len(numbers)  # BUG: ZeroDivisionError when empty


def process_user_data(data: dict) -> str:
    """ユーザーデータを処理

    問題点:
    - キーが存在しない場合のエラー
    - 戻り値型が不正確
    """
    name = data["name"]  # BUG: KeyError if missing
    age = data["age"]
    return f"{name} is {age} years old"


def unsafe_eval(expression: str) -> any:
    """式を評価（危険）

    問題点:
    - eval使用はセキュリティリスク
    - 型ヒントにanyを使用
    """
    return eval(expression)  # BUG: Security risk


def get_config(options: dict = {}) -> dict:
    """設定を取得

    問題点:
    - ミュータブルなデフォルト引数
    """
    options["timestamp"] = "now"
    return options


class DataProcessor:
    """データ処理クラス

    問題点:
    - グローバル変数使用
    - 例外処理が広すぎる
    """

    cache = []  # WARNING: Class-level mutable

    def process(self, data):
        global counter  # STYLE: Global usage
        try:
            result = self._transform(data)
            self.cache.append(result)
            return result
        except:  # WARNING: Bare except
            return None

    def _transform(self, data):
        return str(data).upper()


def divide_numbers(a, b):
    """二つの数を割る

    問題点:
    - 型ヒントなし
    - ゼロ除算チェックなし
    - docstringが不完全
    """
    return a / b


def FindUser(user_id):
    """ユーザーを検索

    問題点:
    - 関数名がsnake_caseでない（PEP8違反）
    - 型ヒントなし
    """
    users = {"1": "Alice", "2": "Bob"}
    return users.get(user_id)


# 期待されるDevBuddyAIの指摘:
#
# [BUG] Line 15: Division by zero when 'numbers' is empty
#   Suggestion: Add check: if not numbers: return 0.0
#
# [BUG] Line 25: KeyError possible when 'name' or 'age' missing
#   Suggestion: Use data.get('name', 'Unknown') or validate keys first
#
# [BUG] Line 35: Dangerous eval() usage - security risk
#   Suggestion: Use ast.literal_eval() for safe evaluation
#
# [WARNING] Line 42: Mutable default argument
#   Suggestion: Use None as default, initialize inside function
#
# [WARNING] Line 58: Bare except clause
#   Suggestion: Catch specific exceptions (e.g., except ValueError:)
#
# [STYLE] Line 68: Missing type hints
#   Suggestion: Add type hints (a: float, b: float) -> float
#
# [STYLE] Line 76: Function name 'FindUser' should use snake_case
#   Suggestion: Rename to 'find_user'
