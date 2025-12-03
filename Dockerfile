# syntax=docker/dockerfile:1

# ==========================================
# Stage 1: Builder (构建依赖环境)
# ==========================================
FROM python:3.14-slim-bookworm AS builder

WORKDIR /app

# 1. 安装编译所需的系统工具
# 虽然大部分库都有 Wheel 包，但保留 build-essential 以防万一 (如 miservice 依赖的底层库)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates

# 2. 高效安装 uv (直接从官方镜像复制)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 3. 安装 Python 依赖
# 关键修改：添加 --no-install-project，这样就不需要 README.md，也不会安装项目本身
ENV UV_COMPILE_BYTECODE=1
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# ==========================================
# Stage 2: Runtime (运行时环境)
# ==========================================
FROM python:3.14-slim-bookworm

WORKDIR /app

# 1. 安装运行时系统依赖
# 保留 curl 用于 Healthcheck
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

# 4. 复制源代码
COPY src ./src

# 5. 创建缓存目录并设置权限
RUN mkdir -p /app/audio_cache && chown -R root:root /app/audio_cache

# 6. 环境配置
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 7. 暴露端口
EXPOSE 1810 9527

# 9. 启动命令
# 使用 python 直接运行，不再依赖 uv run
CMD ["python", "-m", "src.main"]
