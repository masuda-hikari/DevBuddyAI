# DevBuddyAI Webhook Server デプロイガイド

本番環境へのデプロイ手順を説明します。

## 必須環境変数

```bash
STRIPE_API_KEY=sk_live_xxx       # Stripe API キー
STRIPE_WEBHOOK_SECRET=whsec_xxx  # Stripe Webhook シークレット
```

## デプロイオプション

### 1. Railway.app（推奨）

最も簡単なデプロイ方法です。

```bash
# 1. Railway CLIインストール
npm install -g @railway/cli

# 2. ログイン
railway login

# 3. プロジェクト作成・デプロイ
railway init
railway up

# 4. 環境変数設定
railway variables set STRIPE_API_KEY=sk_xxx
railway variables set STRIPE_WEBHOOK_SECRET=whsec_xxx

# 5. ドメイン確認
railway domain
```

### 2. Render.com

```bash
# 1. GitHubリポジトリをRenderに接続
# https://dashboard.render.com/

# 2. New Web Service → From GitHub

# 3. 設定:
#    - Name: devbuddy-webhook
#    - Docker
#    - Plan: Free または Starter

# 4. 環境変数をダッシュボードで設定
```

### 3. Fly.io

```bash
# 1. Fly CLIインストール
curl -L https://fly.io/install.sh | sh

# 2. ログイン
flyctl auth login

# 3. アプリ作成（初回のみ）
flyctl launch --dockerfile Dockerfile

# 4. シークレット設定
flyctl secrets set STRIPE_API_KEY=sk_xxx STRIPE_WEBHOOK_SECRET=whsec_xxx

# 5. デプロイ
flyctl deploy
```

### 4. Docker（自己ホスト）

```bash
# 1. イメージビルド
docker build -t devbuddy-webhook .

# 2. コンテナ起動
docker run -d \
  --name devbuddy-webhook \
  -p 8000:8000 \
  -e STRIPE_API_KEY=sk_xxx \
  -e STRIPE_WEBHOOK_SECRET=whsec_xxx \
  devbuddy-webhook

# または docker-compose使用
docker-compose up -d --build
```

## Stripe Webhook設定

デプロイ後、Stripeダッシュボードでエンドポイントを設定：

1. [Stripe Dashboard](https://dashboard.stripe.com/webhooks) → Webhooks
2. Add endpoint
3. Endpoint URL: `https://your-domain.com/api/v1/webhook/stripe`
4. Events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`

## ヘルスチェック

```bash
curl https://your-domain.com/health
# {"status": "healthy"}
```

## API確認

```bash
# 価格一覧
curl https://your-domain.com/api/v1/prices

# OpenAPI docs
open https://your-domain.com/docs
```

## トラブルシューティング

### ログ確認

```bash
# Railway
railway logs

# Fly.io
flyctl logs

# Docker
docker logs devbuddy-webhook
```

### 環境変数確認

```bash
# Railway
railway variables

# Fly.io
flyctl secrets list
```

## セキュリティ

- HTTPSを必ず使用
- Stripe APIキーはシークレットとして管理
- Webhook署名検証は必須
- IP制限の検討（オプション）
