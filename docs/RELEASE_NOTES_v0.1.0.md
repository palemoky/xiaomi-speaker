# 🎉 v0.1.0 Release Notes

**Release Date**: 2025-12-05

首个正式版本发布！这是一个功能完整、经过充分测试的生产就绪版本。

## 🌟 主要特性

### 核心功能

- **GitHub 集成** - 完整支持 GitHub Actions webhook 通知
- **本地 TTS** - 使用 Piper TTS 实现高质量离线语音合成
- **智能回退** - 中文自动使用音箱内置 TTS，无需额外配置
- **小米音箱控制** - 通过 MiService 完整控制小米音箱

### 安全特性

- **API 密钥认证** - 保护自定义 webhook 端点
- **GitHub 签名验证** - 可选的 webhook 签名验证
- **安全对比** - 使用 `secrets.compare_digest()` 防止时序攻击

### 开发体验

- **完整测试** - 81 个单元测试，66% 代码覆盖率
- **CI/CD 集成** - GitHub Actions 自动化测试和构建
- **类型安全** - 完整的 mypy 类型检查
- **代码质量** - Ruff 代码检查和格式化

## 📦 快速开始

### Docker 部署（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/palemoky/xiaomi-speaker.git
cd xiaomi-speaker

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 3. 启动服务
docker-compose up -d
```

### Docker Hub

```bash
docker pull palemoky/xiaomi-speaker:v0.1.0
```

支持架构：
- `linux/amd64` - x86_64
- `linux/arm64` - ARM64（树莓派 4/5）

## 🔧 配置要求

### 必填配置

```bash
MI_USER=your_xiaomi_account@example.com
MI_PASS=your_xiaomi_password
MI_DID=your_device_id
STATIC_SERVER_HOST=192.168.1.100  # 你的设备 IP
```

### 推荐配置

```bash
# API 安全
API_SECRET=your_strong_random_api_key

# GitHub Webhook 验证
GITHUB_WEBHOOK_SECRET=your_webhook_secret
```

## 📊 测试覆盖率

| 模块 | 覆盖率 |
|------|--------|
| API Webhooks | 100% ✅ |
| Configuration | 100% ✅ |
| Language Utils | 100% ✅ |
| Speaker Service | 97% ✅ |
| Notification Service | 95% ✅ |
| **Overall** | **66%** |

## 🚀 CI/CD

### 自动化测试

每次 push 和 PR 都会自动运行：
- ✅ Ruff 代码检查
- ✅ Mypy 类型检查
- ✅ 81 个单元测试
- ✅ 代码覆盖率报告

### 自动化构建

- 多架构 Docker 镜像构建
- 自动推送到 Docker Hub
- 版本标签管理
- 构建状态通知

## 📚 文档

- [README](../README.md) - 完整使用指南
- [Cloudflare Tunnel 设置](cloudflare-tunnel-setup.md) - Tunnel 配置指南
- [GitHub Actions 示例](github-actions-examples.md) - 集成示例
- [CHANGELOG](../CHANGELOG.md) - 完整变更日志

## 🐛 已知问题

无重大已知问题。

如果发现问题，请[提交 Issue](https://github.com/palemoky/xiaomi-speaker/issues)。

## 🔄 升级指南

这是首个版本，无需升级。

## 🤝 贡献

欢迎贡献！请查看[贡献指南](../README.md#-贡献指南)。

## 📝 完整变更日志

查看 [CHANGELOG.md](../CHANGELOG.md) 获取详细的变更列表。

## 🙏 致谢

感谢以下开源项目：

- [MiService](https://github.com/yihong0618/MiService) - 小米云服务接口
- [Piper TTS](https://github.com/rhasspy/piper) - 本地神经网络 TTS
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Web 框架

## 📮 联系方式

- **GitHub Issues**: [提交问题](https://github.com/palemoky/xiaomi-speaker/issues)
- **Email**: palemoky@gmail.com

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**
