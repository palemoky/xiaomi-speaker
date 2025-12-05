"""MiService integration for Xiaomi speaker control."""

import asyncio
import logging
from typing import Optional

from aiohttp import ClientSession
from miservice import MiAccount, MiNAService

from src.config import settings

logger = logging.getLogger(__name__)


class SpeakerService:
    """Service for controlling Xiaomi speaker via MiService (async)."""

    def __init__(self) -> None:
        """Initialize the speaker service."""
        self.session: Optional[ClientSession] = None
        self.account: Optional[MiAccount] = None
        self.service: Optional[MiNAService] = None
        self.device_id = settings.mi_did

    async def connect(self) -> None:
        """Connect to Xiaomi account and initialize service.

        Raises:
            Exception: If connection fails
        """
        try:
            logger.info("Connecting to Xiaomi account...")
            logger.debug(f"MI_USER: {settings.mi_user}, MI_DID: {settings.mi_did}")
            
            # Create aiohttp session if not exists
            if not self.session:
                self.session = ClientSession()
            
            # miservice-fork's MiAccount requires session, username, and password
            self.account = MiAccount(
                session=self.session,
                username=settings.mi_user,
                password=settings.mi_pass
            )
            
            self.service = MiNAService(self.account)
            logger.info("Successfully connected to Xiaomi account")
        except Exception as e:
            logger.error(f"Failed to connect to Xiaomi account: {e}")
            logger.error(f"Please check MI_USER, MI_PASS, and MI_DID environment variables")
            raise

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def play_audio_url(self, audio_url: str) -> bool:
        """Play audio from URL on the speaker.

        Args:
            audio_url: HTTP URL of the audio file to play

        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            await self.connect()

        try:
            logger.info(f"Playing audio from URL: {audio_url}")
            logger.debug(f"Device ID: {self.device_id}, Type: {type(self.device_id)}")
            
            # Use MiNAService to play audio by URL
            result = await self.service.play_by_url(self.device_id, audio_url)
            
            logger.info(f"play_by_url result: {result}")
            logger.debug(f"Result type: {type(result)}")
            
            # Check if result indicates success
            # MiNA API might return different formats
            if result is None or result == "":
                logger.info("Audio playback initiated successfully (no error)")
                return True
            elif isinstance(result, dict):
                if result.get("code") == 0 or result.get("status") == "success":
                    logger.info("Audio playback initiated successfully")
                    return True
                else:
                    logger.error(f"API returned error: {result}")
                    return False
            else:
                # Unknown result format, log it
                logger.warning(f"Unexpected result format: {result}")
                return True  # Assume success if no exception
                
        except Exception as e:
            logger.error(f"Failed to play audio: {e}", exc_info=True)
            return False

    async def play_tts(self, text: str) -> bool:
        """Play text-to-speech on the speaker.

        Args:
            text: Text to speak

        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            await self.connect()

        try:
            logger.info(f"Playing TTS: {text}")
            # Use MiNAService text_to_speech method
            result = await self.service.text_to_speech(self.device_id, text)
            logger.info(f"TTS playback initiated: {result}")
            return True
        except Exception as e:
            logger.error(f"Failed to play TTS: {e}")
            return False

    async def set_volume(self, volume: int) -> bool:
        """Set speaker volume.

        Args:
            volume: Volume level (0-100)

        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            await self.connect()

        if not 0 <= volume <= 100:
            logger.error(f"Invalid volume level: {volume}")
            return False

        try:
            logger.info(f"Setting volume to: {volume}")
            # Use MiNAService player_set_volume method
            result = await self.service.player_set_volume(self.device_id, volume)
            logger.info(f"Volume set: {result}")
            return True
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False

