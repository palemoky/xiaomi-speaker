"""Tests for language detection utilities."""

import pytest
from src.utils.language import (
    count_chinese_chars,
    detect_language,
    is_chinese,
    get_chinese_ratio,
    CHINESE_THRESHOLD,
)


class TestCountChineseChars:
    """Tests for count_chinese_chars function."""
    
    def test_pure_chinese(self):
        """Test counting pure Chinese text."""
        text = "这是一段中文文本"
        assert count_chinese_chars(text) == 8  # 8 Chinese characters
    
    def test_pure_english(self):
        """Test counting pure English text."""
        text = "This is English text"
        assert count_chinese_chars(text) == 0
    
    def test_mixed_text(self):
        """Test counting mixed Chinese and English text."""
        text = "GitHub Actions 构建失败"
        assert count_chinese_chars(text) == 4
    
    def test_empty_string(self):
        """Test counting empty string."""
        assert count_chinese_chars("") == 0
    
    def test_punctuation_only(self):
        """Test counting punctuation."""
        text = "！@#￥%……&*（）"
        assert count_chinese_chars(text) == 0


class TestDetectLanguage:
    """Tests for detect_language function."""
    
    def test_detect_chinese(self):
        """Test detecting Chinese text."""
        text = "这是一段中文文本"
        assert detect_language(text) == "zh"
    
    def test_detect_english(self):
        """Test detecting English text."""
        text = "This is English text"
        assert detect_language(text) == "en"
    
    def test_detect_mixed_mostly_chinese(self):
        """Test detecting mixed text with majority Chinese."""
        # "构建失败：仓库" = 6 Chinese chars, total ~30 chars = 20% < 30% threshold
        # Use a better example with more Chinese
        text = "GitHub Actions 构建失败：仓库 用户名/项目名"
        assert detect_language(text) == "zh"
    
    def test_detect_mixed_mostly_english(self):
        """Test detecting mixed text with majority English."""
        text = "Build failed for 仓库"
        assert detect_language(text) == "en"
    
    def test_detect_empty_defaults_to_chinese(self):
        """Test that empty string defaults to Chinese."""
        assert detect_language("") == "zh"
    
    def test_detect_threshold_boundary(self):
        """Test detection at threshold boundary."""
        # Exactly at threshold (30%)
        text = "a" * 7 + "中文字"  # 3 Chinese out of 10 = 30%
        assert detect_language(text) == "en"  # <= threshold
        
        # Just above threshold
        text = "a" * 6 + "中文字"  # 3 Chinese out of 9 = 33.3%
        assert detect_language(text) == "zh"  # > threshold


class TestIsChinese:
    """Tests for is_chinese function."""
    
    def test_is_chinese_true(self):
        """Test Chinese text returns True."""
        assert is_chinese("这是中文") is True
    
    def test_is_chinese_false(self):
        """Test English text returns False."""
        assert is_chinese("This is English") is False
    
    def test_is_chinese_empty(self):
        """Test empty string returns False."""
        assert is_chinese("") is False
    
    def test_is_chinese_mixed(self):
        """Test mixed text based on ratio."""
        # Mostly Chinese (>30%)
        assert is_chinese("GitHub Actions 构建失败：仓库 用户名/项目名") is True
        # Mostly English (<30%)
        assert is_chinese("Build failed for 仓库") is False


class TestGetChineseRatio:
    """Tests for get_chinese_ratio function."""
    
    def test_ratio_pure_chinese(self):
        """Test ratio for pure Chinese text."""
        text = "中文"
        assert get_chinese_ratio(text) == 1.0
    
    def test_ratio_pure_english(self):
        """Test ratio for pure English text."""
        text = "English"
        assert get_chinese_ratio(text) == 0.0
    
    def test_ratio_mixed(self):
        """Test ratio for mixed text."""
        text = "a中b文c"  # 2 Chinese out of 5
        assert get_chinese_ratio(text) == 0.4
    
    def test_ratio_empty(self):
        """Test ratio for empty string."""
        assert get_chinese_ratio("") == 0.0
    
    def test_ratio_with_spaces(self):
        """Test ratio calculation strips spaces."""
        text = "  中文  "
        # After strip: "中文" = 2 chars
        assert get_chinese_ratio(text) == 1.0


class TestConstants:
    """Tests for module constants."""
    
    def test_threshold_value(self):
        """Test that threshold is set correctly."""
        assert CHINESE_THRESHOLD == 0.3
