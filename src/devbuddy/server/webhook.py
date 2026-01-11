"""
Stripe Webhook エンドポイント

FastAPIを使用したWebhookサーバー実装。
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ..core.billing import (
    BillingClient,
    BillingWebhookHandler,
    WebhookVerificationError,
    get_all_prices,
    get_price_info,
)
from ..core.licensing import LicenseManager, Plan

logger = logging.getLogger(__name__)


@dataclass
class WebhookConfig:
    """Webhookサーバー設定"""
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""
    license_file: str = ".devbuddy_license"
    log_level: str = "INFO"
    allowed_origins: list[str] = field(default_factory=lambda: ["*"])
    host: str = "0.0.0.0"
    port: int = 8000

    @classmethod
    def from_env(cls) -> "WebhookConfig":
        """環境変数から設定を読み込み"""
        return cls(
            stripe_api_key=os.environ.get("STRIPE_API_KEY", ""),
            stripe_webhook_secret=os.environ.get("STRIPE_WEBHOOK_SECRET", ""),
            license_file=os.environ.get(
                "DEVBUDDY_LICENSE_FILE", ".devbuddy_license"
            ),
            log_level=os.environ.get("DEVBUDDY_LOG_LEVEL", "INFO"),
            allowed_origins=os.environ.get(
                "DEVBUDDY_ALLOWED_ORIGINS", "*"
            ).split(","),
            host=os.environ.get("DEVBUDDY_HOST", "0.0.0.0"),
            port=int(os.environ.get("DEVBUDDY_PORT", "8000")),
        )


class WebhookServer:
    """Webhookサーバークラス

    FastAPIアプリケーションのライフサイクル管理。
    """

    def __init__(self, config: Optional[WebhookConfig] = None):
        self.config = config or WebhookConfig.from_env()
        self._app: Any = None
        self._billing_client: Optional[BillingClient] = None
        self._webhook_handler: Optional[BillingWebhookHandler] = None

    @property
    def billing_client(self) -> BillingClient:
        """BillingClientを取得（遅延初期化）"""
        if self._billing_client is None:
            self._billing_client = BillingClient(
                api_key=self.config.stripe_api_key,
                webhook_secret=self.config.stripe_webhook_secret,
            )
        return self._billing_client

    @property
    def webhook_handler(self) -> BillingWebhookHandler:
        """WebhookHandlerを取得（遅延初期化）"""
        if self._webhook_handler is None:
            license_manager = LicenseManager(Path(self.config.license_file))
            self._webhook_handler = BillingWebhookHandler(
                billing_client=self.billing_client,
                license_manager=license_manager,
            )
        return self._webhook_handler

    @property
    def app(self) -> Any:
        """FastAPIアプリケーションを取得"""
        if self._app is None:
            self._app = create_app(
                billing_client=self.billing_client,
                webhook_handler=self.webhook_handler,
                config=self.config,
            )
        return self._app

    def run(self) -> None:
        """サーバーを起動"""
        try:
            import uvicorn
        except ImportError:
            raise RuntimeError(
                "uvicorn not installed. Run: pip install uvicorn"
            )

        uvicorn.run(
            self.app,
            host=self.config.host,
            port=self.config.port,
            log_level=self.config.log_level.lower(),
        )


def create_app(
    billing_client: Optional[BillingClient] = None,
    webhook_handler: Optional[BillingWebhookHandler] = None,
    config: Optional[WebhookConfig] = None,
) -> Any:
    """FastAPIアプリケーションを作成

    Args:
        billing_client: BillingClient インスタンス
        webhook_handler: BillingWebhookHandler インスタンス
        config: WebhookConfig 設定

    Returns:
        FastAPI: アプリケーションインスタンス
    """
    try:
        from fastapi import FastAPI, Request, HTTPException, Header
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import JSONResponse
    except ImportError:
        raise RuntimeError(
            "fastapi not installed. Run: pip install fastapi uvicorn"
        )

    config = config or WebhookConfig.from_env()

    # デフォルトのクライアント初期化
    if billing_client is None:
        billing_client = BillingClient(
            api_key=config.stripe_api_key,
            webhook_secret=config.stripe_webhook_secret,
        )

    if webhook_handler is None:
        license_manager = LicenseManager(Path(config.license_file))
        webhook_handler = BillingWebhookHandler(
            billing_client=billing_client,
            license_manager=license_manager,
        )

    # FastAPIアプリケーション作成
    app = FastAPI(
        title="DevBuddyAI Webhook Server",
        description="Stripe Webhook および課金関連エンドポイント",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ヘルスチェックエンドポイント
    @app.get("/health")
    async def health_check() -> dict:
        """ヘルスチェック"""
        return {
            "status": "healthy",
            "service": "devbuddy-webhook",
            "version": "0.1.0",
        }

    # 価格情報エンドポイント
    @app.get("/api/v1/prices")
    async def get_prices() -> dict:
        """利用可能なプラン価格を取得"""
        prices = get_all_prices()
        return {
            "prices": [
                {
                    "plan": p.plan.value,
                    "price_id": p.price_id,
                    "amount": p.amount,
                    "currency": p.currency,
                    "interval": p.interval,
                    "display_name": p.display_name,
                }
                for p in prices
            ]
        }

    @app.get("/api/v1/prices/{plan}")
    async def get_price_by_plan(plan: str) -> dict:
        """特定プランの価格情報を取得"""
        try:
            plan_enum = Plan(plan)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Plan not found: {plan}")

        price_info = get_price_info(plan_enum)
        if price_info is None:
            raise HTTPException(status_code=404, detail="Price not available")

        return {
            "plan": price_info.plan.value,
            "price_id": price_info.price_id,
            "amount": price_info.amount,
            "currency": price_info.currency,
            "interval": price_info.interval,
            "display_name": price_info.display_name,
        }

    # Checkout Session作成エンドポイント
    @app.post("/api/v1/checkout/create")
    async def create_checkout(request: Request) -> dict:
        """Checkout Sessionを作成"""
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON")

        plan_str = body.get("plan", "")
        email = body.get("email", "")
        success_url = body.get("success_url", "")
        cancel_url = body.get("cancel_url", "")

        if not all([plan_str, email, success_url, cancel_url]):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: plan, email, success_url, cancel_url"
            )

        try:
            plan = Plan(plan_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid plan: {plan_str}")

        if plan == Plan.FREE:
            raise HTTPException(
                status_code=400,
                detail="Free plan does not require payment"
            )

        try:
            session = billing_client.create_checkout_session(
                plan=plan,
                email=email,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=body.get("metadata"),
            )
            return {
                "session_id": session.session_id,
                "url": session.url,
                "plan": session.plan.value,
                "status": session.status,
            }
        except Exception as e:
            logger.error(f"Checkout creation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Stripe Webhook エンドポイント
    @app.post("/api/v1/webhook/stripe")
    async def stripe_webhook(
        request: Request,
        stripe_signature: str = Header(None, alias="Stripe-Signature"),
    ) -> dict:
        """Stripe Webhookを処理"""
        if not stripe_signature:
            raise HTTPException(
                status_code=400,
                detail="Missing Stripe-Signature header"
            )

        # リクエストボディを取得
        try:
            payload = await request.body()
        except Exception as e:
            logger.error(f"Failed to read request body: {e}")
            raise HTTPException(status_code=400, detail="Invalid request body")

        # 署名検証
        try:
            event = billing_client.verify_webhook_signature(
                payload=payload,
                signature=stripe_signature,
            )
        except WebhookVerificationError as e:
            logger.warning(f"Webhook verification failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

        # イベント処理
        try:
            result = webhook_handler.handle_event(event)
            logger.info(
                f"Webhook processed: {event.get('type')} -> {result.get('action')}"
            )
            return result
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # サブスクリプションキャンセルエンドポイント
    @app.post("/api/v1/subscription/cancel")
    async def cancel_subscription(request: Request) -> dict:
        """サブスクリプションをキャンセル"""
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON")

        subscription_id = body.get("subscription_id", "")
        at_period_end = body.get("at_period_end", True)

        if not subscription_id:
            raise HTTPException(
                status_code=400,
                detail="Missing subscription_id"
            )

        try:
            sub = billing_client.cancel_subscription(
                subscription_id=subscription_id,
                at_period_end=at_period_end,
            )
            return {
                "subscription_id": sub.subscription_id,
                "status": sub.status,
                "cancel_at_period_end": sub.cancel_at_period_end,
                "current_period_end": sub.current_period_end.isoformat(),
            }
        except Exception as e:
            logger.error(f"Subscription cancel failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # サブスクリプション情報取得エンドポイント
    @app.get("/api/v1/subscription/{subscription_id}")
    async def get_subscription(subscription_id: str) -> dict:
        """サブスクリプション情報を取得"""
        try:
            sub = billing_client.get_subscription(subscription_id)
            return {
                "subscription_id": sub.subscription_id,
                "customer_id": sub.customer_id,
                "plan": sub.plan.value,
                "status": sub.status,
                "current_period_start": sub.current_period_start.isoformat(),
                "current_period_end": sub.current_period_end.isoformat(),
                "cancel_at_period_end": sub.cancel_at_period_end,
            }
        except Exception as e:
            logger.error(f"Get subscription failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # エラーハンドラー
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """グローバルエラーハンドラー"""
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app


def run_server(config: Optional[WebhookConfig] = None) -> None:
    """サーバーを起動（コマンドライン用）

    Args:
        config: WebhookConfig 設定
    """
    server = WebhookServer(config)
    server.run()
