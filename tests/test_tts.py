"""Tests for TTS service cache functionality."""

import time
from pathlib import Path
from unittest.mock import patch

import pytest


class TestTTSCacheSize:
    """Tests for cache size calculation and limit enforcement."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path: Path) -> Path:
        """Create a temporary cache directory."""
        cache_dir = tmp_path / "audio_cache"
        cache_dir.mkdir()
        return cache_dir

    @pytest.fixture
    def tts_service(self, temp_cache_dir: Path):
        """Create a TTSService with mocked settings."""
        with patch("src.services.tts.settings") as mock_settings:
            mock_settings.piper_voice_zh = None
            mock_settings.piper_voice_en = "en_US-lessac-medium"
            mock_settings.piper_speaker = 0
            mock_settings.piper_length_scale = 1.0
            mock_settings.audio_cache_dir = temp_cache_dir
            mock_settings.audio_cache_max_size_mb = 1  # 1 MB limit
            mock_settings.ensure_audio_cache_dir = lambda: None

            from src.services.tts import TTSService

            service = TTSService()
            return service

    def _create_cache_file(
        self, cache_dir: Path, name: str, size_kb: int, age_seconds: int = 0
    ) -> Path:
        """Create a dummy cache file with specified size and age."""
        file_path = cache_dir / name
        # Create file with specified size (1 KB = 1024 bytes)
        file_path.write_bytes(b"0" * (size_kb * 1024))
        # Set modification time
        if age_seconds > 0:
            mtime = time.time() - age_seconds
            import os

            os.utime(file_path, (mtime, mtime))
        return file_path

    def test_get_cache_size_empty(self, tts_service, temp_cache_dir: Path):
        """Test cache size is 0 for empty directory."""
        assert tts_service._get_cache_size() == 0

    def test_get_cache_size_with_files(self, tts_service, temp_cache_dir: Path):
        """Test cache size calculation with multiple files."""
        self._create_cache_file(temp_cache_dir, "file1.wav", 100)
        self._create_cache_file(temp_cache_dir, "file2.wav", 200)

        # 100 KB + 200 KB = 300 KB = 307200 bytes
        assert tts_service._get_cache_size() == 300 * 1024

    def test_get_cache_size_ignores_non_wav(self, tts_service, temp_cache_dir: Path):
        """Test that non-wav files are ignored."""
        self._create_cache_file(temp_cache_dir, "file1.wav", 100)
        self._create_cache_file(temp_cache_dir, "file2.txt", 200)

        # Only count .wav files
        assert tts_service._get_cache_size() == 100 * 1024

    def test_enforce_cache_limit_within_limit(self, tts_service, temp_cache_dir: Path):
        """Test no eviction when within limit."""
        # 1 MB limit, create 500 KB of files
        self._create_cache_file(temp_cache_dir, "file1.wav", 500)

        deleted = tts_service._enforce_cache_limit()

        assert deleted == 0
        assert (temp_cache_dir / "file1.wav").exists()

    def test_enforce_cache_limit_deletes_oldest(self, tts_service, temp_cache_dir: Path):
        """Test LRU eviction deletes oldest files first."""
        # 1 MB limit = 1024 KB, create 1500 KB of files
        # oldest file (created 10 seconds ago)
        self._create_cache_file(temp_cache_dir, "oldest.wav", 500, age_seconds=10)
        # middle file (created 5 seconds ago)
        self._create_cache_file(temp_cache_dir, "middle.wav", 500, age_seconds=5)
        # newest file (created just now)
        self._create_cache_file(temp_cache_dir, "newest.wav", 500, age_seconds=0)

        deleted = tts_service._enforce_cache_limit()

        # Should delete oldest file to get under 1 MB
        assert deleted == 1
        assert not (temp_cache_dir / "oldest.wav").exists()
        assert (temp_cache_dir / "middle.wav").exists()
        assert (temp_cache_dir / "newest.wav").exists()

    def test_enforce_cache_limit_deletes_multiple(self, tts_service, temp_cache_dir: Path):
        """Test eviction deletes multiple files if needed."""
        # 1 MB limit = 1024 KB, create 2000 KB of files
        self._create_cache_file(temp_cache_dir, "a.wav", 500, age_seconds=30)
        self._create_cache_file(temp_cache_dir, "b.wav", 500, age_seconds=20)
        self._create_cache_file(temp_cache_dir, "c.wav", 500, age_seconds=10)
        self._create_cache_file(temp_cache_dir, "d.wav", 500, age_seconds=0)

        deleted = tts_service._enforce_cache_limit()

        # Should delete 2 oldest files (a and b) to get under 1 MB
        assert deleted == 2
        assert not (temp_cache_dir / "a.wav").exists()
        assert not (temp_cache_dir / "b.wav").exists()
        assert (temp_cache_dir / "c.wav").exists()
        assert (temp_cache_dir / "d.wav").exists()


class TestTTSCacheLimitZero:
    """Tests for unlimited cache (max_size = 0)."""

    @pytest.fixture
    def tts_service_unlimited(self, tmp_path: Path):
        """Create a TTSService with unlimited cache."""
        cache_dir = tmp_path / "audio_cache"
        cache_dir.mkdir()

        with patch("src.services.tts.settings") as mock_settings:
            mock_settings.piper_voice_zh = None
            mock_settings.piper_voice_en = "en_US-lessac-medium"
            mock_settings.piper_speaker = 0
            mock_settings.piper_length_scale = 1.0
            mock_settings.audio_cache_dir = cache_dir
            mock_settings.audio_cache_max_size_mb = 0  # Unlimited
            mock_settings.ensure_audio_cache_dir = lambda: None

            from src.services.tts import TTSService

            service = TTSService()
            service._cache_dir_for_test = cache_dir
            return service

    def test_cache_limit_zero_means_unlimited(self, tts_service_unlimited, tmp_path: Path):
        """Test that 0 means no eviction happens."""
        cache_dir = tts_service_unlimited._cache_dir_for_test

        # Create large files (10 MB each)
        for i in range(5):
            file_path = cache_dir / f"large{i}.wav"
            file_path.write_bytes(b"0" * (10 * 1024 * 1024))

        deleted = tts_service_unlimited._enforce_cache_limit()

        # No files should be deleted
        assert deleted == 0
        assert len(list(cache_dir.glob("*.wav"))) == 5
