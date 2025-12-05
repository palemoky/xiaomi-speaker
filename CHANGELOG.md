# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-12-05

### ✨ Features

#### Core Functionality
- **GitHub Webhook Integration** - Support for `workflow_run`, `workflow_job`, and `check_run` events
- **Piper TTS Integration** - Local offline text-to-speech with high-quality neural voices
- **Smart TTS Fallback** - Automatically uses speaker's built-in TTS for Chinese when Piper voice not configured
- **MiService Integration** - Full support for Xiaomi speaker control via MiNA protocol
- **Multi-format Device ID** - Support UUID, numeric DID, or device name for speaker identification

#### Security
- **API Key Authentication** - Protect custom webhook endpoint with `X-API-Key` header
- **GitHub Webhook Signature Verification** - Optional HMAC-SHA256 signature validation
- **Secure Comparison** - Using `secrets.compare_digest()` to prevent timing attacks

#### Infrastructure
- **Docker Multi-arch Support** - Automated builds for `linux/amd64` and `linux/arm64`
- **Static File Server** - Serve generated audio files for speaker playback
- **Audio Caching** - Automatic caching of generated TTS audio files
- **Health Check Endpoint** - `/health` endpoint for monitoring

### 🧪 Testing & Quality

- **Comprehensive Test Suite** - 81 unit tests with 66% code coverage
- **100% Coverage** on critical modules:
  - `src/api/webhooks.py` - API endpoints
  - `src/config.py` - Configuration management
  - `src/utils/language.py` - Language detection utilities
- **High Coverage** on services:
  - `src/services/speaker.py` - 97% coverage
  - `src/services/notification.py` - 95% coverage

### 🚀 CI/CD

- **GitHub Actions Test Workflow** - Automated testing on every push and PR
  - Ruff linting
  - Mypy type checking
  - Pytest with coverage reporting
  - Codecov integration
- **GitHub Actions Docker Build** - Multi-architecture image builds
  - Automatic tagging (`latest`, version tags, SHA tags)
  - Docker Hub deployment
  - Build notifications via speaker

### 📚 Documentation

- **Comprehensive README** - Complete setup and usage guide
- **API Documentation** - Detailed endpoint specifications with examples
- **Development Guide** - Local development setup and testing instructions
- **Contribution Guidelines** - Clear guidelines for contributors
- **Cloudflare Tunnel Setup** - Step-by-step tunnel configuration
- **GitHub Actions Examples** - Integration examples and best practices

### 🛠️ Developer Experience

- **UV Package Manager** - Fast dependency management
- **Commitizen Integration** - Conventional commits with custom scopes
- **Pre-commit Hooks** - Automated code quality checks
- **Type Safety** - Full mypy type checking support
- **Code Formatting** - Ruff for consistent code style

### 🐳 Docker

- **Multi-stage Build** - Optimized image size
- **Layer Caching** - Fast rebuilds with build cache
- **Health Checks** - Built-in container health monitoring
- **Volume Management** - Persistent audio cache and Piper voices
- **Docker Compose** - Easy deployment with compose file

### 📦 Dependencies

**Core**:
- FastAPI >= 0.123.0
- Uvicorn >= 0.38.0
- Piper TTS >= 1.2.0
- MiService Fork >= 2.9.3
- Pydantic >= 2.12.0
- Python 3.13

**Development**:
- Ruff - Linting and formatting
- Mypy - Type checking
- Pytest - Testing framework
- Pytest-cov - Coverage reporting

### 🔧 Configuration

- **Environment-based Config** - All settings via `.env` file
- **Optional TTS Models** - Piper Chinese voice is optional
- **Flexible Speaker ID** - Support multiple ID formats
- **Security Options** - Optional API key and webhook signature verification

### 📊 Project Stats

- **Lines of Code**: ~1,200 (excluding tests)
- **Test Coverage**: 66%
- **Total Tests**: 81
- **Supported Architectures**: 2 (amd64, arm64)
- **Python Version**: 3.13
- **Docker Image Size**: ~500MB (with Piper models)

### 🎯 Highlights

1. **Production Ready** - Comprehensive testing and CI/CD
2. **Developer Friendly** - Modern tooling and clear documentation
3. **Secure by Default** - Optional but recommended authentication
4. **Flexible Deployment** - Docker-first with multi-arch support
5. **Offline Capable** - Piper TTS works without internet (after model download)

---

## Links

- [GitHub Repository](https://github.com/palemoky/xiaomi-speaker)
- [Docker Hub](https://hub.docker.com/r/palemoky/xiaomi-speaker)
- [Documentation](https://github.com/palemoky/xiaomi-speaker/tree/main/docs)

[0.1.0]: https://github.com/palemoky/xiaomi-speaker/releases/tag/v0.1.0
