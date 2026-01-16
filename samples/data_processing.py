"""
データ処理のサンプルコード（pandas + 統計処理）

このコードをDevBuddyAIでレビュー・テスト生成してみましょう：
$ devbuddy review samples/data_processing.py
$ devbuddy testgen samples/data_processing.py
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class DataQualityReport:
    """データ品質レポート"""
    total_rows: int
    missing_values: Dict[str, int]
    duplicate_rows: int
    outliers: Dict[str, List[int]]  # 列名 -> 外れ値のインデックス
    numeric_stats: Dict[str, Dict[str, float]]


class DataCleaner:
    """データクリーニング"""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.original_shape = df.shape

    def remove_duplicates(self, subset: Optional[List[str]] = None) -> int:
        """重複行を削除"""
        before = len(self.df)
        self.df.drop_duplicates(subset=subset, inplace=True)
        return before - len(self.df)

    def fill_missing_numeric(self, strategy: str = 'mean') -> int:
        """数値列の欠損値を補完"""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        filled = 0

        for col in numeric_cols:
            missing = self.df[col].isna().sum()
            if missing > 0:
                if strategy == 'mean':
                    self.df[col].fillna(self.df[col].mean(), inplace=True)
                elif strategy == 'median':
                    self.df[col].fillna(self.df[col].median(), inplace=True)
                elif strategy == 'zero':
                    self.df[col].fillna(0, inplace=True)
                filled += missing

        return filled

    def remove_outliers_iqr(
        self, columns: List[str], threshold: float = 1.5
    ) -> int:
        """IQR法で外れ値を除去"""
        before = len(self.df)

        for col in columns:
            if col not in self.df.columns:
                continue

            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR

            self.df = self.df[
                (self.df[col] >= lower_bound) &
                (self.df[col] <= upper_bound)
            ]

        return before - len(self.df)

    def standardize_column_names(self) -> None:
        """カラム名を標準化（小文字・スネークケース）"""
        self.df.columns = [
            col.lower().replace(' ', '_').replace('-', '_')
            for col in self.df.columns
        ]

    def get_cleaned_data(self) -> pd.DataFrame:
        """クリーニング済みデータを取得"""
        return self.df


class DataAnalyzer:
    """データ分析"""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def generate_quality_report(self) -> DataQualityReport:
        """データ品質レポート生成"""
        # 欠損値
        missing = self.df.isna().sum().to_dict()
        missing = {k: v for k, v in missing.items() if v > 0}

        # 重複
        duplicates = self.df.duplicated().sum()

        # 外れ値検出
        outliers = self._detect_outliers_iqr()

        # 数値統計
        numeric_stats = {}
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            numeric_stats[col] = {
                'mean': float(self.df[col].mean()),
                'median': float(self.df[col].median()),
                'std': float(self.df[col].std()),
                'min': float(self.df[col].min()),
                'max': float(self.df[col].max())
            }

        return DataQualityReport(
            total_rows=len(self.df),
            missing_values=missing,
            duplicate_rows=int(duplicates),
            outliers=outliers,
            numeric_stats=numeric_stats
        )

    def _detect_outliers_iqr(
        self,
        threshold: float = 1.5
    ) -> Dict[str, List[int]]:
        """IQR法で外れ値を検出"""
        outliers = {}
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR

            outlier_mask = (
                (self.df[col] < lower_bound) |
                (self.df[col] > upper_bound)
            )
            outlier_indices = self.df[outlier_mask].index.tolist()

            if outlier_indices:
                outliers[col] = outlier_indices

        return outliers

    def find_correlations(
        self,
        threshold: float = 0.7
    ) -> List[Tuple[str, str, float]]:
        """強い相関を持つ列ペアを検出"""
        numeric_df = self.df.select_dtypes(include=[np.number])
        corr_matrix = numeric_df.corr()

        correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                corr_value = corr_matrix.iloc[i, j]

                if abs(corr_value) >= threshold:
                    correlations.append((col1, col2, float(corr_value)))

        return sorted(correlations, key=lambda x: abs(x[2]), reverse=True)


def process_sales_data(
    file_path: str
) -> Tuple[pd.DataFrame, DataQualityReport]:
    """売上データ処理のエンドツーエンド例"""
    # データ読み込み
    df = pd.read_csv(file_path)

    # クリーニング
    cleaner = DataCleaner(df)
    cleaner.standardize_column_names()
    duplicates_removed = cleaner.remove_duplicates()
    missing_filled = cleaner.fill_missing_numeric(strategy='median')
    outliers_removed = cleaner.remove_outliers_iqr(
        columns=['price', 'quantity'],
        threshold=2.0
    )

    cleaned_df = cleaner.get_cleaned_data()

    # 分析
    analyzer = DataAnalyzer(cleaned_df)
    report = analyzer.generate_quality_report()

    print("データクリーニング完了:")
    print(f"  - 重複削除: {duplicates_removed}行")
    print(f"  - 欠損値補完: {missing_filled}個")
    print(f"  - 外れ値削除: {outliers_removed}行")
    print(f"  - 最終行数: {len(cleaned_df)}")

    return cleaned_df, report


# DevBuddyAIで検出される可能性のある問題：
# - NaN/Inf値の処理（pandas操作で発生する可能性）
# - 空のDataFrameに対する操作
# - 列名の存在チェック
# - 型変換時のエラーハンドリング
#
# DevBuddyAIが生成するテストの例：
# - 正常系: 各クリーニング処理、統計計算、相関検出
# - 異常系: 空DataFrame、全欠損列、数値列なし
# - エッジケース: 単一行、全て同じ値、極端な外れ値
