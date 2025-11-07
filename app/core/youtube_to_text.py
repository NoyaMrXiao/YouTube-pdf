"""
完整的YouTube視頻轉文本流程
優先使用字幕，如果字幕不可用則回退到音頻下載和轉錄
"""
import os
import sys
from pathlib import Path
from typing import Optional
from app.core.download_youtube_audio import download_youtube_audio
from app.core.transcribe_audio import transcribe_audio, save_transcription_result
from app.core.get_youtube_subtitles import get_available_subtitles, get_youtube_subtitles
from app.core.parse_subtitle import subtitle_to_transcription_result


def youtube_to_text(
    url: str,
    model_name: str = "base",
    device: str = "auto",
    batch_size: int = 16,
    language: Optional[str] = None,
    diarize: bool = False,
    hf_token: Optional[str] = None,
    output_dir: Optional[str] = None,
    keep_audio: bool = False,
    prefer_subtitles: bool = True
) -> dict:
    """
    完整流程：從YouTube URL獲取文本
    優先使用字幕，如果字幕不可用則下載音頻並轉錄
    
    參數:
        url (str): YouTube視頻URL
        model_name (str): Whisper模型名稱（僅在字幕不可用時使用）
        device (str): 計算設備（僅在字幕不可用時使用）
        batch_size (int): 批次大小（僅在字幕不可用時使用）
        language (str, optional): 語言代碼，用於選擇字幕或轉錄語言
        diarize (bool): 是否進行說話人分離（僅在字幕不可用時使用，字幕不支持說話人分離）
        hf_token (str, optional): HuggingFace token（僅在字幕不可用時使用）
        output_dir (str, optional): 輸出目錄
        keep_audio (bool): 是否保留下載的音頻文件（僅在字幕不可用時使用）
        prefer_subtitles (bool): 是否優先使用字幕（默認True）
    
    返回:
        dict: 轉錄結果，格式與transcribe_audio返回的格式相同
    """
    print("=" * 60)
    print("YouTube 視頻轉文本流程")
    print("=" * 60)
    
    # 設置輸出目錄
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), 'downloads')
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 優先嘗試使用字幕
    if prefer_subtitles:
        print("\n[步驟 1] 正在檢查可用字幕...")
        available_subtitles = get_available_subtitles(url)
        
        if available_subtitles:
            # 選擇語言
            target_language = language or 'en'
            
            # 如果指定語言不可用，嘗試使用第一個可用語言
            if target_language not in available_subtitles:
                target_language = list(available_subtitles.keys())[0]
                print(f"⚠ 指定語言不可用，使用: {target_language}")
            
            print(f"✓ 找到字幕，語言: {target_language} ({available_subtitles[target_language].get('name', target_language)})")
            print(f"  類型: {'手動' if available_subtitles[target_language].get('type') == 'manual' else '自動'}")
            
            # 下載字幕
            print("\n[步驟 2] 正在下載字幕...")
            subtitle_result = get_youtube_subtitles(
                url,
                languages=[target_language],
                output_dir=output_dir,
                subtitle_format='srt'
            )
            
            if subtitle_result['success'] and subtitle_result['files']:
                subtitle_file = subtitle_result['files'][0]
                print(f"✓ 字幕下載成功: {subtitle_file}")
                
                # 解析字幕並轉換為轉錄結果格式
                print("\n[步驟 3] 正在解析字幕...")
                result = subtitle_to_transcription_result(
                    subtitle_file,
                    language=target_language
                )
                
                # 保存結果（使用與transcribe_audio相同的格式）
                video_title = subtitle_result.get('video_title', 'video')
                base_name = Path(subtitle_file).stem.replace(f'.{target_language}', '').replace(f'_{target_language}', '')
                if not base_name or base_name == Path(subtitle_file).stem:
                    base_name = video_title.replace(' ', '_')[:50]  # 限制長度
                
                output_path = save_transcription_result(
                    result,
                    output_dir,
                    base_name
                )
                
                result['output_file'] = output_path
                result['method'] = 'subtitles'
                result['subtitle_file'] = subtitle_file
                result['video_title'] = video_title
                result['video_id'] = subtitle_result.get('video_id', '')
                
                print(f"\n✓ 完成！使用字幕方法")
                print(f"輸出文件: {output_path}")
                
                if diarize:
                    print("\n⚠ 注意: 字幕不支持說話人分離，已跳過此功能")
                
                return result
            else:
                print("⚠ 字幕下載失敗，回退到音頻轉錄方法...")
        else:
            print("⚠ 沒有可用字幕，使用音頻轉錄方法...")
    
    # 回退到原來的音頻下載+轉錄方法
    print("\n[步驟 1/2] 正在下載YouTube音頻...")
    audio_file = download_youtube_audio(url, output_dir=output_dir)
    
    if not audio_file:
        raise Exception("音頻下載失敗")
    
    print("\n[步驟 2/2] 正在轉錄音頻為文本...")
    result = transcribe_audio(
        audio_file,
        model_name=model_name,
        device=device,
        batch_size=batch_size,
        language=language,
        diarize=diarize,
        hf_token=hf_token,
        output_dir=output_dir
    )
    
    result['method'] = 'transcription'
    result['audio_file'] = audio_file
    
    # 可選：刪除音頻文件
    if not keep_audio and os.path.exists(audio_file):
        try:
            os.remove(audio_file)
            print(f"\n已刪除臨時音頻文件: {audio_file}")
        except:
            print(f"\n⚠ 無法刪除音頻文件: {audio_file}")
    
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python youtube_to_text.py <YouTube_URL> [模型名稱]")
        print("示例: python youtube_to_text.py https://www.youtube.com/watch?v=VIDEO_ID base")
        sys.exit(1)
    
    url = sys.argv[1]
    model_name = sys.argv[2] if len(sys.argv) > 2 else "base"
    hf_token = os.getenv("HF_TOKEN")
    
    try:
        result = youtube_to_text(
            url,
            model_name=model_name,
            diarize=False,  # 設置為True並提供HF_TOKEN以啟用說話人分離
            hf_token=hf_token,
            keep_audio=True  # 保留音頻文件
        )
        
        print("\n" + "=" * 60)
        print("流程完成！")
        print("=" * 60)
        print(f"\n輸出文件: {result.get('output_file', 'Unknown')}")
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()

