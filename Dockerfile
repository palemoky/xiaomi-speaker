# syntax=docker/dockerfile:1

# ==========================================
# Stage 1: Builder (构建依赖环境)
# ==========================================
FROM python:3.13-slim AS builder

WORKDIR /app

# 1. 安装编译所需的系统工具
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl

# 2. 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 3. 安装 Python 依赖
ENV UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --no-editable

# 4. 优化虚拟环境大小
RUN find /app/.venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true \
    && find /app/.venv -type f -name "*.pyc" -delete \
    && find /app/.venv -type f -name "*.pyo" -delete \
    && find /app/.venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true \
    && find /app/.venv -type d -name "test" -exec rm -rf {} + 2>/dev/null || true

# ==========================================
# Stage 2: Runtime (运行时环境)
# ==========================================
FROM dhi.io/python:3.13

# OCI 标准元数据
LABEL org.opencontainers.image.title="Xiaomi Speaker" \
      org.opencontainers.image.description="Smart voice notification system for Xiaomi speakers with GitHub Actions integration" \
      org.opencontainers.image.vendor="Palemoky" \
      org.opencontainers.image.source="https://github.com/palemoky/xiaomi-speaker" \
      org.opencontainers.image.licenses="GPL-3.0"

WORKDIR /app

# 1. 从 Builder 复制虚拟环境
COPY --from=builder --chown=nonroot:nonroot /app/.venv /app/.venv

# 2. 从 Builder 复制 curl（用于健康检查）
COPY --from=builder /usr/bin/curl /usr/bin/curl
COPY --from=builder /usr/lib/*/libcurl.so.4* /usr/lib/
COPY --from=builder /usr/lib/*/libnghttp2.so.14* /usr/lib/
COPY --from=builder /usr/lib/*/libssl.so.3* /usr/lib/
COPY --from=builder /usr/lib/*/libcrypto.so.3* /usr/lib/
COPY --from=builder /lib/*/libz.so.1* /lib/

# 3. 设置环境变量
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# 4. 复制源代码
COPY --chown=nonroot:nonroot src ./src

# 5. 端口与健康检查
EXPOSE 1810 2010

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD ["/usr/bin/curl", "-f", "http://127.0.0.1:2010/health"]

CMD ["python", "-m", "src.main"]
