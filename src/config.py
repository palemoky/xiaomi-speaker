"""Configuration management using Pydantic settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Xiaomi Account Configuration
    mi_user: str = Field(..., description="Xiaomi account username/email")
    mi_pass: str = Field(..., description="Xiaomi account password")
    mi_did: str = Field(..., description="Xiaomi device ID or name")

    # Server Configuration
    server_host: str = Field(default="0.0.0.0", description="Webhook server host")
    server_port: int = Field(default=5000, description="Webhook server port")

    # Static File Server Configuration
    static_server_host: str = Field(
        default="0.0.0.0", description="Static file server host"
    )
    static_server_port: int = Field(
        default=8000, description="Static file server port"
    )

    # Edge TTS Configuration
    tts_voice: str = Field(
        default="zh-CN-XiaoxiaoNeural",
        description="Edge TTS voice for Chinese",
    )
    tts_rate: str = Field(default="+0%", description="Speech rate adjustment")
    tts_volume: str = Field(default="+0%", description="Speech volume adjustment")

    # Notification Templates
    notification_template_failure: str = Field(
        default="GitHub Actions 构建失败：仓库 {repo}，工作流 {workflow} 执行失败",
        description="Template for failure notifications",
    )
    notification_template_success: str = Field(
        default="GitHub Actions 构建成功：仓库 {repo}，工作流 {workflow} 执行成功",
        description="Template for success notifications",
    )

    # Audio Cache Directory
    audio_cache_dir: Path = Field(
        default=Path("audio_cache"), description="Directory for cached audio files"
    )

    # Webhook Security (optional)
    github_webhook_secret: Optional[str] = Field(
        default=None, description="GitHub webhook secret for signature verification"
    )

    def get_static_server_url(self) -> str:
        """Get the base URL for the static file server."""
        # Use localhost for local access from the same machine
        return f"http://localhost:{self.static_server_port}"

    def ensure_audio_cache_dir(self) -> None:
        """Ensure the audio cache directory exists."""
        self.audio_cache_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
