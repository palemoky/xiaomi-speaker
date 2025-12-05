"""Tests for SpeakerService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.speaker import SpeakerService


@pytest.fixture
def mock_mina_service():
    """Mock MiNAService."""
    service = MagicMock()
    service.device_list = AsyncMock(return_value=[
        {
            'name': '北京小米音箱',
            'deviceID': 'uuid-1234-5678',
            'miotDID': '77889911',
            'hardware': 'S12'
        },
        {
            'name': '卧室音箱',
            'deviceID': 'uuid-abcd-efgh',
            'miotDID': '12345678',
            'hardware': 'L05B'
        }
    ])
    service.play_by_url = AsyncMock(return_value={'code': 0})
    service.text_to_speech = AsyncMock(return_value={'code': 0})
    service.player_set_volume = AsyncMock(return_value={'code': 0})
    return service


@pytest.fixture
def mock_account():
    """Mock MiAccount."""
    return MagicMock()


@pytest.fixture
def mock_session():
    """Mock aiohttp ClientSession."""
    session = MagicMock()
    session.close = AsyncMock()
    return session


class TestSpeakerServiceInit:
    """Tests for SpeakerService initialization."""
    
    def test_init_with_device_id(self):
        """Test initialization with device ID."""
        with patch("src.services.speaker.settings") as mock_settings:
            mock_settings.mi_did = "test_device_id"
            
            service = SpeakerService()
            
            assert service.device_id == "test_device_id"
            assert service.account is None
            assert service.service is None
            assert service.session is None


class TestSpeakerServiceConnect:
    """Tests for SpeakerService.connect method."""
    
    @pytest.mark.asyncio
    async def test_connect_with_uuid(self, mock_account, mock_mina_service, mock_session):
        """Test connecting with UUID device ID."""
        with patch("src.services.speaker.settings") as mock_settings, \
             patch("src.services.speaker.ClientSession", return_value=mock_session), \
             patch("src.services.speaker.MiAccount", return_value=mock_account), \
             patch("src.services.speaker.MiNAService", return_value=mock_mina_service):
            
            mock_settings.mi_user = "test_user"
            mock_settings.mi_pass = "test_pass"
            mock_settings.mi_did = "uuid-1234-5678"
            
            service = SpeakerService()
            await service.connect()
            
            assert service.device_id == "uuid-1234-5678"
            assert service.account == mock_account
            assert service.service == mock_mina_service
    
    @pytest.mark.asyncio
    async def test_connect_with_miot_did(self, mock_account, mock_mina_service, mock_session):
        """Test connecting with numeric MiotDID."""
        with patch("src.services.speaker.settings") as mock_settings, \
             patch("src.services.speaker.ClientSession", return_value=mock_session), \
             patch("src.services.speaker.MiAccount", return_value=mock_account), \
             patch("src.services.speaker.MiNAService", return_value=mock_mina_service):
            
            mock_settings.mi_user = "test_user"
            mock_settings.mi_pass = "test_pass"
            mock_settings.mi_did = "77889911"
            
            service = SpeakerService()
            await service.connect()
            
            # Should be converted to UUID
            assert service.device_id == "uuid-1234-5678"
    
    @pytest.mark.asyncio
    async def test_connect_with_device_name(self, mock_account, mock_mina_service, mock_session):
        """Test connecting with device name."""
        with patch("src.services.speaker.settings") as mock_settings, \
             patch("src.services.speaker.ClientSession", return_value=mock_session), \
             patch("src.services.speaker.MiAccount", return_value=mock_account), \
             patch("src.services.speaker.MiNAService", return_value=mock_mina_service):
            
            mock_settings.mi_user = "test_user"
            mock_settings.mi_pass = "test_pass"
            mock_settings.mi_did = "北京小米音箱"
            
            service = SpeakerService()
            await service.connect()
            
            # Should be converted to UUID
            assert service.device_id == "uuid-1234-5678"
    
    @pytest.mark.asyncio
    async def test_connect_device_not_found(self, mock_account, mock_mina_service, mock_session):
        """Test connecting with non-existent device."""
        with patch("src.services.speaker.settings") as mock_settings, \
             patch("src.services.speaker.ClientSession", return_value=mock_session), \
             patch("src.services.speaker.MiAccount", return_value=mock_account), \
             patch("src.services.speaker.MiNAService", return_value=mock_mina_service):
            
            mock_settings.mi_user = "test_user"
            mock_settings.mi_pass = "test_pass"
            mock_settings.mi_did = "non_existent_device"
            
            service = SpeakerService()
            
            with pytest.raises(ValueError, match="not found"):
                await service.connect()
    
    @pytest.mark.asyncio
    async def test_connect_device_list_error(self, mock_account, mock_session):
        """Test connecting when device list fails."""
        mock_service = MagicMock()
        mock_service.device_list = AsyncMock(side_effect=Exception("Network error"))
        
        with patch("src.services.speaker.settings") as mock_settings, \
             patch("src.services.speaker.ClientSession", return_value=mock_session), \
             patch("src.services.speaker.MiAccount", return_value=mock_account), \
             patch("src.services.speaker.MiNAService", return_value=mock_service):
            
            mock_settings.mi_user = "test_user"
            mock_settings.mi_pass = "test_pass"
            mock_settings.mi_did = "test_device"
            
            service = SpeakerService()
            
            with pytest.raises(Exception, match="Network error"):
                await service.connect()


class TestSpeakerServiceClose:
    """Tests for SpeakerService.close method."""
    
    @pytest.mark.asyncio
    async def test_close_with_session(self, mock_session):
        """Test closing with active session."""
        service = SpeakerService()
        service.session = mock_session
        
        await service.close()
        
        mock_session.close.assert_called_once()
        assert service.session is None
    
    @pytest.mark.asyncio
    async def test_close_without_session(self):
        """Test closing without session."""
        service = SpeakerService()
        service.session = None
        
        # Should not raise error
        await service.close()


class TestSpeakerServicePlayAudioUrl:
    """Tests for SpeakerService.play_audio_url method."""
    
    @pytest.mark.asyncio
    async def test_play_audio_url_success(self, mock_mina_service):
        """Test playing audio URL successfully."""
        service = SpeakerService()
        service.service = mock_mina_service
        service.device_id = "uuid-1234-5678"
        
        result = await service.play_audio_url("http://example.com/audio.mp3")
        
        assert result is True
        mock_mina_service.play_by_url.assert_called_once_with(
            "uuid-1234-5678",
            "http://example.com/audio.mp3"
        )
    
    @pytest.mark.asyncio
    async def test_play_audio_url_empty_result(self, mock_mina_service):
        """Test playing audio URL with empty result."""
        mock_mina_service.play_by_url = AsyncMock(return_value="")
        
        service = SpeakerService()
        service.service = mock_mina_service
        service.device_id = "uuid-1234-5678"
        
        result = await service.play_audio_url("http://example.com/audio.mp3")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_play_audio_url_error_response(self, mock_mina_service):
        """Test playing audio URL with error response."""
        mock_mina_service.play_by_url = AsyncMock(return_value={'code': 1, 'message': 'Error'})
        
        service = SpeakerService()
        service.service = mock_mina_service
        service.device_id = "uuid-1234-5678"
        
        result = await service.play_audio_url("http://example.com/audio.mp3")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_play_audio_url_exception(self, mock_mina_service):
        """Test playing audio URL with exception."""
        mock_mina_service.play_by_url = AsyncMock(side_effect=Exception("Network error"))
        
        service = SpeakerService()
        service.service = mock_mina_service
        service.device_id = "uuid-1234-5678"
        
        result = await service.play_audio_url("http://example.com/audio.mp3")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_play_audio_url_auto_connect(self, mock_account, mock_mina_service, mock_session):
        """Test auto-connecting when service is None."""
        with patch("src.services.speaker.settings") as mock_settings, \
             patch("src.services.speaker.ClientSession", return_value=mock_session), \
             patch("src.services.speaker.MiAccount", return_value=mock_account), \
             patch("src.services.speaker.MiNAService", return_value=mock_mina_service):
            
            mock_settings.mi_user = "test_user"
            mock_settings.mi_pass = "test_pass"
            mock_settings.mi_did = "uuid-1234-5678"
            
            service = SpeakerService()
            result = await service.play_audio_url("http://example.com/audio.mp3")
            
            assert result is True
            assert service.service is not None


class TestSpeakerServicePlayTts:
    """Tests for SpeakerService.play_tts method."""
    
    @pytest.mark.asyncio
    async def test_play_tts_success(self, mock_mina_service):
        """Test playing TTS successfully."""
        service = SpeakerService()
        service.service = mock_mina_service
        service.device_id = "uuid-1234-5678"
        
        result = await service.play_tts("这是测试文本")
        
        assert result is True
        mock_mina_service.text_to_speech.assert_called_once_with(
            "uuid-1234-5678",
            "这是测试文本"
        )
    
    @pytest.mark.asyncio
    async def test_play_tts_exception(self, mock_mina_service):
        """Test playing TTS with exception."""
        mock_mina_service.text_to_speech = AsyncMock(side_effect=Exception("TTS error"))
        
        service = SpeakerService()
        service.service = mock_mina_service
        service.device_id = "uuid-1234-5678"
        
        result = await service.play_tts("测试")
        
        assert result is False


class TestSpeakerServiceSetVolume:
    """Tests for SpeakerService.set_volume method."""
    
    @pytest.mark.asyncio
    async def test_set_volume_success(self, mock_mina_service):
        """Test setting volume successfully."""
        service = SpeakerService()
        service.service = mock_mina_service
        service.device_id = "uuid-1234-5678"
        
        result = await service.set_volume(50)
        
        assert result is True
        mock_mina_service.player_set_volume.assert_called_once_with(
            "uuid-1234-5678",
            50
        )
    
    @pytest.mark.asyncio
    async def test_set_volume_invalid_low(self, mock_mina_service):
        """Test setting volume below 0."""
        service = SpeakerService()
        service.service = mock_mina_service
        service.device_id = "uuid-1234-5678"
        
        result = await service.set_volume(-1)
        
        assert result is False
        mock_mina_service.player_set_volume.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_set_volume_invalid_high(self, mock_mina_service):
        """Test setting volume above 100."""
        service = SpeakerService()
        service.service = mock_mina_service
        service.device_id = "uuid-1234-5678"
        
        result = await service.set_volume(101)
        
        assert result is False
        mock_mina_service.player_set_volume.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_set_volume_boundary_values(self, mock_mina_service):
        """Test setting volume at boundary values."""
        service = SpeakerService()
        service.service = mock_mina_service
        service.device_id = "uuid-1234-5678"
        
        # Test 0
        result = await service.set_volume(0)
        assert result is True
        
        # Test 100
        result = await service.set_volume(100)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_set_volume_exception(self, mock_mina_service):
        """Test setting volume with exception."""
        mock_mina_service.player_set_volume = AsyncMock(side_effect=Exception("Volume error"))
        
        service = SpeakerService()
        service.service = mock_mina_service
        service.device_id = "uuid-1234-5678"
        
        result = await service.set_volume(50)
        
        assert result is False
