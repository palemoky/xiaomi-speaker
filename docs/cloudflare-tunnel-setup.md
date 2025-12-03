# Cloudflare Tunnel 设置

## 安装 cloudflared

```bash
# ARM64（树莓派 4/5）
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o cloudflared

# AMD64（普通电脑）
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared

# 安装
sudo mv cloudflared /usr/local/bin/
sudo chmod +x /usr/local/bin/cloudflared
```

## 配置 Tunnel

### 1. 登录 Cloudflare

```bash
cloudflared tunnel login
```

### 2. 创建 Tunnel

```bash
cloudflared tunnel create xiaomi-speaker
```

记下输出中的 Tunnel ID。

### 3. 配置文件

创建 `~/.cloudflared/config.yml`：

```yaml
tunnel: xiaomi-speaker
credentials-file: /home/YOUR_USER/.cloudflared/TUNNEL_ID.json

ingress:
  - service: http://localhost:5000
```

将 `YOUR_USER` 和 `TUNNEL_ID` 替换为实际值。

### 4. 运行 Tunnel

```bash
cloudflared tunnel run xiaomi-speaker
```

会显示类似以下的公网 URL：

```
https://random-words-1234.trycloudflare.com
```

## 设置为系统服务

```bash
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

## 使用自己的域名（可选）

```bash
# 配置 DNS
cloudflared tunnel route dns xiaomi-speaker your-domain.com

# 更新 config.yml
cat > ~/.cloudflared/config.yml << EOF
tunnel: xiaomi-speaker
credentials-file: /home/YOUR_USER/.cloudflared/TUNNEL_ID.json

ingress:
  - hostname: your-domain.com
    service: http://localhost:5000
  - service: http_status:404
EOF
```

## 故障排除

### 查看 Tunnel 状态

```bash
cloudflared tunnel list
```

### 查看日志

```bash
# 如果使用 systemd
sudo journalctl -u cloudflared -f

# 如果手动运行
# 日志会直接显示在终端
```

### 测试连接

```bash
# 测试本地服务
curl http://localhost:5000/health

# 测试公网访问
curl https://your-tunnel-url.com/health
```
