#!/usr/bin/env python3
"""手动下载 Piper TTS 语音模型"""

import urllib.request
from pathlib import Path

def download_file(url: str, dest: Path):
    """下载文件"""
    print(f"  下载: {url}")
    urllib.request.urlretrieve(url, dest)
    print(f"  保存到: {dest}")

def download_voice(voice_name: str, models_dir: Path):
    """下载语音模型和配置文件"""
    print(f"\n📥 下载语音模型: {voice_name}")
    
    # 构建 URL (从 Hugging Face)
    base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
    
    # 根据语音名称构建路径
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
        print(f"❌ 不支持的语音: {voice_name}")
        return False
    
    # 创建目标目录
    voice_dir = models_dir / lang_path / voice_id / quality
    voice_dir.mkdir(parents=True, exist_ok=True)
    
    # 下载 .onnx 和 .onnx.json 文件
    files = [
        f"{voice_name}.onnx",
        f"{voice_name}.onnx.json",
    ]
    
    try:
        for filename in files:
            url = f"{base_url}/{lang_path}/{voice_id}/{quality}/{filename}"
            dest = voice_dir / filename
            
            if dest.exists():
                print(f"  ⏭️  已存在: {filename}")
                continue
            
            download_file(url, dest)
        
        print(f"✅ {voice_name} 下载完成")
        return True
    except Exception as e:
        print(f"❌ {voice_name} 下载失败: {e}")
        return False

def main():
    """下载所需的语音模型"""
    models_dir = Path.home() / ".local" / "share" / "piper-voices"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    voices = [
        "zh_CN-huayan-medium",
        "en_US-lessac-medium",
    ]
    
    print("=" * 60)
    print("Piper TTS 语音模型下载工具")
    print(f"目标目录: {models_dir}")
    print("=" * 60)
    
    success_count = 0
    for voice in voices:
        if download_voice(voice, models_dir):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"完成！成功下载 {success_count}/{len(voices)} 个语音模型")
    print("=" * 60)

if __name__ == "__main__":
    main()
