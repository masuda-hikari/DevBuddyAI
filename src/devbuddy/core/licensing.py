"""
ライセンス・認証システム

プラン制限と利用量トラッキングを管理。
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class Plan(Enum):
    """利用プラン"""
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"


@dataclass
class PlanLimits:
    """プラン制限"""
    reviews_per_month: int
    max_file_lines: int
    private_repos: bool
    github_integration: bool
    self_hosted: bool
    priority_support: bool
    testgen_per_month: int
    fix_per_month: int


# プラン別制限定義
PLAN_LIMITS: dict[Plan, PlanLimits] = {
    Plan.FREE: PlanLimits(
        reviews_per_month=50,
        max_file_lines=500,
        private_repos=False,
        github_integration=False,
        self_hosted=False,
        priority_support=False,
        testgen_per_month=20,
        fix_per_month=10,
    ),
    Plan.PRO: PlanLimits(
        reviews_per_month=500,
        max_file_lines=2000,
        private_repos=True,
        github_integration=True,
        self_hosted=False,
        priority_support=False,
        testgen_per_month=200,
        fix_per_month=100,
    ),
    Plan.TEAM: PlanLimits(
        reviews_per_month=-1,  # 無制限
        max_file_lines=-1,  # 無制限
        private_repos=True,
        github_integration=True,
        self_hosted=False,
        priority_support=True,
        testgen_per_month=-1,
        fix_per_month=-1,
    ),
    Plan.ENTERPRISE: PlanLimits(
        reviews_per_month=-1,
        max_file_lines=-1,
        private_repos=True,
        github_integration=True,
        self_hosted=True,
        priority_support=True,
        testgen_per_month=-1,
        fix_per_month=-1,
    ),
}


@dataclass
class UsageRecord:
    """利用量レコード"""
    reviews: int = 0
    testgens: int = 0
    fixes: int = 0
    month: str = ""  # YYYY-MM形式
    last_updated: str = ""


@dataclass
class License:
    """ライセンス情報"""
    license_key: str
    plan: Plan
    email: str
    organization: Optional[str] = None
    expires_at: Optional[str] = None  # ISO形式
    created_at: str = ""
    is_valid: bool = True
    features: dict = field(default_factory=dict)

    def is_expired(self) -> bool:
        """有効期限切れかどうか"""
        if not self.expires_at:
            return False
        expires_str = self.expires_at.replace("Z", "+00:00")
        expires = datetime.fromisoformat(expires_str)
        return datetime.now(timezone.utc) > expires

    def get_limits(self) -> PlanLimits:
        """プラン制限を取得"""
        return PLAN_LIMITS.get(self.plan, PLAN_LIMITS[Plan.FREE])


class LicenseError(Exception):
    """ライセンスエラー"""
    pass


class UsageLimitError(LicenseError):
    """利用制限エラー"""
    pass


class LicenseManager:
    """ライセンス管理クラス"""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        license_key: Optional[str] = None,
    ):
        """
        Args:
            data_dir: データ保存ディレクトリ（デフォルト: ~/.devbuddy）
            license_key: ライセンスキー（環境変数からも取得可能）
        """
        self.data_dir = data_dir or Path.home() / ".devbuddy"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.license_file = self.data_dir / "license.json"
        self.usage_file = self.data_dir / "usage.json"

        # ライセンスキー取得（引数 > 環境変数）
        self.license_key = license_key or os.environ.get(
            "DEVBUDDY_LICENSE_KEY", ""
        )

        self._license: Optional[License] = None
        self._usage: Optional[UsageRecord] = None

    def activate(self, license_key: str, email: str) -> License:
        """ライセンスをアクティベート

        Args:
            license_key: ライセンスキー
            email: メールアドレス

        Returns:
            License: アクティベートされたライセンス
        """
        # ライセンスキーを検証・デコード
        plan = self._decode_license_key(license_key)

        license_info = License(
            license_key=license_key,
            plan=plan,
            email=email,
            created_at=datetime.now(timezone.utc).isoformat(),
            is_valid=True,
        )

        # ライセンス情報を保存
        self._save_license(license_info)
        self._license = license_info

        return license_info

    def _decode_license_key(self, key: str) -> Plan:
        """ライセンスキーからプランを判定

        キー形式: DB-{PLAN}-{HASH}
        例: DB-PRO-abc123def456
        """
        if not key.startswith("DB-"):
            raise LicenseError("Invalid license key format")

        parts = key.split("-")
        if len(parts) < 3:
            raise LicenseError("Invalid license key format")

        plan_code = parts[1].upper()
        plan_map = {
            "FREE": Plan.FREE,
            "PRO": Plan.PRO,
            "TEAM": Plan.TEAM,
            "ENT": Plan.ENTERPRISE,
            "ENTERPRISE": Plan.ENTERPRISE,
        }

        if plan_code not in plan_map:
            raise LicenseError(f"Unknown plan: {plan_code}")

        return plan_map[plan_code]

    def get_license(self) -> Optional[License]:
        """現在のライセンス情報を取得"""
        if self._license:
            return self._license

        if self.license_file.exists():
            try:
                with open(self.license_file, encoding="utf-8") as f:
                    data = json.load(f)
                    data["plan"] = Plan(data["plan"])
                    self._license = License(**data)
                    return self._license
            except Exception:
                return None

        return None

    def get_plan(self) -> Plan:
        """現在のプランを取得（ライセンスがなければFREE）"""
        license_info = self.get_license()
        is_active = (license_info is not None and license_info.is_valid
                     and not license_info.is_expired())
        if is_active and license_info is not None:
            return license_info.plan
        return Plan.FREE

    def get_limits(self) -> PlanLimits:
        """現在のプラン制限を取得"""
        return PLAN_LIMITS[self.get_plan()]

    def _save_license(self, license_info: License) -> None:
        """ライセンス情報を保存"""
        data = asdict(license_info)
        data["plan"] = license_info.plan.value
        with open(self.license_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_usage(self) -> UsageRecord:
        """現在の利用量を取得"""
        if self._usage:
            return self._usage

        current_month = datetime.now().strftime("%Y-%m")

        if self.usage_file.exists():
            try:
                with open(self.usage_file, encoding="utf-8") as f:
                    data = json.load(f)

                # 月が変わっていたらリセット
                if data.get("month") != current_month:
                    self._usage = UsageRecord(month=current_month)
                    self._save_usage()
                else:
                    self._usage = UsageRecord(**data)
            except Exception:
                self._usage = UsageRecord(month=current_month)
        else:
            self._usage = UsageRecord(month=current_month)

        return self._usage

    def _save_usage(self) -> None:
        """利用量を保存"""
        if self._usage:
            self._usage.last_updated = datetime.now(timezone.utc).isoformat()
            with open(self.usage_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self._usage), f, indent=2)

    def check_review_limit(self, file_lines: int = 0) -> bool:
        """レビュー制限をチェック

        Args:
            file_lines: ファイルの行数

        Returns:
            bool: 制限内ならTrue

        Raises:
            UsageLimitError: 制限を超えている場合
        """
        limits = self.get_limits()
        usage = self.get_usage()

        # 月間レビュー数チェック
        if limits.reviews_per_month != -1:
            if usage.reviews >= limits.reviews_per_month:
                raise UsageLimitError(
                    f"Monthly review limit reached: {usage.reviews}/"
                    f"{limits.reviews_per_month}. "
                    f"Upgrade to Pro for more reviews."
                )

        # ファイルサイズチェック
        if limits.max_file_lines != -1:
            if file_lines > limits.max_file_lines:
                raise UsageLimitError(
                    f"File too large: {file_lines} lines "
                    f"(max: {limits.max_file_lines}). "
                    f"Upgrade to Pro for larger files."
                )

        return True

    def check_testgen_limit(self) -> bool:
        """テスト生成制限をチェック"""
        limits = self.get_limits()
        usage = self.get_usage()

        if limits.testgen_per_month != -1:
            if usage.testgens >= limits.testgen_per_month:
                raise UsageLimitError(
                    f"Monthly test generation limit reached: {usage.testgens}/"
                    f"{limits.testgen_per_month}. "
                    f"Upgrade to Pro for more."
                )

        return True

    def check_fix_limit(self) -> bool:
        """バグ修正制限をチェック"""
        limits = self.get_limits()
        usage = self.get_usage()

        if limits.fix_per_month != -1:
            if usage.fixes >= limits.fix_per_month:
                raise UsageLimitError(
                    f"Monthly fix suggestion limit reached: {usage.fixes}/"
                    f"{limits.fix_per_month}. "
                    f"Upgrade to Pro for more."
                )

        return True

    def check_feature(self, feature: str) -> bool:
        """機能が利用可能かチェック

        Args:
            feature: 機能名（private_repos, github_integration, self_hosted等）

        Returns:
            bool: 利用可能ならTrue
        """
        limits = self.get_limits()
        return getattr(limits, feature, False)

    def record_review(self) -> None:
        """レビュー実行を記録"""
        usage = self.get_usage()
        usage.reviews += 1
        self._save_usage()

    def record_testgen(self) -> None:
        """テスト生成を記録"""
        usage = self.get_usage()
        usage.testgens += 1
        self._save_usage()

    def record_fix(self) -> None:
        """バグ修正提案を記録"""
        usage = self.get_usage()
        usage.fixes += 1
        self._save_usage()

    def get_usage_summary(self) -> dict:
        """利用状況サマリーを取得"""
        limits = self.get_limits()
        usage = self.get_usage()

        def format_limit(used: int, limit: int) -> str:
            if limit == -1:
                return f"{used} / unlimited"
            return f"{used} / {limit}"

        return {
            "plan": self.get_plan().value,
            "month": usage.month,
            "reviews": format_limit(usage.reviews, limits.reviews_per_month),
            "testgens": format_limit(usage.testgens, limits.testgen_per_month),
            "fixes": format_limit(usage.fixes, limits.fix_per_month),
            "max_file_lines": (
                "unlimited" if limits.max_file_lines == -1
                else str(limits.max_file_lines)
            ),
            "features": {
                "private_repos": limits.private_repos,
                "github_integration": limits.github_integration,
                "self_hosted": limits.self_hosted,
                "priority_support": limits.priority_support,
            },
        }

    def deactivate(self) -> None:
        """ライセンスを無効化"""
        if self.license_file.exists():
            self.license_file.unlink()
        self._license = None

    def reset_usage(self) -> None:
        """利用量をリセット（テスト用）"""
        current_month = datetime.now().strftime("%Y-%m")
        self._usage = UsageRecord(month=current_month)
        self._save_usage()


def generate_license_key(plan: Plan, identifier: str) -> str:
    """ライセンスキーを生成（サーバーサイド用）

    Args:
        plan: プラン
        identifier: ユーザー識別子（メールなど）

    Returns:
        str: ライセンスキー
    """
    # 識別子とタイムスタンプからハッシュを生成
    timestamp = str(int(time.time()))
    data = f"{identifier}:{timestamp}:{plan.value}"
    hash_value = hashlib.sha256(data.encode()).hexdigest()[:12]

    plan_code = {
        Plan.FREE: "FREE",
        Plan.PRO: "PRO",
        Plan.TEAM: "TEAM",
        Plan.ENTERPRISE: "ENT",
    }[plan]

    return f"DB-{plan_code}-{hash_value}"
