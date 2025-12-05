# Cloudflare Tunnel 设置指南

本指南介绍如何使用 Cloudflare Tunnel 将本地运行的 xiaomi-speaker 服务暴露到公网，以便 GitHub 可以发送 webhook 请求。

## 方式一：使用 Docker Compose（推荐）

最简单的方式，无需手动安装 cloudflared。

### 1. 获取 Tunnel Token

1. 登录 [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. 进入 **Networks** > **Tunnels** > **Create a tunnel**
3. 选择 **Cloudflared**
4. 命名你的 Tunnel（例如 `xiaomi-speaker`）并保存
5. 在 "Install and run a connector" 页面，找到 Docker 命令中的 token 部分：
   ```bash
   tunnel run --token eyJhIjoi...
   ```
6. 复制这个长字符串 Token

### 2. 配置 Public Hostname

1. 在 Tunnel 配置页面的 "Public Hostnames" 标签
2. 点击 **Add a public hostname**
3. 配置：
   - **Subdomain**: 例如 `speaker`
   - **Domain**: 选择你的域名
   - **Service**: 选择 `HTTP`
   - **URL**: 填写 `xiaomi-speaker:9527`（注意使用容器名）
4. 保存

### 3. 更新 .env 文件

在 `.env` 文件中添加 Token：

```bash
TUNNEL_TOKEN=eyJhIjoi...你的完整token...
```

### 4. 启动服务

```bash
docker-compose up -d
```

现在你的服务可以通过 `https://speaker.yourdomain.com` 访问了！

## 方式二：手动安装 cloudflared

如果你不想在 Docker 中运行 Tunnel，可以在宿主机直接安装。

### 1. 安装 cloudflared

```bash
# ARM64（树莓派 4/5）
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o cloudflared

# AMD64（普通电脑）
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared

# 安装
sudo mv cloudflared /usr/local/bin/
sudo chmod +x /usr/local/bin/cloudflared

# 验证安装
cloudflared --version
```

### 2. 登录 Cloudflare

```bash
cloudflared tunnel login
```

这会打开浏览器，选择你要使用的域名。

### 3. 创建 Tunnel

```bash
cloudflared tunnel create xiaomi-speaker
```

记下输出中的 Tunnel ID（类似 `a1b2c3d4-e5f6-7890-abcd-ef1234567890`）。

### 4. 配置文件

创建 `~/.cloudflared/config.yml`：

```yaml
tunnel: xiaomi-speaker
credentials-file: /home/YOUR_USER/.cloudflared/TUNNEL_ID.json

ingress:
  - hostname: speaker.yourdomain.com
    service: http://localhost:9527
  - service: http_status:404
```

将 `YOUR_USER`、`TUNNEL_ID` 和 `speaker.yourdomain.com` 替换为实际值。

### 5. 配置 DNS

```bash
cloudflared tunnel route dns xiaomi-speaker speaker.yourdomain.com
```

### 6. 运行 Tunnel

```bash
# 测试运行
cloudflared tunnel run xiaomi-speaker

# 如果一切正常，设置为系统服务
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

## 验证配置

### 1. 检查 Tunnel 状态

```bash
# Docker Compose 方式
docker-compose logs cloudflared

# 手动安装方式
cloudflared tunnel list
cloudflared tunnel info xiaomi-speaker
```

### 2. 测试本地服务

```bash
curl http://localhost:9527/health
```

应该返回：
```json
{"status": "healthy"}
```

### 3. 测试公网访问

```bash
curl https://speaker.yourdomain.com/health
```

应该返回相同的结果。

### 4. 测试 webhook

```bash
curl -X POST https://speaker.yourdomain.com/webhook/custom \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_secret" \
  -d '{"message": "测试通知"}'
```

如果配置正确，音箱应该会播报"测试通知"。

## 安全建议

### 1. 启用 API 认证

在 `.env` 中配置：

```bash
API_SECRET=your_strong_random_api_key
```

生成强密钥：
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. 配置 Cloudflare Access（可选）

为额外的安全层，可以配置 Cloudflare Access：

1. 在 Cloudflare Zero Trust Dashboard 中
2. 进入 **Access** > **Applications** > **Add an application**
3. 选择 **Self-hosted**
4. 配置应用程序：
   - **Application name**: xiaomi-speaker
   - **Session duration**: 24 hours
   - **Application domain**: speaker.yourdomain.com
5. 添加策略（例如，只允许特定 IP 或 Service Token）

### 3. 使用 GitHub Webhook Secret

在 `.env` 中配置：

```bash
GITHUB_WEBHOOK_SECRET=your_webhook_secret
```

在 GitHub webhook 配置中设置相同的 secret。

## 故障排除

### Tunnel 无法连接

1. **检查 token 是否正确**
   ```bash
   # Docker Compose
   docker-compose logs cloudflared

   # 手动安装
   sudo journalctl -u cloudflared -f
   ```

2. **验证网络连接**
   ```bash
   ping cloudflare.com
   ```

3. **检查防火墙规则**
   - 确保允许出站 HTTPS 连接

### 本地服务可访问，公网不可访问

1. **检查 DNS 配置**
   ```bash
   nslookup speaker.yourdomain.com
   ```

2. **验证 ingress 配置**
   - 确保 service URL 正确（Docker 使用容器名，本地使用 localhost）

3. **查看 Tunnel 日志**
   ```bash
   # Docker
   docker-compose logs -f cloudflared

   # Systemd
   sudo journalctl -u cloudflared -f
   ```

### 502 Bad Gateway

1. **确认本地服务运行**
   ```bash
   curl http://localhost:9527/health
   ```

2. **检查端口配置**
   - Docker Compose: 使用容器名和内部端口
   - 手动安装: 使用 localhost 和暴露的端口

3. **查看应用日志**
   ```bash
   docker-compose logs -f xiaomi-speaker
   ```

## 高级配置

### 使用临时 URL（测试用）

如果你只是想快速测试，可以使用临时 URL：

```bash
cloudflared tunnel --url http://localhost:9527
```

这会生成一个临时的 `*.trycloudflare.com` URL。

**注意**：临时 URL 在进程结束后失效，不适合生产使用。

### 多个服务

如果你想通过同一个 tunnel 暴露多个服务：

```yaml
tunnel: xiaomi-speaker
credentials-file: /home/YOUR_USER/.cloudflared/TUNNEL_ID.json

ingress:
  - hostname: speaker.yourdomain.com
    service: http://localhost:9527
  - hostname: other-service.yourdomain.com
    service: http://localhost:8080
  - service: http_status:404
```

### 自定义 Cloudflare 设置

在 Cloudflare Dashboard 中，你可以为你的域名配置：

- **SSL/TLS 模式**: 推荐 "Full" 或 "Full (strict)"
- **WAF 规则**: 保护你的端点
- **Rate Limiting**: 防止滥用
- **Analytics**: 监控流量

## 参考资料

- [Cloudflare Tunnel 官方文档](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Cloudflare Access 文档](https://developers.cloudflare.com/cloudflare-one/applications/)
- [GitHub Webhooks 文档](https://docs.github.com/en/webhooks)
