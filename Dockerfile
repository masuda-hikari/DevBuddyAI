# DevBuddyAI Webhook Server Dockerfile
# 本番環境向け最適化済みマルチステージビルド

# ステージ1: ビルド
FROM python:3.12-slim AS builder

WORKDIR /app

# 依存関係のみ先にインストール（キャッシュ最適化）
COPY pyproject.toml README.md ./
COPY src/ ./src/

# pipアップグレードとパッケージビルド
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir build \
    && python -m build --wheel

# ステージ2: ランタイム
FROM python:3.12-slim AS runtime

# セキュリティ: 非rootユーザーで実行
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# ビルド済みwheelをコピー
COPY --from=builder /app/dist/*.whl /tmp/

# サーバー依存含めてインストール
RUN pip install --no-cache-dir /tmp/*.whl[server] \
    && rm -rf /tmp/*.whl

# 非rootユーザーに切り替え
USER appuser

# 環境変数のデフォルト値
ENV DEVBUDDY_HOST=0.0.0.0 \
    DEVBUDDY_PORT=8000 \
    DEVBUDDY_LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${DEVBUDDY_PORT}/health || exit 1

# ポート公開
EXPOSE ${DEVBUDDY_PORT}

# 起動コマンド
CMD ["python", "-c", "from devbuddy.server.webhook import WebhookServer, WebhookConfig; import os; config = WebhookConfig(stripe_api_key=os.environ.get('STRIPE_API_KEY', ''), stripe_webhook_secret=os.environ.get('STRIPE_WEBHOOK_SECRET', ''), host=os.environ.get('DEVBUDDY_HOST', '0.0.0.0'), port=int(os.environ.get('DEVBUDDY_PORT', '8000')), log_level=os.environ.get('DEVBUDDY_LOG_LEVEL', 'INFO')); WebhookServer(config).run()"]
