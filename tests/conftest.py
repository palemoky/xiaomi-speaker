"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    from src.config import Settings
    
    return Settings(
        mi_user="test_user",
        mi_pass="test_pass",
        mi_did="test_device_id",
        server_host="0.0.0.0",
        server_port=9527,
        static_server_host="192.168.1.100",
        static_server_port=1810,
        piper_voice_zh=None,  # Use speaker's built-in TTS
        piper_voice_en="en_US-lessac-medium",
        api_secret="test_secret_key",
    )


@pytest.fixture
def mock_speaker_service():
    """Mock SpeakerService for testing."""
    from src.services.speaker import SpeakerService
    
    service = MagicMock(spec=SpeakerService)
    service.play_tts = AsyncMock(return_value=True)
    service.play_audio_url = AsyncMock(return_value=True)
    service.set_volume = AsyncMock(return_value=True)
    service.connect = AsyncMock()
    service.close = AsyncMock()
    
    return service


@pytest.fixture
def mock_tts_service():
    """Mock TTSService for testing."""
    from pathlib import Path
    from src.services.tts import TTSService
    
    service = MagicMock(spec=TTSService)
    service.generate_speech = AsyncMock(return_value=Path("/tmp/test_audio.wav"))
    
    return service


@pytest.fixture
def mock_notification_service(mock_speaker_service, mock_tts_service):
    """Mock NotificationService for testing."""
    from src.services.notification import NotificationService
    
    service = MagicMock(spec=NotificationService)
    service.speaker = mock_speaker_service
    service.tts = mock_tts_service
    service.send_github_notification = AsyncMock(return_value=True)
    service.send_custom_notification = AsyncMock(return_value=True)
    service.cleanup = AsyncMock()
    
    return service
