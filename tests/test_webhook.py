"""
Webhookサーバーのテスト
"""

from unittest.mock import MagicMock, patch

import pytest


def _can_import_fastapi() -> bool:
    """FastAPIがインポート可能かチェック"""
    try:
        import fastapi  # noqa: F401
        return True
    except ImportError:
        return False


class TestWebhookConfig:
    """WebhookConfig テスト"""

    def test_default_config(self) -> None:
        """デフォルト設定が正しいことを確認"""
        from devbuddy.server.webhook import WebhookConfig

        config = WebhookConfig()
        assert config.stripe_api_key == ""
        assert config.stripe_webhook_secret == ""
        assert config.license_file == ".devbuddy_license"
        assert config.log_level == "INFO"
        assert config.allowed_origins == ["*"]
        assert config.host == "0.0.0.0"
        assert config.port == 8000

    def test_from_env(self) -> None:
        """環境変数から設定を読み込めることを確認"""
        from devbuddy.server.webhook import WebhookConfig

        with patch.dict("os.environ", {
            "STRIPE_API_KEY": "sk_test_xxx",
            "STRIPE_WEBHOOK_SECRET": "whsec_xxx",
            "DEVBUDDY_LICENSE_FILE": "/tmp/license",
            "DEVBUDDY_LOG_LEVEL": "DEBUG",
            "DEVBUDDY_ALLOWED_ORIGINS": "https://example.com,https://test.com",
            "DEVBUDDY_HOST": "127.0.0.1",
            "DEVBUDDY_PORT": "9000",
        }):
            config = WebhookConfig.from_env()
            assert config.stripe_api_key == "sk_test_xxx"
            assert config.stripe_webhook_secret == "whsec_xxx"
            assert config.license_file == "/tmp/license"
            assert config.log_level == "DEBUG"
            assert config.allowed_origins == [
                "https://example.com", "https://test.com"
            ]
            assert config.host == "127.0.0.1"
            assert config.port == 9000


class TestWebhookServer:
    """WebhookServer テスト"""

    def test_init_default(self) -> None:
        """デフォルト設定で初期化できることを確認"""
        from devbuddy.server.webhook import WebhookServer

        server = WebhookServer()
        assert server.config is not None
        assert server._app is None
        assert server._billing_client is None

    def test_init_with_config(self) -> None:
        """カスタム設定で初期化できることを確認"""
        from devbuddy.server.webhook import WebhookConfig, WebhookServer

        config = WebhookConfig(
            stripe_api_key="test_key",
            port=9999,
        )
        server = WebhookServer(config)
        assert server.config.stripe_api_key == "test_key"
        assert server.config.port == 9999


class TestCreateApp:
    """create_app テスト"""

    @pytest.fixture
    def mock_billing_client(self) -> MagicMock:
        """モックBillingClientを作成"""
        return MagicMock()

    @pytest.fixture
    def mock_webhook_handler(self) -> MagicMock:
        """モックWebhookHandlerを作成"""
        return MagicMock()

    @pytest.mark.skipif(
        not _can_import_fastapi(),
        reason="FastAPI not installed"
    )
    def test_create_app_success(
        self,
        mock_billing_client: MagicMock,
        mock_webhook_handler: MagicMock,
    ) -> None:
        """正常にアプリを作成できることを確認"""
        from devbuddy.server.webhook import create_app, WebhookConfig

        config = WebhookConfig(
            stripe_api_key="test_key",
            stripe_webhook_secret="test_secret",
        )

        app = create_app(
            billing_client=mock_billing_client,
            webhook_handler=mock_webhook_handler,
            config=config,
        )

        assert app is not None
        assert app.title == "DevBuddyAI Webhook Server"


# FastAPIがインストールされている場合のみ実行するテスト
@pytest.mark.skipif(not _can_import_fastapi(), reason="FastAPI not installed")
class TestEndpoints:
    """エンドポイントテスト"""

    @pytest.fixture
    def client(self):  # type: ignore[no-untyped-def]
        """テストクライアントを作成"""
        from fastapi.testclient import TestClient
        from devbuddy.server.webhook import create_app, WebhookConfig

        # モッククライアントを設定
        mock_billing = MagicMock()
        mock_handler = MagicMock()

        config = WebhookConfig(
            stripe_api_key="test_key",
            stripe_webhook_secret="test_secret",
        )

        app = create_app(
            billing_client=mock_billing,
            webhook_handler=mock_handler,
            config=config,
        )

        return TestClient(app)

    # type: ignore[no-untyped-def]
    def test_health_check(self, client) -> None:
        """ヘルスチェックエンドポイント"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "devbuddy-webhook"
        assert data["version"] == "0.1.0"

    def test_get_prices(self, client) -> None:  # type: ignore[no-untyped-def]
        """価格一覧取得エンドポイント"""
        response = client.get("/api/v1/prices")
        assert response.status_code == 200
        data = response.json()
        assert "prices" in data
        assert len(data["prices"]) > 0

        # 各価格情報の構造を確認
        for price in data["prices"]:
            assert "plan" in price
            assert "price_id" in price
            assert "amount" in price
            assert "currency" in price
            assert "interval" in price
            assert "display_name" in price

    # type: ignore[no-untyped-def]
    def test_get_price_by_plan_pro(self, client) -> None:
        """Proプラン価格取得"""
        response = client.get("/api/v1/prices/pro")
        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "pro"
        assert data["amount"] == 1980
        assert data["currency"] == "jpy"

    # type: ignore[no-untyped-def]
    def test_get_price_by_plan_team(self, client) -> None:
        """Teamプラン価格取得"""
        response = client.get("/api/v1/prices/team")
        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "team"
        assert data["amount"] == 9800
        assert data["currency"] == "jpy"

    def test_get_price_by_plan_not_found(
        self, client  # type: ignore[no-untyped-def]
    ) -> None:
        """存在しないプランの価格取得"""
        response = client.get("/api/v1/prices/invalid")
        assert response.status_code == 404

    # type: ignore[no-untyped-def]
    def test_get_price_free_plan(self, client) -> None:
        """Freeプランの価格取得（存在しない）"""
        response = client.get("/api/v1/prices/free")
        assert response.status_code == 404

    def test_create_checkout_missing_fields(
        self, client  # type: ignore[no-untyped-def]
    ) -> None:
        """Checkout作成時の必須フィールド不足"""
        response = client.post(
            "/api/v1/checkout/create",
            json={"plan": "pro"},
        )
        assert response.status_code == 400
        assert "Missing" in response.json()["detail"]

    def test_create_checkout_invalid_plan(
        self, client  # type: ignore[no-untyped-def]
    ) -> None:
        """Checkout作成時の無効なプラン"""
        response = client.post(
            "/api/v1/checkout/create",
            json={
                "plan": "invalid",
                "email": "test@example.com",
                "success_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel",
            },
        )
        assert response.status_code == 400
        assert "Invalid plan" in response.json()["detail"]

    def test_create_checkout_free_plan(
        self, client  # type: ignore[no-untyped-def]
    ) -> None:
        """Checkout作成時のFreeプラン"""
        response = client.post(
            "/api/v1/checkout/create",
            json={
                "plan": "free",
                "email": "test@example.com",
                "success_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel",
            },
        )
        assert response.status_code == 400
        assert "Free plan" in response.json()["detail"]

    def test_stripe_webhook_missing_signature(
        self, client  # type: ignore[no-untyped-def]
    ) -> None:
        """Webhook署名ヘッダー不足"""
        response = client.post(
            "/api/v1/webhook/stripe",
            content=b"{}",
        )
        assert response.status_code == 400
        assert "Missing Stripe-Signature" in response.json()["detail"]

    def test_subscription_cancel_missing_id(
        self, client  # type: ignore[no-untyped-def]
    ) -> None:
        """サブスクリプションキャンセル時のID不足"""
        response = client.post(
            "/api/v1/subscription/cancel",
            json={},
        )
        assert response.status_code == 400
        assert "Missing subscription_id" in response.json()["detail"]

    def test_invalid_json_checkout(
        self, client  # type: ignore[no-untyped-def]
    ) -> None:
        """無効なJSON（Checkout）"""
        response = client.post(
            "/api/v1/checkout/create",
            content=b"invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

    def test_invalid_json_cancel(
        self, client  # type: ignore[no-untyped-def]
    ) -> None:
        """無効なJSON（キャンセル）"""
        response = client.post(
            "/api/v1/subscription/cancel",
            content=b"invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400


class TestWebhookIntegration:
    """Webhook統合テスト（モック使用）"""

    def test_webhook_handler_checkout_completed(self) -> None:
        """Checkout完了イベントの処理"""
        from devbuddy.core.billing import BillingWebhookHandler, BillingClient
        from devbuddy.core.licensing import LicenseManager

        mock_billing = MagicMock(spec=BillingClient)
        mock_license = MagicMock(spec=LicenseManager)

        handler = BillingWebhookHandler(
            billing_client=mock_billing,
            license_manager=mock_license,
        )

        event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer_email": "test@example.com",
                    "metadata": {"plan": "pro"},
                }
            }
        }

        result = handler.handle_event(event)
        assert result["status"] == "success"
        assert result["action"] == "license_activated"
        assert mock_license.activate.called

    def test_webhook_handler_subscription_deleted(self) -> None:
        """サブスクリプション削除イベントの処理"""
        from devbuddy.core.billing import BillingWebhookHandler, BillingClient
        from devbuddy.core.licensing import LicenseManager

        mock_billing = MagicMock(spec=BillingClient)
        mock_license = MagicMock(spec=LicenseManager)

        handler = BillingWebhookHandler(
            billing_client=mock_billing,
            license_manager=mock_license,
        )

        event = {
            "type": "customer.subscription.deleted",
            "data": {"object": {}}
        }

        result = handler.handle_event(event)
        assert result["status"] == "success"
        assert result["action"] == "license_deactivated"
        assert mock_license.deactivate.called

    def test_webhook_handler_payment_failed_multiple(self) -> None:
        """支払い失敗（3回）でライセンス停止"""
        from devbuddy.core.billing import BillingWebhookHandler, BillingClient
        from devbuddy.core.licensing import LicenseManager

        mock_billing = MagicMock(spec=BillingClient)
        mock_license = MagicMock(spec=LicenseManager)

        handler = BillingWebhookHandler(
            billing_client=mock_billing,
            license_manager=mock_license,
        )

        event = {
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "attempt_count": 3,
                    "subscription": "sub_test",
                }
            }
        }

        result = handler.handle_event(event)
        assert result["status"] == "warning"
        assert result["action"] == "license_suspended"
        assert mock_license.deactivate.called

    def test_webhook_handler_unknown_event(self) -> None:
        """未知のイベントタイプの処理"""
        from devbuddy.core.billing import BillingWebhookHandler, BillingClient
        from devbuddy.core.licensing import LicenseManager

        mock_billing = MagicMock(spec=BillingClient)
        mock_license = MagicMock(spec=LicenseManager)

        handler = BillingWebhookHandler(
            billing_client=mock_billing,
            license_manager=mock_license,
        )

        event = {
            "type": "unknown.event.type",
            "data": {"object": {}}
        }

        result = handler.handle_event(event)
        assert result["status"] == "ignored"
        assert result["event_type"] == "unknown.event.type"
