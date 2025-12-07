# GitHub Actions 集成示例

本文档介绍如何将 Xiaomi Speaker 智能语音播报系统与 GitHub Actions 集成，实现自动化的构建和部署通知。

## 方式一：配置 Webhook（推荐）

最简单的方式，无需修改工作流。

### 配置步骤

1. 在 GitHub 仓库中进入 **Settings → Webhooks → Add webhook**

2. 配置 webhook：
   - **Payload URL**: `https://your-tunnel-url.com/webhook/github`
   - **Content type**: `application/json`
   - **Secret**: （可选）与 `.env` 中的 `GITHUB_WEBHOOK_SECRET` 一致
   - **Events**: 选择以下事件：
     - ✅ Workflow runs
     - ✅ Workflow jobs (可选)
     - ✅ Check runs (可选)

3. 保存配置

现在，每当工作流运行完成时，音箱都会自动播报结果。

## 方式二：在工作流中手动发送

### 基本通知

```yaml
name: CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: npm run build

      - name: Send notification
        if: always()
        run: |
          curl -X POST ${{ secrets.WEBHOOK_URL }}/webhook/custom \
            -H "Content-Type: application/json" \
            -H "X-API-Key: ${{ secrets.API_SECRET }}" \
            -d '{"message": "构建完成：${{ github.repository }} - ${{ job.status }}"}'
```

### 仅失败时通知

```yaml
- name: Send failure notification
  if: failure()
  run: |
    curl -X POST ${{ secrets.WEBHOOK_URL }}/webhook/custom \
      -H "Content-Type: application/json" \
      -H "X-API-Key: ${{ secrets.API_SECRET }}" \
      -d '{"message": "构建失败：${{ github.repository }}"}'
```

### 部署通知

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy
        run: ./deploy.sh

      - name: Notify success
        if: success()
        run: |
          curl -X POST ${{ secrets.WEBHOOK_URL }}/webhook/custom \
            -H "Content-Type: application/json" \
            -H "X-API-Key: ${{ secrets.API_SECRET }}" \
            -d '{"message": "部署成功：${{ github.repository }}"}'

      - name: Notify failure
        if: failure()
        run: |
          curl -X POST ${{ secrets.WEBHOOK_URL }}/webhook/custom \
            -H "Content-Type: application/json" \
            -H "X-API-Key: ${{ secrets.API_SECRET }}" \
            -d '{"message": "部署失败：${{ github.repository }}，请检查日志"}'
```

### 带 Cloudflare Access 的通知

如果你的 webhook 端点受 Cloudflare Access 保护：

```yaml
- name: Send notification with CF Access
  run: |
    curl -X POST ${{ secrets.WEBHOOK_URL }}/webhook/custom \
      -H "Content-Type: application/json" \
      -H "X-API-Key: ${{ secrets.API_SECRET }}" \
      -H "CF-Access-Client-Id: ${{ secrets.CF_CLIENT_ID }}" \
      -H "CF-Access-Client-Secret: ${{ secrets.CF_CLIENT_SECRET }}" \
      -d '{"message": "构建完成"}'
```

## 配置 Secrets

在仓库 **Settings → Secrets and variables → Actions** 中添加：

| Secret | 说明 | 必需 |
|--------|------|------|
| `WEBHOOK_URL` | Webhook 基础 URL | ✅ |
| `API_SECRET` | API 密钥（如果配置了 API_SECRET） | ⚠️ 推荐 |
| `CF_CLIENT_ID` | Cloudflare Access Client ID | ⚪ 可选 |
| `CF_CLIENT_SECRET` | Cloudflare Access Client Secret | ⚪ 可选 |

## Webhook 负载格式

### GitHub 标准 Webhook

#### workflow_run 事件

```json
{
  "action": "completed",
  "workflow_run": {
    "name": "CI",
    "conclusion": "success",
    "repository": {
      "full_name": "user/repo"
    },
    "html_url": "https://github.com/user/repo/actions/runs/123456"
  }
}
```

#### workflow_job 事件

```json
{
  "action": "completed",
  "workflow_job": {
    "name": "Build",
    "conclusion": "failure",
    "html_url": "https://github.com/user/repo/actions/runs/123456/jobs/789"
  },
  "repository": {
    "full_name": "user/repo"
  }
}
```

#### check_run 事件

```json
{
  "action": "completed",
  "check_run": {
    "name": "Lint",
    "conclusion": "success",
    "html_url": "https://github.com/user/repo/runs/123456"
  },
  "repository": {
    "full_name": "user/repo"
  }
}
```

### 自定义通知

```json
{
  "message": "你的自定义消息"
}
```

## 高级用例

### 条件通知

只在特定分支通知：

```yaml
- name: Notify on main branch
  if: github.ref == 'refs/heads/main' && success()
  run: |
    curl -X POST ${{ secrets.WEBHOOK_URL }}/webhook/custom \
      -H "Content-Type: application/json" \
      -H "X-API-Key: ${{ secrets.API_SECRET }}" \
      -d '{"message": "主分支构建成功"}'
```

### 包含更多信息

```yaml
- name: Detailed notification
  run: |
    curl -X POST ${{ secrets.WEBHOOK_URL }}/webhook/custom \
      -H "Content-Type: application/json" \
      -H "X-API-Key: ${{ secrets.API_SECRET }}" \
      -d "{\"message\": \"仓库：${{ github.repository }}，分支：${{ github.ref_name }}，提交：${{ github.sha }}，状态：${{ job.status }}\"}"
```

### 重试机制

```yaml
- name: Send notification with retry
  run: |
    for i in {1..3}; do
      curl -X POST ${{ secrets.WEBHOOK_URL }}/webhook/custom \
        -H "Content-Type: application/json" \
        -H "X-API-Key: ${{ secrets.API_SECRET }}" \
        -d '{"message": "构建完成"}' && break || sleep 5
    done
```

## 故障排除

### 通知未收到

1. **检查 webhook 配置**
   ```bash
   curl -X POST https://your-tunnel-url.com/webhook/custom \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your_api_secret" \
     -d '{"message": "测试"}'
   ```

2. **查看 GitHub Actions 日志**
   - 检查 curl 命令是否成功执行
   - 查看返回的 HTTP 状态码

3. **验证 API 密钥**
   - 确保 `API_SECRET` 与 `.env` 中的配置一致
   - 检查 header 名称是否为 `X-API-Key`

### 签名验证失败

如果使用 GitHub webhook 签名验证：

1. 确保 `GITHUB_WEBHOOK_SECRET` 在 GitHub 和 `.env` 中一致
2. 检查 webhook 配置中的 "Secret" 字段
3. 查看服务器日志获取详细错误信息

## 最佳实践

1. **使用 API 密钥** - 保护你的 webhook 端点
2. **配置签名验证** - 对 GitHub webhooks 启用签名验证
3. **使用 Secrets** - 不要在代码中硬编码敏感信息
4. **添加重试逻辑** - 网络可能不稳定
5. **简洁的消息** - 保持通知消息简短明了
6. **条件通知** - 只在重要事件时通知，避免过度打扰
