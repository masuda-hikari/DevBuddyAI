"""
共通データモデル

循環インポートを回避するための共通定義。
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Issue:
    """レビュー指摘事項"""

    level: str  # bug, warning, style, info
    line: int
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class ReviewResult:
    """レビュー結果"""

    file_path: Path
    issues: list[Issue] = field(default_factory=list)
    summary: str = ""
    success: bool = True
    error: Optional[str] = None
