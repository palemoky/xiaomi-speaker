"""MiService integration for Xiaomi speaker control."""

import logging
import os
from pathlib import Path
from typing import Optional

from miservice import MiAccount, MiNAService

from src.config import settings

logger = logging.getLogger(__name__)


class SpeakerService:
    """Service for controlling Xiaomi speaker via MiService."""

    def __init__(self) -> None:
        """Initialize the speaker service."""
        self.account: Optional[MiAccount] = None
        self.service: Optional[MiNAService] = None
        self.device_id = settings.mi_did
        self._setup_credentials()

    def _setup_credentials(self) -> None:
        """Set up MiService credentials from settings."""
        # MiService uses environment variables
        os.environ["MI_USER"] = settings.mi_user
        os.environ["MI_PASS"] = settings.mi_pass
        os.environ["MI_DID"] = settings.mi_did

    def connect(self) -> None:
        """Connect to Xiaomi account and initialize service.

        Raises:
            Exception: If connection fails
        """
        try:
            logger.info("Connecting to Xiaomi account...")
            self.account = MiAccount(
                settings.mi_user,
                settings.mi_pass,
            )
            self.service = MiNAService(self.account)
            logger.info("Successfully connected to Xiaomi account")
        except Exception as e:
            logger.error(f"Failed to connect to Xiaomi account: {e}")
            raise

    def play_audio_url(self, audio_url: str) -> bool:
        """Play audio from URL on the speaker.

        Args:
            audio_url: HTTP URL of the audio file to play

        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            self.connect()

        try:
            logger.info(f"Playing audio from URL: {audio_url}")
            # Use MiNAService to play audio by URL
            result = self.service.play_by_url(self.device_id, audio_url)
            logger.info(f"Audio playback initiated: {result}")
            return True
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            return False

    def play_tts(self, text: str) -> bool:
        """Play text-to-speech on the speaker.

        Args:
            text: Text to speak

        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            self.connect()

        try:
            logger.info(f"Playing TTS: {text}")
            # Use MiNAService text_to_speech method
            result = self.service.text_to_speech(self.device_id, text)
            logger.info(f"TTS playback initiated: {result}")
            return True
        except Exception as e:
            logger.error(f"Failed to play TTS: {e}")
            return False

    def set_volume(self, volume: int) -> bool:
        """Set speaker volume.

        Args:
            volume: Volume level (0-100)

        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            self.connect()

        if not 0 <= volume <= 100:
            logger.error(f"Invalid volume level: {volume}")
            return False

        try:
            logger.info(f"Setting volume to: {volume}")
            # Use MiNAService player_set_volume method
            result = self.service.player_set_volume(self.device_id, volume)
            logger.info(f"Volume set: {result}")
            return True
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False

