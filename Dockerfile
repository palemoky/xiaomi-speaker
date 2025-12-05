# syntax=docker/dockerfile:1

# ==========================================
# Stage 1: Builder (构建依赖环境)
# ==========================================
FROM python:3.13-slim-bookworm AS builder

WORKDIR /app

# 1. 安装编译所需的系统工具
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates

# 2. 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 3. 安装 Python 依赖
ENV UV_COMPILE_BYTECODE=1
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --no-editable

# ==========================================
# Stage 2: Runtime (运行时环境)
# ==========================================
FROM python:3.13-slim-bookworm

WORKDIR /app

# 1. 安装运行时系统依赖
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# 2. 从 Builder 复制虚拟环境
COPY --from=builder /app/.venv /app/.venv

# 3. 设置 PATH，自动激活虚拟环境
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 4. 复制源代码
COPY src ./src

# 5. 创建缓存目录和模型目录
RUN mkdir -p /app/audio_cache /root/.local/share/piper-voices 

# 6. 端口与健康检查
EXPOSE 1810 9527

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:9527/health || exit 1

CMD ["python", "-m", "src.main"]
