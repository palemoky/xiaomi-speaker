"""Edge TTS service for generating natural Chinese audio."""

import hashlib
import logging
from pathlib import Path
from typing import Optional

import edge_tts

from src.config import settings

logger = logging.getLogger(__name__)


class TTSService:
    """Service for text-to-speech conversion using Edge TTS."""

    def __init__(self) -> None:
        """Initialize the TTS service."""
        self.voice = settings.tts_voice
        self.rate = settings.tts_rate
        self.volume = settings.tts_volume
        self.cache_dir = settings.audio_cache_dir
        settings.ensure_audio_cache_dir()

    def _get_cache_filename(self, text: str) -> str:
        """Generate a cache filename based on text hash.

        Args:
            text: The text to convert to speech

        Returns:
            Filename for the cached audio file
        """
        # Create a hash of the text and TTS settings
        content = f"{text}_{self.voice}_{self.rate}_{self.volume}"
        text_hash = hashlib.md5(content.encode()).hexdigest()
        return f"{text_hash}.mp3"

    async def generate_speech(
        self,
        text: str,
        use_cache: bool = True,
    ) -> Path:
        """Generate speech from text using Edge TTS.

        Args:
            text: The text to convert to speech
            use_cache: Whether to use cached audio if available

        Returns:
            Path to the generated audio file

        Raises:
            Exception: If TTS generation fails
        """
        cache_file = self.cache_dir / self._get_cache_filename(text)

        # Return cached file if it exists and caching is enabled
        if use_cache and cache_file.exists():
            logger.info(f"Using cached audio: {cache_file}")
            return cache_file

        try:
            logger.info(f"Generating speech for: {text}")
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume,
            )

            await communicate.save(str(cache_file))
            logger.info(f"Generated audio saved to: {cache_file}")
            return cache_file

        except Exception as e:
            logger.error(f"Failed to generate speech: {e}")
            raise

    async def clear_cache(self, max_age_days: Optional[int] = None) -> int:
        """Clear old cached audio files.

        Args:
            max_age_days: Only delete files older than this many days.
                         If None, delete all cached files.

        Returns:
            Number of files deleted
        """
        import time

        deleted_count = 0

        for audio_file in self.cache_dir.glob("*.mp3"):
            should_delete = False

            if max_age_days is None:
                should_delete = True
            else:
                file_age_days = (
                    time.time() - audio_file.stat().st_mtime
                ) / 86400
                if file_age_days > max_age_days:
                    should_delete = True

            if should_delete:
                try:
                    audio_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted cached file: {audio_file}")
                except Exception as e:
                    logger.error(f"Failed to delete {audio_file}: {e}")

        logger.info(f"Cleared {deleted_count} cached audio files")
        return deleted_count
