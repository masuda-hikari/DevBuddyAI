"""
ライセンス・認証システムのテスト
"""

import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from devbuddy.core.licensing import (
    Plan,
    PLAN_LIMITS,
    License,
    LicenseError,
    UsageLimitError,
    LicenseManager,
    generate_license_key,
)


class TestPlan:
    """Planのテスト"""

    def test_plan_values(self):
        """プラン値が正しいこと"""
        assert Plan.FREE.value == "free"
        assert Plan.PRO.value == "pro"
        assert Plan.TEAM.value == "team"
        assert Plan.ENTERPRISE.value == "enterprise"

    def test_plan_limits_exist(self):
        """全プランの制限が定義されていること"""
        for plan in Plan:
            assert plan in PLAN_LIMITS


class TestPlanLimits:
    """PlanLimitsのテスト"""

    def test_free_limits(self):
        """Freeプランの制限が正しいこと"""
        limits = PLAN_LIMITS[Plan.FREE]
        assert limits.reviews_per_month == 50
        assert limits.max_file_lines == 500
        assert limits.private_repos is False
        assert limits.github_integration is False
        assert limits.testgen_per_month == 20
        assert limits.fix_per_month == 10

    def test_pro_limits(self):
        """Proプランの制限が正しいこと"""
        limits = PLAN_LIMITS[Plan.PRO]
        assert limits.reviews_per_month == 500
        assert limits.max_file_lines == 2000
        assert limits.private_repos is True
        assert limits.github_integration is True

    def test_team_unlimited(self):
        """Teamプランが無制限であること"""
        limits = PLAN_LIMITS[Plan.TEAM]
        assert limits.reviews_per_month == -1  # 無制限
        assert limits.max_file_lines == -1

    def test_enterprise_features(self):
        """Enterpriseプランの機能が正しいこと"""
        limits = PLAN_LIMITS[Plan.ENTERPRISE]
        assert limits.self_hosted is True
        assert limits.priority_support is True


class TestLicense:
    """Licenseのテスト"""

    def test_license_not_expired(self):
        """期限切れでないライセンス"""
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        license_info = License(
            license_key="DB-PRO-test123",
            plan=Plan.PRO,
            email="test@example.com",
            expires_at=future,
        )
        assert license_info.is_expired() is False

    def test_license_expired(self):
        """期限切れライセンス"""
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        license_info = License(
            license_key="DB-PRO-test123",
            plan=Plan.PRO,
            email="test@example.com",
            expires_at=past,
        )
        assert license_info.is_expired() is True

    def test_license_no_expiry(self):
        """期限なしライセンス（永久ライセンス）"""
        license_info = License(
            license_key="DB-PRO-test123",
            plan=Plan.PRO,
            email="test@example.com",
            expires_at=None,
        )
        assert license_info.is_expired() is False

    def test_get_limits(self):
        """ライセンスから制限を取得"""
        license_info = License(
            license_key="DB-PRO-test123",
            plan=Plan.PRO,
            email="test@example.com",
        )
        limits = license_info.get_limits()
        assert limits.reviews_per_month == 500


class TestLicenseManager:
    """LicenseManagerのテスト"""

    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_default_plan_is_free(self, temp_dir):
        """デフォルトはFreeプラン"""
        manager = LicenseManager(data_dir=temp_dir)
        assert manager.get_plan() == Plan.FREE

    def test_activate_pro_license(self, temp_dir):
        """Proライセンスのアクティベート"""
        manager = LicenseManager(data_dir=temp_dir)
        license_info = manager.activate("DB-PRO-test123", "test@example.com")

        assert license_info.plan == Plan.PRO
        assert license_info.email == "test@example.com"
        assert manager.get_plan() == Plan.PRO

    def test_activate_team_license(self, temp_dir):
        """Teamライセンスのアクティベート"""
        manager = LicenseManager(data_dir=temp_dir)
        license_info = manager.activate("DB-TEAM-test456", "team@example.com")

        assert license_info.plan == Plan.TEAM

    def test_activate_enterprise_license(self, temp_dir):
        """Enterpriseライセンスのアクティベート"""
        manager = LicenseManager(data_dir=temp_dir)
        license_info = manager.activate("DB-ENT-test789", "ent@example.com")

        assert license_info.plan == Plan.ENTERPRISE

    def test_invalid_license_key_format(self, temp_dir):
        """無効なライセンスキー形式"""
        manager = LicenseManager(data_dir=temp_dir)

        with pytest.raises(LicenseError, match="Invalid license key format"):
            manager.activate("INVALID-KEY", "test@example.com")

    def test_invalid_plan_code(self, temp_dir):
        """未知のプランコード"""
        manager = LicenseManager(data_dir=temp_dir)

        with pytest.raises(LicenseError, match="Unknown plan"):
            manager.activate("DB-UNKNOWN-test123", "test@example.com")

    def test_license_persistence(self, temp_dir):
        """ライセンス情報が永続化されること"""
        # 最初のマネージャーでアクティベート
        manager1 = LicenseManager(data_dir=temp_dir)
        manager1.activate("DB-PRO-test123", "test@example.com")

        # 新しいマネージャーで読み込み
        manager2 = LicenseManager(data_dir=temp_dir)
        license_info = manager2.get_license()

        assert license_info is not None
        assert license_info.plan == Plan.PRO
        assert license_info.email == "test@example.com"

    def test_deactivate_license(self, temp_dir):
        """ライセンスの無効化"""
        manager = LicenseManager(data_dir=temp_dir)
        manager.activate("DB-PRO-test123", "test@example.com")
        assert manager.get_plan() == Plan.PRO

        manager.deactivate()
        assert manager.get_plan() == Plan.FREE
        assert manager.get_license() is None


class TestUsageTracking:
    """利用量トラッキングのテスト"""

    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_initial_usage_is_zero(self, temp_dir):
        """初期利用量はゼロ"""
        manager = LicenseManager(data_dir=temp_dir)
        usage = manager.get_usage()

        assert usage.reviews == 0
        assert usage.testgens == 0
        assert usage.fixes == 0

    def test_record_review(self, temp_dir):
        """レビュー記録"""
        manager = LicenseManager(data_dir=temp_dir)
        manager.record_review()
        manager.record_review()

        usage = manager.get_usage()
        assert usage.reviews == 2

    def test_record_testgen(self, temp_dir):
        """テスト生成記録"""
        manager = LicenseManager(data_dir=temp_dir)
        manager.record_testgen()

        usage = manager.get_usage()
        assert usage.testgens == 1

    def test_record_fix(self, temp_dir):
        """修正提案記録"""
        manager = LicenseManager(data_dir=temp_dir)
        manager.record_fix()

        usage = manager.get_usage()
        assert usage.fixes == 1

    def test_usage_persistence(self, temp_dir):
        """利用量が永続化されること"""
        manager1 = LicenseManager(data_dir=temp_dir)
        manager1.record_review()
        manager1.record_review()
        manager1.record_testgen()

        # 新しいマネージャーで読み込み
        manager2 = LicenseManager(data_dir=temp_dir)
        usage = manager2.get_usage()

        assert usage.reviews == 2
        assert usage.testgens == 1

    def test_reset_usage(self, temp_dir):
        """利用量リセット"""
        manager = LicenseManager(data_dir=temp_dir)
        manager.record_review()
        manager.record_review()

        manager.reset_usage()
        usage = manager.get_usage()

        assert usage.reviews == 0

    def test_usage_summary(self, temp_dir):
        """利用状況サマリー"""
        manager = LicenseManager(data_dir=temp_dir)
        manager.record_review()
        manager.record_testgen()
        manager.record_fix()

        summary = manager.get_usage_summary()

        assert summary["plan"] == "free"
        assert "1 / 50" in summary["reviews"]
        assert "1 / 20" in summary["testgens"]
        assert "1 / 10" in summary["fixes"]


class TestUsageLimits:
    """利用制限のテスト"""

    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_check_review_limit_within(self, temp_dir):
        """制限内のレビュー"""
        manager = LicenseManager(data_dir=temp_dir)
        # Freeプラン: 50回/月
        for _ in range(10):
            assert manager.check_review_limit() is True
            manager.record_review()

    def test_check_review_limit_exceeded(self, temp_dir):
        """レビュー制限超過"""
        manager = LicenseManager(data_dir=temp_dir)
        # Freeプラン: 50回/月 → 超過させる
        usage = manager.get_usage()
        usage.reviews = 50
        manager._save_usage()

        with pytest.raises(UsageLimitError, match="Monthly review limit reached"):
            manager.check_review_limit()

    def test_check_file_size_within(self, temp_dir):
        """制限内のファイルサイズ"""
        manager = LicenseManager(data_dir=temp_dir)
        # Freeプラン: 500行まで
        assert manager.check_review_limit(file_lines=400) is True

    def test_check_file_size_exceeded(self, temp_dir):
        """ファイルサイズ制限超過"""
        manager = LicenseManager(data_dir=temp_dir)
        # Freeプラン: 500行まで

        with pytest.raises(UsageLimitError, match="File too large"):
            manager.check_review_limit(file_lines=600)

    def test_check_testgen_limit_exceeded(self, temp_dir):
        """テスト生成制限超過"""
        manager = LicenseManager(data_dir=temp_dir)
        usage = manager.get_usage()
        usage.testgens = 20  # Freeプランの制限
        manager._save_usage()

        with pytest.raises(UsageLimitError, match="Monthly test generation limit"):
            manager.check_testgen_limit()

    def test_check_fix_limit_exceeded(self, temp_dir):
        """修正提案制限超過"""
        manager = LicenseManager(data_dir=temp_dir)
        usage = manager.get_usage()
        usage.fixes = 10  # Freeプランの制限
        manager._save_usage()

        with pytest.raises(UsageLimitError, match="Monthly fix suggestion limit"):
            manager.check_fix_limit()

    def test_pro_plan_higher_limits(self, temp_dir):
        """Proプランはより高い制限"""
        manager = LicenseManager(data_dir=temp_dir)
        manager.activate("DB-PRO-test123", "test@example.com")

        # 500行を超えるファイルもOK
        assert manager.check_review_limit(file_lines=1000) is True

        # 2000行を超えるとNG
        with pytest.raises(UsageLimitError):
            manager.check_review_limit(file_lines=2500)

    def test_team_plan_unlimited(self, temp_dir):
        """Teamプランは無制限"""
        manager = LicenseManager(data_dir=temp_dir)
        manager.activate("DB-TEAM-test123", "test@example.com")

        # どんなに大きなファイルでもOK
        assert manager.check_review_limit(file_lines=100000) is True

        # どんなに多くの利用でもOK
        usage = manager.get_usage()
        usage.reviews = 10000
        manager._save_usage()

        assert manager.check_review_limit() is True


class TestFeatureCheck:
    """機能チェックのテスト"""

    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_free_no_private_repos(self, temp_dir):
        """Freeプランはプライベートリポジトリ不可"""
        manager = LicenseManager(data_dir=temp_dir)
        assert manager.check_feature("private_repos") is False

    def test_pro_has_private_repos(self, temp_dir):
        """Proプランはプライベートリポジトリ可"""
        manager = LicenseManager(data_dir=temp_dir)
        manager.activate("DB-PRO-test123", "test@example.com")
        assert manager.check_feature("private_repos") is True

    def test_free_no_github_integration(self, temp_dir):
        """Freeプランはプライベートリポジトリ不可"""
        manager = LicenseManager(data_dir=temp_dir)
        assert manager.check_feature("github_integration") is False

    def test_enterprise_has_self_hosted(self, temp_dir):
        """Enterpriseプランは自己ホスト可"""
        manager = LicenseManager(data_dir=temp_dir)
        manager.activate("DB-ENT-test123", "test@example.com")
        assert manager.check_feature("self_hosted") is True


class TestLicenseKeyGeneration:
    """ライセンスキー生成のテスト"""

    def test_generate_pro_key(self):
        """Proライセンスキー生成"""
        key = generate_license_key(Plan.PRO, "test@example.com")
        assert key.startswith("DB-PRO-")
        assert len(key) > len("DB-PRO-")

    def test_generate_team_key(self):
        """Teamライセンスキー生成"""
        key = generate_license_key(Plan.TEAM, "team@example.com")
        assert key.startswith("DB-TEAM-")

    def test_generate_enterprise_key(self):
        """Enterpriseライセンスキー生成"""
        key = generate_license_key(Plan.ENTERPRISE, "ent@example.com")
        assert key.startswith("DB-ENT-")

    def test_generated_key_is_valid(self):
        """生成されたキーが有効であること"""
        key = generate_license_key(Plan.PRO, "test@example.com")

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LicenseManager(data_dir=Path(tmpdir))
            license_info = manager.activate(key, "test@example.com")
            assert license_info.plan == Plan.PRO


class TestEnvironmentVariable:
    """環境変数からのライセンスキー取得テスト"""

    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_license_key_from_env(self, temp_dir):
        """環境変数からライセンスキーを取得"""
        with patch.dict(
            "os.environ", {"DEVBUDDY_LICENSE_KEY": "DB-PRO-envtest"}
        ):
            manager = LicenseManager(data_dir=temp_dir)
            assert manager.license_key == "DB-PRO-envtest"

    def test_explicit_key_overrides_env(self, temp_dir):
        """明示的なキーが環境変数より優先"""
        with patch.dict(
            "os.environ", {"DEVBUDDY_LICENSE_KEY": "DB-PRO-envtest"}
        ):
            manager = LicenseManager(
                data_dir=temp_dir,
                license_key="DB-TEAM-explicit"
            )
            assert manager.license_key == "DB-TEAM-explicit"
