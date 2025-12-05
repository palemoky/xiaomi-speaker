"""Tests for NotificationService."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.notification import NotificationService


@pytest.fixture
def notification_service(mock_speaker_service, mock_tts_service):
    """Create NotificationService with mocked dependencies."""
    with patch("src.services.notification.TTSService", return_value=mock_tts_service), \
         patch("src.services.notification.SpeakerService", return_value=mock_speaker_service):
        service = NotificationService()
        return service


class TestNotificationService:
    """Tests for NotificationService class."""
    
    @pytest.mark.asyncio
    async def test_send_github_notification_success(self, notification_service, mock_speaker_service):
        """Test sending GitHub notification successfully."""
        result = await notification_service.send_github_notification(
            repo="user/repo",
            workflow="CI",
            conclusion="success"
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_github_notification_failure(self, notification_service, mock_speaker_service):
        """Test sending GitHub notification for failure."""
        result = await notification_service.send_github_notification(
            repo="user/repo",
            workflow="CI",
            conclusion="failure"
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_custom_notification(self, notification_service):
        """Test sending custom notification."""
        message = "这是一条测试通知"
        result = await notification_service.send_custom_notification(message)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_cleanup(self, notification_service, mock_speaker_service):
        """Test cleanup closes speaker service."""
        await notification_service.cleanup()
        mock_speaker_service.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_message_with_speaker_tts(self, notification_service, mock_speaker_service):
        """Test _send_message uses speaker TTS for Chinese when Piper not configured."""
        with patch("src.services.notification.settings") as mock_settings:
            mock_settings.piper_voice_zh = None
            
            message = "这是中文测试"
            result = await notification_service._send_message(message)
            
            assert result is True
            mock_speaker_service.play_tts.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_send_message_with_piper_tts(self, notification_service, mock_speaker_service, mock_tts_service):
        """Test _send_message uses Piper TTS when configured."""
        with patch("src.services.notification.settings") as mock_settings:
            mock_settings.piper_voice_zh = "zh_CN-huayan-medium"
            mock_settings.get_static_server_url = MagicMock(return_value="http://192.168.1.100:1810")
            
            message = "这是中文测试"
            result = await notification_service._send_message(message)
            
            assert result is True
            mock_tts_service.generate_speech.assert_called_once()
            mock_speaker_service.play_audio_url.assert_called_once()
    
    def test_should_use_speaker_tts_chinese_no_piper(self, notification_service):
        """Test should use speaker TTS for Chinese when Piper not configured."""
        with patch("src.services.notification.settings") as mock_settings:
            mock_settings.piper_voice_zh = None
            
            assert notification_service._should_use_speaker_tts("这是中文") is True
    
    def test_should_use_speaker_tts_english_no_piper(self, notification_service):
        """Test should not use speaker TTS for English even when Piper not configured."""
        with patch("src.services.notification.settings") as mock_settings:
            mock_settings.piper_voice_zh = None
            
            assert notification_service._should_use_speaker_tts("This is English") is False
    
    def test_should_use_speaker_tts_with_piper_configured(self, notification_service):
        """Test should not use speaker TTS when Piper is configured."""
        with patch("src.services.notification.settings") as mock_settings:
            mock_settings.piper_voice_zh = "zh_CN-huayan-medium"
            
            assert notification_service._should_use_speaker_tts("这是中文") is False
    
    def test_format_notification(self, notification_service):
        """Test notification message formatting."""
        template = "Repo: {repo}, Workflow: {workflow}, Status: {conclusion}"
        message = notification_service._format_notification(
            template=template,
            repo="user/repo",
            workflow="CI",
            conclusion="success",
            url="https://github.com/user/repo/actions/runs/123"
        )
        
        assert message == "Repo: user/repo, Workflow: CI, Status: success"
    
    def test_get_audio_url(self, notification_service):
        """Test audio URL generation."""
        with patch("src.services.notification.settings") as mock_settings:
            mock_settings.get_static_server_url = MagicMock(return_value="http://192.168.1.100:1810")
            
            audio_file = Path("/app/audio_cache/test.wav")
            url = notification_service._get_audio_url(audio_file)
            
            assert url == "http://192.168.1.100:1810/test.wav"
