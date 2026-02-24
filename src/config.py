"""Configuration management using Pydantic settings."""

from pathlib import Path

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
    mi_user: str = Field(default="", description="Xiaomi account username/email")
    mi_pass: str = Field(default="", description="Xiaomi account password")
    mi_did: str = Field(default="", description="Xiaomi device ID or name")
    mi_user_id: str = Field(default="", description="Xiaomi user ID from browser cookies (used when password login fails)")
    mi_pass_token: str = Field(default="", description="Xiaomi passToken from browser cookies (used when password login fails)")
    mi_token_path: str = Field(default="/app/data/.mi.token", description="Path to store Xiaomi account token for persistent login")

    # Server Configuration
    server_host: str = Field(default="0.0.0.0", description="Webhook server host")
    server_port: int = Field(default=2010, description="Webhook server port")

    # Static File Server Configuration
    static_server_host: str = Field(default="0.0.0.0", description="Static file server host")
    static_server_port: int = Field(default=1810, description="Static file server port")

    # Piper TTS Configuration
    piper_voice_zh: str | None = Field(
        default=None,
        description="Piper voice model for Chinese (if not set, use speaker's built-in TTS)",
    )
    piper_voice_en: str = Field(
        default="en_US-lessac-medium",
        description="Piper voice model for English",
    )
    piper_speaker: int = Field(
        default=0,
        description="Speaker ID for multi-speaker models",
    )
    piper_length_scale: float = Field(
        default=1.0,
        description="Speech speed (1.0 = normal, <1.0 = faster, >1.0 = slower)",
    )

    # Notification Templates
    notification_template_failure: str = Field(
        default="GitHub Actions 构建失败：仓库 {repo}，工作流 {workflow} 执行失败",
        description="Template for failure notifications",
    )
    notification_template_success: str = Field(
        default="GitHub Actions 构建成功：仓库 {repo}，工作流 {workflow} 执行成功",
        description="Template for success notifications",
    )

    # Notification Queue Configuration
    notification_interval: float = Field(
        default=3.0,
        description="Interval in seconds between consecutive notifications",
    )

    # Audio Cache Configuration
    audio_cache_dir: Path = Field(
        default=Path("audio_cache"), description="Directory for cached audio files"
    )
    audio_cache_max_size_mb: int = Field(
        default=100, description="Maximum cache size in MB (0 = unlimited)"
    )

    # Webhook Security (optional)
    github_webhook_secret: str | None = Field(
        default=None, description="GitHub webhook secret for signature verification"
    )

    # API Security (optional)
    api_secret: str | None = Field(
        default=None, description="API secret for custom webhook authentication"
    )

    def get_static_server_url(self) -> str:
        """Get the base URL for the static file server."""
        # Use configured host (e.g., Raspberry Pi IP) for network access
        return f"http://{self.static_server_host}:{self.static_server_port}"

    def ensure_audio_cache_dir(self) -> None:
        """Ensure the audio cache directory exists."""
        self.audio_cache_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
