"""Piper TTS service for generating natural speech locally."""

import hashlib
import logging
import wave
from pathlib import Path
from typing import Optional

from piper import PiperVoice

from src.config import settings
from src.utils.language import detect_language

logger = logging.getLogger(__name__)


class TTSService:
    """Service for text-to-speech conversion using Piper TTS."""

    def __init__(self) -> None:
        """Initialize the TTS service."""
        self.voice_zh_name = settings.piper_voice_zh
        self.voice_en_name = settings.piper_voice_en
        self.speaker = settings.piper_speaker
        self.length_scale = settings.piper_length_scale
        self.cache_dir = settings.audio_cache_dir
        settings.ensure_audio_cache_dir()
        
        # Model directory (default Piper location or custom)
        self.models_dir = Path.home() / ".local" / "share" / "piper-voices"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Lazy load voices (will be loaded on first use)
        self.voice_zh: Optional[PiperVoice] = None
        self.voice_en: Optional[PiperVoice] = None

    def _find_model_file(self, voice_name: str) -> Optional[Path]:
        """Find the .onnx model file for a voice.

        Args:
            voice_name: Voice name (e.g., 'zh_CN-huayan-medium')

        Returns:
            Path to .onnx file if found, None otherwise
        """
        # Search in models directory
        for model_file in self.models_dir.rglob(f"{voice_name}.onnx"):
            logger.debug(f"Found model: {model_file}")
            return model_file
        
        # Also check in audio_cache/voices (for Docker volume mounts)
        alt_dir = self.cache_dir / "voices"
        if alt_dir.exists():
            for model_file in alt_dir.rglob(f"{voice_name}.onnx"):
                logger.debug(f"Found model in cache: {model_file}")
                return model_file
        
        return None

    def _download_voice_model(self, voice_name: str) -> Path:
        """Download voice model if not found.

        Args:
            voice_name: Voice name (e.g., 'zh_CN-huayan-medium')

        Returns:
            Path to downloaded .onnx file

        Raises:
            Exception: If download fails
        """
        import urllib.request

        logger.info(f"Voice model not found, downloading: {voice_name}")
        
        # Construct download URL
        base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
        
        # Parse voice name to get path components
        if voice_name.startswith("zh_CN"):
            lang_path = "zh/zh_CN"
            voice_parts = voice_name.split("-")
            voice_id = voice_parts[1]  # huayan
            quality = voice_parts[2]    # medium
        elif voice_name.startswith("en_US"):
            lang_path = "en/en_US"
            voice_parts = voice_name.split("-")
            voice_id = voice_parts[1]  # lessac
            quality = voice_parts[2]    # medium
        else:
            raise ValueError(f"Unsupported voice: {voice_name}")
        
        # Create target directory
        voice_dir = self.models_dir / lang_path / voice_id / quality
        voice_dir.mkdir(parents=True, exist_ok=True)
        
        # Download .onnx and .onnx.json files
        files = [
            f"{voice_name}.onnx",
            f"{voice_name}.onnx.json",
        ]
        
        for filename in files:
            url = f"{base_url}/{lang_path}/{voice_id}/{quality}/{filename}"
            dest = voice_dir / filename
            
            logger.info(f"Downloading: {filename}")
            try:
                urllib.request.urlretrieve(url, dest)
                logger.info(f"Downloaded: {dest}")
            except Exception as e:
                logger.error(f"Failed to download {filename}: {e}")
                raise
        
        model_path = voice_dir / f"{voice_name}.onnx"
        logger.info(f"Voice model downloaded successfully: {model_path}")
        return model_path

    def _load_voice(self, language: str) -> PiperVoice:
        """Load Piper voice model for the specified language.

        Args:
            language: 'zh' or 'en'

        Returns:
            Loaded PiperVoice instance

        Raises:
            Exception: If voice model cannot be loaded
        """
        if language == 'zh':
            if self.voice_zh is None:
                voice_name = self.voice_zh_name
                
                # Check if Chinese voice is configured
                if not voice_name:
                    raise ValueError(
                        "PIPER_VOICE_ZH is not configured. "
                        "Either set it in .env or the system will use speaker's built-in TTS for Chinese."
                    )
                
                logger.info(f"Loading Chinese voice: {voice_name}")
                
                model_path = self._find_model_file(voice_name)
                if model_path is None:
                    # Auto-download if not found
                    logger.info(f"Model not found locally, will download: {voice_name}")
                    model_path = self._download_voice_model(voice_name)
                
                self.voice_zh = PiperVoice.load(str(model_path))
                logger.info(f"Chinese voice loaded from: {model_path}")
            
            return self.voice_zh
        else:
            if self.voice_en is None:
                voice_name = self.voice_en_name
                logger.info(f"Loading English voice: {voice_name}")
                
                model_path = self._find_model_file(voice_name)
                if model_path is None:
                    # Auto-download if not found
                    logger.info(f"Model not found locally, will download: {voice_name}")
                    model_path = self._download_voice_model(voice_name)
                
                self.voice_en = PiperVoice.load(str(model_path))
                logger.info(f"English voice loaded from: {model_path}")
            
            return self.voice_en

    def _get_cache_filename(self, text: str, language: str) -> str:
        """Generate a cache filename based on text hash and language.

        Args:
            text: The text to convert to speech
            language: Language code ('zh' or 'en')

        Returns:
            Filename for the cached audio file
        """
        # Create a hash of the text, language, and TTS settings
        content = f"{text}_{language}_{self.speaker}_{self.length_scale}"
        text_hash = hashlib.md5(content.encode()).hexdigest()
        return f"{text_hash}.wav"

    async def generate_speech(
        self,
        text: str,
        use_cache: bool = True,
    ) -> Path:
        """Generate speech from text using Piper TTS with language detection.

        Args:
            text: The text to convert to speech
            use_cache: Whether to use cached audio if available

        Returns:
            Path to the generated audio file (WAV format)

        Raises:
            Exception: If TTS generation fails
        """
        # Detect language
        language = detect_language(text)
        logger.info(f"Detected language: {language} for text: {text[:50]}...")
        
        cache_file = self.cache_dir / self._get_cache_filename(text, language)

        # Return cached file if it exists and caching is enabled
        if use_cache and cache_file.exists() and cache_file.stat().st_size > 0:
            logger.info(f"Using cached audio: {cache_file}")
            return cache_file

        try:
            logger.info(f"Generating speech with Piper TTS ({language})")
            
            # Load appropriate voice
            voice = self._load_voice(language)
            
            # Generate audio using synthesize_wav
            with wave.open(str(cache_file), "wb") as wav_file:
                voice.synthesize_wav(text, wav_file)
            
            # Verify the file was created
            if cache_file.exists() and cache_file.stat().st_size > 0:
                logger.info(f"Generated audio saved to: {cache_file} ({cache_file.stat().st_size} bytes)")
                return cache_file
            else:
                raise Exception("Generated file is empty or does not exist")

        except Exception as e:
            logger.error(f"Failed to generate speech: {e}")
            # Clean up failed file
            if cache_file.exists():
                cache_file.unlink()
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

        for audio_file in self.cache_dir.glob("*.wav"):
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

