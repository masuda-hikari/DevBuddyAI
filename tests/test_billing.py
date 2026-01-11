"""
課金システムのテスト

billing.py の機能をテスト。
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from devbuddy.core.billing import (
    BillingClient,
    BillingError,
    BillingWebhookHandler,
    CheckoutSession,
    PaymentStatus,
    PriceInfo,
    PRICE_CONFIG,
    Subscription,
    WebhookVerificationError,
    get_all_prices,
    get_price_info,
)
from devbuddy.core.licensing import (
    LicenseManager,
    Plan,
)


class TestPriceInfo:
    """PriceInfo データクラスのテスト"""

    def test_price_config_has_pro(self):
        """Proプランの価格設定が存在する"""
        assert Plan.PRO in PRICE_CONFIG
        price = PRICE_CONFIG[Plan.PRO]
        assert price.amount == 1980
        assert price.currency == "jpy"
        assert price.interval == "month"

    def test_price_config_has_team(self):
        """Teamプランの価格設定が存在する"""
        assert Plan.TEAM in PRICE_CONFIG
        price = PRICE_CONFIG[Plan.TEAM]
        assert price.amount == 9800
        assert price.currency == "jpy"

    def test_price_config_has_enterprise(self):
        """Enterpriseプランの価格設定が存在する"""
        assert Plan.ENTERPRISE in PRICE_CONFIG
        price = PRICE_CONFIG[Plan.ENTERPRISE]
        assert price.amount == 0  # 要問い合わせ

    def test_get_price_info_pro(self):
        """get_price_info でProプラン情報取得"""
        info = get_price_info(Plan.PRO)
        assert info is not None
        assert info.plan == Plan.PRO
        assert info.display_name == "Pro プラン"

    def test_get_price_info_free_returns_none(self):
        """get_price_info でFreeプランはNone"""
        info = get_price_info(Plan.FREE)
        assert info is None

    def test_get_all_prices(self):
        """get_all_prices で全価格情報取得"""
        prices = get_all_prices()
        assert len(prices) == 3  # PRO, TEAM, ENTERPRISE
        assert all(isinstance(p, PriceInfo) for p in prices)


class TestPaymentStatus:
    """PaymentStatus enumのテスト"""

    def test_status_values(self):
        """ステータス値の確認"""
        assert PaymentStatus.PENDING.value == "pending"
        assert PaymentStatus.SUCCEEDED.value == "succeeded"
        assert PaymentStatus.FAILED.value == "failed"
        assert PaymentStatus.CANCELED.value == "canceled"
        assert PaymentStatus.REFUNDED.value == "refunded"


class TestCheckoutSession:
    """CheckoutSession データクラスのテスト"""

    def test_create_checkout_session(self):
        """CheckoutSession 作成"""
        session = CheckoutSession(
            session_id="cs_test_123",
            url="https://checkout.stripe.com/pay/cs_test_123",
            plan=Plan.PRO,
            email="test@example.com",
            status="open",
            created_at="2026-01-11T00:00:00Z",
        )

        assert session.session_id == "cs_test_123"
        assert session.plan == Plan.PRO
        assert session.email == "test@example.com"


class TestSubscription:
    """Subscription データクラスのテスト"""

    def test_create_subscription(self):
        """Subscription 作成"""
        now = datetime.now(timezone.utc)
        sub = Subscription(
            subscription_id="sub_test_123",
            customer_id="cus_test_456",
            plan=Plan.PRO,
            status="active",
            current_period_start=now,
            current_period_end=now,
            cancel_at_period_end=False,
        )

        assert sub.subscription_id == "sub_test_123"
        assert sub.plan == Plan.PRO
        assert sub.status == "active"
        assert not sub.cancel_at_period_end


class TestBillingClient:
    """BillingClient クラスのテスト"""

    def test_init_with_env_vars(self):
        """環境変数からの初期化"""
        env_vars = {
            "STRIPE_API_KEY": "sk_test_123",
            "STRIPE_WEBHOOK_SECRET": "whsec_123"
        }
        with patch.dict("os.environ", env_vars):
            client = BillingClient()
            assert client.api_key == "sk_test_123"
            assert client.webhook_secret == "whsec_123"

    def test_init_with_args(self):
        """引数からの初期化"""
        client = BillingClient(
            api_key="sk_test_456",
            webhook_secret="whsec_456",
        )
        assert client.api_key == "sk_test_456"
        assert client.webhook_secret == "whsec_456"

    def test_create_checkout_free_raises_error(self):
        """Freeプランでcheckout作成はエラー"""
        client = BillingClient(api_key="sk_test_123")

        with pytest.raises(BillingError, match="Free plan"):
            client.create_checkout_session(
                plan=Plan.FREE,
                email="test@example.com",
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel",
            )

    @patch("devbuddy.core.billing.BillingClient._get_stripe")
    def test_create_checkout_session_success(self, mock_get_stripe):
        """Checkout Session 作成成功"""
        mock_stripe = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "cs_test_123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_123"
        mock_session.status = "open"
        mock_stripe.checkout.Session.create.return_value = mock_session
        mock_get_stripe.return_value = mock_stripe

        client = BillingClient(api_key="sk_test_123")
        session = client.create_checkout_session(
            plan=Plan.PRO,
            email="test@example.com",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )

        assert session.session_id == "cs_test_123"
        assert session.plan == Plan.PRO

    def test_verify_webhook_no_secret(self):
        """Webhook検証でシークレットなしはエラー"""
        client = BillingClient(api_key="sk_test_123", webhook_secret="")

        with pytest.raises(WebhookVerificationError, match="not configured"):
            client.verify_webhook_signature(b"payload", "sig_123")

    @patch("devbuddy.core.billing.BillingClient._get_stripe")
    def test_get_subscription_success(self, mock_get_stripe):
        """サブスクリプション取得成功"""
        mock_stripe = MagicMock()
        mock_sub = MagicMock()
        mock_sub.id = "sub_test_123"
        mock_sub.customer = "cus_test_456"
        mock_sub.metadata = {"plan": "pro"}
        mock_sub.status = "active"
        mock_sub.current_period_start = 1704067200
        mock_sub.current_period_end = 1706745600
        mock_sub.cancel_at_period_end = False
        mock_stripe.Subscription.retrieve.return_value = mock_sub
        mock_get_stripe.return_value = mock_stripe

        client = BillingClient(api_key="sk_test_123")
        sub = client.get_subscription("sub_test_123")

        assert sub.subscription_id == "sub_test_123"
        assert sub.plan == Plan.PRO
        assert sub.status == "active"


class TestBillingWebhookHandler:
    """BillingWebhookHandler クラスのテスト"""

    @pytest.fixture
    def handler(self, tmp_path):
        """テスト用ハンドラー"""
        billing_client = BillingClient(api_key="sk_test_123")
        license_manager = LicenseManager(data_dir=tmp_path)
        return BillingWebhookHandler(billing_client, license_manager)

    def test_handle_unknown_event(self, handler):
        """未知のイベントは無視"""
        event = {"type": "unknown.event", "data": {"object": {}}}
        result = handler.handle_event(event)
        assert result["status"] == "ignored"

    def test_handle_checkout_completed(self, handler):
        """checkout.session.completedの処理"""
        event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer_email": "test@example.com",
                    "metadata": {"plan": "pro", "email": "test@example.com"},
                }
            },
        }

        result = handler.handle_event(event)

        assert result["status"] == "success"
        assert result["action"] == "license_activated"
        assert result["plan"] == "pro"

        # ライセンスがアクティベートされたことを確認
        license_info = handler.license_manager.get_license()
        assert license_info is not None
        assert license_info.plan == Plan.PRO

    def test_handle_subscription_created(self, handler):
        """customer.subscription.createdの処理"""
        event = {
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "customer_email": "test@example.com",
                    "metadata": {"plan": "team"},
                    "status": "active",
                }
            },
        }

        result = handler.handle_event(event)

        assert result["status"] == "success"
        assert result["action"] == "subscription_created"

    def test_handle_subscription_deleted(self, handler):
        """customer.subscription.deletedの処理"""
        # まずライセンスをアクティベート
        handler.license_manager.activate("DB-PRO-abc123", "test@example.com")

        event = {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_test_123",
                }
            },
        }

        result = handler.handle_event(event)

        assert result["status"] == "success"
        assert result["action"] == "license_deactivated"

        # ライセンスが無効化されたことを確認
        license_info = handler.license_manager.get_license()
        assert license_info is None

    def test_handle_payment_succeeded(self, handler):
        """invoice.payment_succeededの処理"""
        event = {
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "subscription": "sub_test_123",
                }
            },
        }

        result = handler.handle_event(event)

        assert result["status"] == "success"
        assert result["action"] == "payment_recorded"

    def test_handle_payment_failed_first_attempt(self, handler):
        """invoice.payment_failedの処理（1回目）"""
        event = {
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "subscription": "sub_test_123",
                    "attempt_count": 1,
                }
            },
        }

        result = handler.handle_event(event)

        assert result["status"] == "warning"
        assert result["action"] == "payment_retry_pending"

    def test_handle_payment_failed_third_attempt(self, handler):
        """invoice.payment_failedの処理（3回目 → ライセンス停止）"""
        # まずライセンスをアクティベート
        handler.license_manager.activate("DB-PRO-abc123", "test@example.com")

        event = {
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "subscription": "sub_test_123",
                    "attempt_count": 3,
                }
            },
        }

        result = handler.handle_event(event)

        assert result["status"] == "warning"
        assert result["action"] == "license_suspended"

        # ライセンスが無効化されたことを確認
        license_info = handler.license_manager.get_license()
        assert license_info is None

    def test_handle_subscription_updated_active(self, handler):
        """subscription.updatedでactiveの処理"""
        event = {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "status": "active",
                    "metadata": {"plan": "team", "email": "test@example.com"},
                }
            },
        }

        result = handler.handle_event(event)

        assert result["status"] == "success"
        assert result["action"] == "subscription_updated"

    def test_handle_subscription_updated_canceled(self, handler):
        """subscription.updatedでcanceledの処理"""
        # まずライセンスをアクティベート
        handler.license_manager.activate("DB-PRO-abc123", "test@example.com")

        event = {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "status": "canceled",
                    "metadata": {"plan": "pro", "email": "test@example.com"},
                }
            },
        }

        result = handler.handle_event(event)

        assert result["status"] == "success"
        assert result["action"] == "subscription_updated"

        # ライセンスが無効化されたことを確認
        license_info = handler.license_manager.get_license()
        assert license_info is None


class TestBillingErrors:
    """エラークラスのテスト"""

    def test_billing_error(self):
        """BillingError"""
        error = BillingError("Test error")
        assert str(error) == "Test error"

    def test_webhook_verification_error(self):
        """WebhookVerificationError"""
        error = WebhookVerificationError("Invalid signature")
        assert str(error) == "Invalid signature"
        assert isinstance(error, BillingError)


class TestBillingIntegration:
    """統合テスト"""

    def test_full_checkout_flow_mock(self, tmp_path):
        """チェックアウトフロー全体のモックテスト"""
        # 1. BillingClient セットアップ
        billing_client = BillingClient(api_key="sk_test_123")
        license_manager = LicenseManager(data_dir=tmp_path)
        handler = BillingWebhookHandler(billing_client, license_manager)

        # 2. Checkout完了イベントを処理
        checkout_event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer_email": "customer@example.com",
                    "metadata": {
                        "plan": "pro",
                        "email": "customer@example.com"
                    },
                }
            },
        }

        result = handler.handle_event(checkout_event)

        # 3. ライセンスがアクティベートされたことを確認
        assert result["status"] == "success"
        license_info = license_manager.get_license()
        assert license_info is not None
        assert license_info.plan == Plan.PRO

        # 4. 支払い成功イベント
        payment_event = {
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "subscription": "sub_test_123",
                }
            },
        }
        result = handler.handle_event(payment_event)
        assert result["status"] == "success"

        # 5. サブスクリプション更新（active維持）
        update_event = {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "status": "active",
                    "metadata": {
                        "plan": "pro",
                        "email": "customer@example.com"
                    },
                }
            },
        }
        result = handler.handle_event(update_event)
        assert result["status"] == "success"

        # ライセンスは引き続き有効
        license_info = license_manager.get_license()
        assert license_info is not None
        assert license_info.plan == Plan.PRO

    def test_cancellation_flow_mock(self, tmp_path):
        """キャンセルフロー全体のモックテスト"""
        billing_client = BillingClient(api_key="sk_test_123")
        license_manager = LicenseManager(data_dir=tmp_path)
        handler = BillingWebhookHandler(billing_client, license_manager)

        # 1. まずライセンスをアクティベート
        license_manager.activate("DB-TEAM-abc123", "customer@example.com")
        assert license_manager.get_license().plan == Plan.TEAM

        # 2. サブスクリプション削除イベント
        delete_event = {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_test_123",
                }
            },
        }

        result = handler.handle_event(delete_event)

        # 3. ライセンスが無効化されたことを確認
        assert result["status"] == "success"
        assert license_manager.get_license() is None
        assert license_manager.get_plan() == Plan.FREE
