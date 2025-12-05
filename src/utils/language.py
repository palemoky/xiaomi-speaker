"""Language detection utilities for text analysis."""

# Constants for Chinese character detection
CHINESE_UNICODE_START = '\u4e00'
CHINESE_UNICODE_END = '\u9fff'
CHINESE_THRESHOLD = 0.3  # 30% Chinese characters to be considered Chinese text


def count_chinese_chars(text: str) -> int:
    """Count Chinese characters in text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Number of Chinese characters (CJK Unified Ideographs)
    """
    return sum(1 for c in text if CHINESE_UNICODE_START <= c <= CHINESE_UNICODE_END)


def detect_language(text: str) -> str:
    """Detect the primary language of the text.
    
    Args:
        text: Text to analyze
        
    Returns:
        'zh' for Chinese, 'en' for English
    """
    chinese_chars = count_chinese_chars(text)
    total_chars = len(text.strip())
    
    if total_chars == 0:
        return 'zh'  # Default to Chinese
    
    chinese_ratio = chinese_chars / total_chars
    return 'zh' if chinese_ratio > CHINESE_THRESHOLD else 'en'


def is_chinese(text: str) -> bool:
    """Check if text is primarily Chinese.
    
    Args:
        text: Text to analyze
        
    Returns:
        True if text is primarily Chinese (>30% Chinese characters)
    """
    chinese_chars = count_chinese_chars(text)
    total_chars = len(text.strip())
    
    if total_chars == 0:
        return False
    
    chinese_ratio = chinese_chars / total_chars
    return chinese_ratio > CHINESE_THRESHOLD


def get_chinese_ratio(text: str) -> float:
    """Get the ratio of Chinese characters in text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Ratio of Chinese characters (0.0 to 1.0)
    """
    chinese_chars = count_chinese_chars(text)
    total_chars = len(text.strip())
    
    if total_chars == 0:
        return 0.0
    
    return chinese_chars / total_chars
