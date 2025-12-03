# GitHub Actions 集成示例

## 方式一：配置 Webhook（推荐）

最简单的方式，无需修改工作流。

### 配置步骤

1. 在 GitHub 仓库中进入 **Settings → Webhooks → Add webhook**

2. 配置 webhook：
   - **Payload URL**: `https://your-tunnel-url.com/webhook/github`
   - **Content type**: `application/json`
   - **Secret**: （可选）与 `.env` 中的 `GITHUB_WEBHOOK_SECRET` 一致
   - **Events**: 选择 `Workflow runs`

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
            -d '{"message": "构建完成：${{ github.repository }} - ${{ job.status }}"}'
```

### 仅失败时通知

```yaml
- name: Send failure notification
  if: failure()
  run: |
    curl -X POST ${{ secrets.WEBHOOK_URL }}/webhook/custom \
      -H "Content-Type: application/json" \
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
            -d '{"message": "部署成功：${{ github.repository }}"}'
      
      - name: Notify failure
        if: failure()
        run: |
          curl -X POST ${{ secrets.WEBHOOK_URL }}/webhook/custom \
            -H "Content-Type: application/json" \
            -d '{"message": "部署失败：${{ github.repository }}，请检查日志"}'
```

## 配置 Secrets

在仓库 **Settings → Secrets and variables → Actions** 中添加：

- **Name**: `WEBHOOK_URL`
- **Value**: `https://your-tunnel-url.com`

## Webhook 负载格式

### GitHub 标准 Webhook

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

### 自定义通知

```json
{
  "message": "你的自定义消息"
}
```
