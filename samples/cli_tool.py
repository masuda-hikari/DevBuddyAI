"""
CLIツールのサンプルコード（ファイル処理）

このコードをDevBuddyAIでレビュー・テスト生成してみましょう：
$ devbuddy review samples/cli_tool.py
$ devbuddy testgen samples/cli_tool.py --function parse_log_file
"""
import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LogEntry:
    """ログエントリー"""
    timestamp: datetime
    level: str
    message: str
    source: Optional[str] = None


class LogParser:
    """ログパーサー"""

    # ログパターン: [2024-01-01 12:00:00] INFO: Message from source
    LOG_PATTERN = re.compile(
        r'\[(?P<timestamp>[\d\-:\s]+)\]\s+'
        r'(?P<level>\w+):\s+'
        r'(?P<message>.+?)'
        r'(?:\s+from\s+(?P<source>\w+))?$'
    )

    def parse_line(self, line: str) -> Optional[LogEntry]:
        """ログ行をパース"""
        match = self.LOG_PATTERN.match(line.strip())
        if not match:
            return None

        try:
            timestamp = datetime.strptime(
                match.group('timestamp'),
                '%Y-%m-%d %H:%M:%S'
            )
            return LogEntry(
                timestamp=timestamp,
                level=match.group('level'),
                message=match.group('message'),
                source=match.group('source')
            )
        except ValueError:
            return None

    def parse_file(self, file_path: Path) -> List[LogEntry]:
        """ログファイルをパース"""
        entries = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                entry = self.parse_line(line)
                if entry:
                    entries.append(entry)
        return entries


class LogAnalyzer:
    """ログ分析"""

    def __init__(self, entries: List[LogEntry]):
        self.entries = entries

    def count_by_level(self) -> Dict[str, int]:
        """レベル別カウント"""
        counts: Dict[str, int] = {}
        for entry in self.entries:
            counts[entry.level] = counts.get(entry.level, 0) + 1
        return counts

    def filter_by_level(self, level: str) -> List[LogEntry]:
        """レベルでフィルタ"""
        return [e for e in self.entries if e.level == level]

    def filter_by_source(self, source: str) -> List[LogEntry]:
        """ソースでフィルタ"""
        return [e for e in self.entries if e.source == source]

    def find_errors(self) -> List[LogEntry]:
        """エラーログを抽出"""
        return [e for e in self.entries if e.level in ('ERROR', 'CRITICAL')]

    def get_time_range(self) -> tuple[datetime, datetime]:
        """時間範囲を取得"""
        if not self.entries:
            raise ValueError("No log entries")
        timestamps = [e.timestamp for e in self.entries]
        return min(timestamps), max(timestamps)


def format_summary(analyzer: LogAnalyzer) -> str:
    """サマリーをフォーマット"""
    counts = analyzer.count_by_level()
    errors = analyzer.find_errors()

    lines = ["ログ分析サマリー", "=" * 40]
    lines.append(f"総エントリー数: {len(analyzer.entries)}")

    try:
        start, end = analyzer.get_time_range()
        lines.append(f"期間: {start} - {end}")
    except ValueError:
        lines.append("期間: (データなし)")

    lines.append("\nレベル別カウント:")
    for level, count in sorted(counts.items()):
        lines.append(f"  {level}: {count}")

    if errors:
        lines.append(f"\n⚠️ エラー検出: {len(errors)}件")
        for error in errors[:5]:  # 最初の5件のみ
            lines.append(f"  - {error.timestamp}: {error.message}")

    return "\n".join(lines)


def main():
    """メインエントリポイント"""
    parser = argparse.ArgumentParser(description='ログファイル分析ツール')
    parser.add_argument('file', type=Path, help='ログファイルパス')
    parser.add_argument(
        '--level',
        help='特定レベルのみ表示',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    )
    parser.add_argument(
        '--source',
        help='特定ソースのみ表示'
    )
    args = parser.parse_args()

    if not args.file.exists():
        print(f"エラー: ファイルが存在しません: {args.file}")
        return 1

    # パース
    log_parser = LogParser()
    entries = log_parser.parse_file(args.file)

    # フィルタ
    analyzer = LogAnalyzer(entries)
    if args.level:
        entries = analyzer.filter_by_level(args.level)
    if args.source:
        entries = analyzer.filter_by_source(args.source)

    # 結果表示
    if not entries:
        print("該当するログエントリーがありません")
        return 0

    print(format_summary(LogAnalyzer(entries)))
    return 0


# DevBuddyAIで検出される可能性のある問題：
# - ファイル読み込みのエラーハンドリング不足
#   → FileNotFoundError, UnicodeDecodeErrorの処理
# - 正規表現のパフォーマンス（大量ログでは事前コンパイル済みなのでOK）
# - タイムゾーン情報の欠如（datetimeはnaive）
#
# DevBuddyAIが生成するテストの例：
# - 正常系: 各種ログ形式のパース、フィルタリング、集計
# - 異常系: 不正な日付形式、存在しないファイル、空ファイル
# - エッジケース: タイムスタンプ順でないログ、重複エントリー


if __name__ == '__main__':
    exit(main())
