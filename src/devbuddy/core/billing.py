"""
Stripe課金連携システム

サブスクリプション決済とライセンス管理を統合。
"""

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from .licensing import LicenseManager, Plan, generate_license_key


class BillingError(Exception):
    """課金エラー"""
    pass


class WebhookVerificationError(BillingError):
    """Webhook検証エラー"""
    pass


class PaymentStatus(Enum):
    """支払いステータス"""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"


@dataclass
class PriceInfo:
    """価格情報"""
    plan: Plan
    price_id: str  # Stripe Price ID
    amount: int  # 金額（円）
    currency: str
    interval: str  # month / year
    display_name: str


# 価格設定（日本円）
PRICE_CONFIG: dict[Plan, PriceInfo] = {
    Plan.PRO: PriceInfo(
        plan=Plan.PRO,
        price_id="price_pro_monthly",
        amount=1980,
        currency="jpy",
        interval="month",
        display_name="Pro プラン",
    ),
    Plan.TEAM: PriceInfo(
        plan=Plan.TEAM,
        price_id="price_team_monthly",
        amount=9800,
        currency="jpy",
        interval="month",
        display_name="Team プラン",
    ),
    Plan.ENTERPRISE: PriceInfo(
        plan=Plan.ENTERPRISE,
        price_id="price_enterprise_monthly",
        amount=0,  # 要問い合わせ
        currency="jpy",
        interval="month",
        display_name="Enterprise プラン",
    ),
}


@dataclass
class CheckoutSession:
    """Checkout Session情報"""
    session_id: str
    url: str
    plan: Plan
    email: str
    status: str
    created_at: str


@dataclass
class Subscription:
    """サブスクリプション情報"""
    subscription_id: str
    customer_id: str
    plan: Plan
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False


class BillingClient:
    """Stripe課金クライアント

    Stripe APIとの連携を管理。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        """
        Args:
            api_key: Stripe APIキー（環境変数: STRIPE_API_KEY）
            webhook_secret: Webhook署名シークレット（環境変数: STRIPE_WEBHOOK_SECRET）
        """
        self.api_key = api_key or os.environ.get("STRIPE_API_KEY", "")
        self.webhook_secret = webhook_secret or os.environ.get(
            "STRIPE_WEBHOOK_SECRET", ""
        )
        self._stripe = None

    def _get_stripe(self):  # type: ignore[no-untyped-def]
        """Stripeクライアントを取得（遅延初期化）"""
        if self._stripe is None:
            try:
                import stripe
                stripe.api_key = self.api_key
                self._stripe = stripe
            except ImportError:
                raise BillingError(
                    "stripe package not installed. "
                    "Run: pip install stripe"
                )
        return self._stripe

    def create_checkout_session(
        self,
        plan: Plan,
        email: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[dict] = None,
    ) -> CheckoutSession:
        """Checkout Sessionを作成

        Args:
            plan: 購入するプラン
            email: 顧客メールアドレス
            success_url: 成功時のリダイレクトURL
            cancel_url: キャンセル時のリダイレクトURL
            metadata: 追加メタデータ

        Returns:
            CheckoutSession: 作成されたセッション情報
        """
        if plan == Plan.FREE:
            raise BillingError("Free plan does not require payment")

        if plan not in PRICE_CONFIG:
            raise BillingError(f"Invalid plan: {plan.value}")

        price_info = PRICE_CONFIG[plan]
        stripe = self._get_stripe()

        session_metadata = {
            "plan": plan.value,
            "email": email,
        }
        if metadata:
            session_metadata.update(metadata)

        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                customer_email=email,
                line_items=[
                    {
                        "price": price_info.price_id,
                        "quantity": 1,
                    }
                ],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=session_metadata,
                subscription_data={
                    "metadata": session_metadata,
                },
            )

            return CheckoutSession(
                session_id=session.id,
                url=session.url,
                plan=plan,
                email=email,
                status=session.status,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            raise BillingError(f"Failed to create checkout session: {e}")

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> dict:
        """Webhook署名を検証

        Args:
            payload: リクエストボディ
            signature: Stripe-Signature ヘッダー

        Returns:
            dict: 検証済みイベントデータ

        Raises:
            WebhookVerificationError: 署名検証失敗
        """
        if not self.webhook_secret:
            raise WebhookVerificationError("Webhook secret not configured")

        stripe = self._get_stripe()

        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret,
            )
            return dict(event)  # type: ignore[arg-type]
        except stripe.error.SignatureVerificationError as e:
            raise WebhookVerificationError(f"Invalid signature: {e}")
        except Exception as e:
            raise WebhookVerificationError(f"Webhook verification failed: {e}")

    def get_subscription(self, subscription_id: str) -> Subscription:
        """サブスクリプション情報を取得

        Args:
            subscription_id: Stripe Subscription ID

        Returns:
            Subscription: サブスクリプション情報
        """
        stripe = self._get_stripe()

        try:
            sub = stripe.Subscription.retrieve(subscription_id)

            # メタデータからプランを取得
            plan_value = sub.metadata.get("plan", "pro")
            plan = Plan(plan_value)

            return Subscription(
                subscription_id=sub.id,
                customer_id=sub.customer,
                plan=plan,
                status=sub.status,
                current_period_start=datetime.fromtimestamp(
                    sub.current_period_start, tz=timezone.utc
                ),
                current_period_end=datetime.fromtimestamp(
                    sub.current_period_end, tz=timezone.utc
                ),
                cancel_at_period_end=sub.cancel_at_period_end,
            )
        except Exception as e:
            raise BillingError(f"Failed to get subscription: {e}")

    def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True,
    ) -> Subscription:
        """サブスクリプションをキャンセル

        Args:
            subscription_id: Stripe Subscription ID
            at_period_end: 期間終了時にキャンセル（True）/ 即座にキャンセル（False）

        Returns:
            Subscription: 更新されたサブスクリプション情報
        """
        stripe = self._get_stripe()

        try:
            if at_period_end:
                sub = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                )
            else:
                sub = stripe.Subscription.cancel(subscription_id)

            plan_value = sub.metadata.get("plan", "pro")
            plan = Plan(plan_value)

            return Subscription(
                subscription_id=sub.id,
                customer_id=sub.customer,
                plan=plan,
                status=sub.status,
                current_period_start=datetime.fromtimestamp(
                    sub.current_period_start, tz=timezone.utc
                ),
                current_period_end=datetime.fromtimestamp(
                    sub.current_period_end, tz=timezone.utc
                ),
                cancel_at_period_end=sub.cancel_at_period_end,
            )
        except Exception as e:
            raise BillingError(f"Failed to cancel subscription: {e}")


class BillingWebhookHandler:
    """Webhook イベントハンドラー

    Stripeからのイベントを処理し、ライセンスを更新。
    """

    def __init__(
        self,
        billing_client: BillingClient,
        license_manager: LicenseManager,
    ):
        self.billing = billing_client
        self.license_manager = license_manager

    def handle_event(self, event: dict) -> dict:
        """Webhookイベントを処理

        Args:
            event: Stripe Event オブジェクト

        Returns:
            dict: 処理結果
        """
        event_type = event.get("type", "")
        data = event.get("data", {}).get("object", {})

        handlers = {
            "checkout.session.completed": self._handle_checkout_completed,
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.payment_succeeded": self._handle_payment_succeeded,
            "invoice.payment_failed": self._handle_payment_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(data)

        return {"status": "ignored", "event_type": event_type}

    def _handle_checkout_completed(self, session: dict) -> dict:
        """Checkout完了処理"""
        email = session.get("customer_email", "")
        metadata = session.get("metadata", {})
        plan_value = metadata.get("plan", "pro")

        try:
            plan = Plan(plan_value)
        except ValueError:
            plan = Plan.PRO

        # ライセンスキーを生成してアクティベート
        license_key = generate_license_key(plan, email)
        self.license_manager.activate(license_key, email)

        return {
            "status": "success",
            "action": "license_activated",
            "plan": plan.value,
            "email": email,
            "license_key": license_key,
        }

    def _handle_subscription_created(self, subscription: dict) -> dict:
        """サブスクリプション作成処理"""
        metadata = subscription.get("metadata", {})
        plan_value = metadata.get("plan", "pro")
        status = subscription.get("status", "")

        return {
            "status": "success",
            "action": "subscription_created",
            "subscription_status": status,
            "plan": plan_value,
        }

    def _handle_subscription_updated(self, subscription: dict) -> dict:
        """サブスクリプション更新処理"""
        status = subscription.get("status", "")
        metadata = subscription.get("metadata", {})
        plan_value = metadata.get("plan", "")
        email = metadata.get("email", "")

        # ステータスに応じてライセンスを更新
        if status == "active":
            # アクティブなら再アクティベート
            try:
                plan = Plan(plan_value)
                license_key = generate_license_key(plan, email)
                self.license_manager.activate(license_key, email)
            except (ValueError, Exception):
                pass

        elif status in ("past_due", "unpaid", "canceled"):
            # 支払い問題またはキャンセルならダウングレード
            self.license_manager.deactivate()

        return {
            "status": "success",
            "action": "subscription_updated",
            "subscription_status": status,
        }

    def _handle_subscription_deleted(self, subscription: dict) -> dict:
        """サブスクリプション削除処理"""
        # ライセンスを無効化
        self.license_manager.deactivate()

        return {
            "status": "success",
            "action": "license_deactivated",
        }

    def _handle_payment_succeeded(self, invoice: dict) -> dict:
        """支払い成功処理"""
        return {
            "status": "success",
            "action": "payment_recorded",
            "subscription_id": invoice.get("subscription", ""),
        }

    def _handle_payment_failed(self, invoice: dict) -> dict:
        """支払い失敗処理"""
        attempt_count = invoice.get("attempt_count", 0)

        # 3回失敗したらライセンスを無効化
        if attempt_count >= 3:
            self.license_manager.deactivate()

            return {
                "status": "warning",
                "action": "license_suspended",
                "reason": "payment_failed",
                "attempt_count": attempt_count,
            }

        return {
            "status": "warning",
            "action": "payment_retry_pending",
            "attempt_count": attempt_count,
        }


def get_price_info(plan: Plan) -> Optional[PriceInfo]:
    """プランの価格情報を取得

    Args:
        plan: プラン

    Returns:
        PriceInfo: 価格情報（Freeの場合はNone）
    """
    return PRICE_CONFIG.get(plan)


def get_all_prices() -> list[PriceInfo]:
    """全価格情報を取得"""
    return list(PRICE_CONFIG.values())


def create_checkout_url(
    plan: Plan,
    email: str,
    base_url: str = "https://devbuddy.ai",
) -> str:
    """Checkout URLを生成（簡易版）

    Args:
        plan: プラン
        email: メールアドレス
        base_url: ベースURL

    Returns:
        str: Checkout URL
    """
    client = BillingClient()
    success_url = f"{base_url}/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{base_url}/pricing"

    session = client.create_checkout_session(
        plan=plan,
        email=email,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return session.url
