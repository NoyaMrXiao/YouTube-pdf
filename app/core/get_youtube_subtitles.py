"""
獲取YouTube視頻字幕
使用yt-dlp庫直接獲取字幕，支持自動生成和手動上傳的字幕
"""
import yt_dlp
import os
from pathlib import Path
from typing import Optional, List, Dict, Union


def get_available_subtitles(url: str) -> Dict[str, Dict]:
    """
    獲取視頻可用的字幕列表
    
    參數:
        url (str): YouTube視頻URL
    
    返回:
        dict: 可用字幕的字典，格式為 {語言代碼: {字幕信息}}
            例如: {'en': {'ext': 'vtt', 'name': 'English'}, ...}
    """
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})
            
            # 合併手動字幕和自動字幕
            all_subtitles = {}
            
            # 添加手動字幕（優先）
            for lang, subs in subtitles.items():
                if subs:
                    all_subtitles[lang] = {
                        'name': subs[0].get('name', lang),
                        'ext': subs[0].get('ext', 'vtt'),
                        'type': 'manual'
                    }
            
            # 添加自動字幕（如果該語言沒有手動字幕）
            for lang, subs in automatic_captions.items():
                if lang not in all_subtitles and subs:
                    all_subtitles[lang] = {
                        'name': subs[0].get('name', lang),
                        'ext': subs[0].get('ext', 'vtt'),
                        'type': 'auto'
                    }
            
            return all_subtitles
    except Exception as e:
        print(f"❌ 獲取字幕列表失敗: {e}")
        return {}


def get_youtube_subtitles(
    url: str,
    languages: Optional[Union[str, List[str]]] = None,
    output_dir: Optional[str] = None,
    filename: Optional[str] = None,
    subtitle_format: str = 'srt',
    write_auto_sub: bool = True,
    prefer_manual: bool = True
) -> Dict[str, Union[str, Dict]]:
    """
    下載YouTube視頻字幕
    
    參數:
        url (str): YouTube視頻URL
        languages (str | List[str], optional): 要下載的語言代碼，例如 'en', 'zh', ['en', 'zh']
            如果為None，則下載所有可用字幕
        output_dir (str, optional): 輸出目錄，默認為當前目錄下的 'downloads' 文件夾
        filename (str, optional): 輸出文件名（不含擴展名），如果為None則使用視頻標題
        subtitle_format (str): 字幕格式，可選: 'srt', 'vtt', 'ttml', 'json3'
        write_auto_sub (bool): 是否下載自動生成的字幕（如果手動字幕不可用）
        prefer_manual (bool): 是否優先使用手動字幕而非自動字幕
    
    返回:
        dict: 包含下載結果的字典
            {
                'success': bool,
                'files': List[str],  # 下載的文件路徑列表
                'video_title': str,
                'video_id': str,
                'subtitles_info': Dict  # 每個語言的字幕信息
            }
    """
    # 設置輸出目錄
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), 'downloads')
    
    # 創建輸出目錄（如果不存在）
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 處理語言參數
    if languages is None:
        # 獲取所有可用字幕
        available = get_available_subtitles(url)
        languages = list(available.keys())
    elif isinstance(languages, str):
        languages = [languages]
    
    if not languages:
        return {
            'success': False,
            'error': '沒有可用的字幕',
            'files': [],
            'video_title': '',
            'video_id': '',
            'subtitles_info': {}
        }
    
    # 配置yt-dlp選項
    ydl_opts = {
        'writesubtitles': True,  # 下載字幕
        'writeautomaticsub': write_auto_sub,  # 下載自動字幕
        'subtitleslangs': languages,  # 指定語言
        'subtitlesformat': subtitle_format,  # 字幕格式
        'skip_download': True,  # 不下載視頻/音頻
        'quiet': False,
        'no_warnings': False,
    }
    
    # 設置輸出文件名模板
    if filename:
        outtmpl = os.path.join(output_dir, f'{filename}.%(ext)s')
    else:
        outtmpl = os.path.join(output_dir, '%(title)s.%(ext)s')
    
    ydl_opts['outtmpl'] = outtmpl
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 獲取視頻信息
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'Unknown')
            video_id = info.get('id', 'Unknown')
            
            print(f"正在獲取字幕: {video_title}")
            print(f"視頻ID: {video_id}")
            print(f"語言: {', '.join(languages)}")
            print(f"格式: {subtitle_format}")
            
            # 下載字幕
            ydl.download([url])
            
            # 查找下載的字幕文件
            subtitle_files = []
            subtitle_extensions = [subtitle_format, 'srt', 'vtt', 'ttml']
            
            for ext in subtitle_extensions:
                pattern = f'*.{ext}'
                files = list(Path(output_dir).glob(pattern))
                # 按修改時間排序，獲取最新的文件
                if files:
                    # 過濾出包含語言代碼的文件
                    for lang in languages:
                        for file in files:
                            if lang in file.stem.lower() or len(languages) == 1:
                                if file not in subtitle_files:
                                    subtitle_files.append(str(file))
            
            # 如果沒找到，嘗試查找所有字幕文件
            if not subtitle_files:
                for ext in subtitle_extensions:
                    files = list(Path(output_dir).glob(f'*.{ext}'))
                    if files:
                        latest = max(files, key=os.path.getmtime)
                        if str(latest) not in subtitle_files:
                            subtitle_files.append(str(latest))
            
            # 獲取字幕信息
            subtitles_info = {}
            available_subs = get_available_subtitles(url)
            for lang in languages:
                if lang in available_subs:
                    subtitles_info[lang] = available_subs[lang]
            
            result = {
                'success': len(subtitle_files) > 0,
                'files': subtitle_files,
                'video_title': video_title,
                'video_id': video_id,
                'subtitles_info': subtitles_info
            }
            
            if subtitle_files:
                print(f"\n✓ 成功下載 {len(subtitle_files)} 個字幕文件:")
                for file in subtitle_files:
                    print(f"  - {file}")
            else:
                print("\n⚠ 未找到下載的字幕文件")
                result['error'] = '未找到字幕文件'
            
            return result
            
    except yt_dlp.utils.DownloadError as e:
        error_msg = f"下載錯誤: {e}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'files': [],
            'video_title': '',
            'video_id': '',
            'subtitles_info': {}
        }
    except Exception as e:
        error_msg = f"發生錯誤: {e}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'files': [],
            'video_title': '',
            'video_id': '',
            'subtitles_info': {}
        }


def get_subtitle_text(
    url: str,
    language: str = 'en',
    subtitle_format: str = 'srt'
) -> Optional[str]:
    """
    直接獲取字幕文本內容（不下載文件）
    
    參數:
        url (str): YouTube視頻URL
        language (str): 語言代碼，例如 'en', 'zh'
        subtitle_format (str): 字幕格式，可選: 'srt', 'vtt', 'ttml', 'json3'
    
    返回:
        str: 字幕文本內容，如果失敗則返回None
    """
    try:
        import tempfile
        
        # 創建臨時目錄
        with tempfile.TemporaryDirectory() as temp_dir:
            result = get_youtube_subtitles(
                url,
                languages=[language],
                output_dir=temp_dir,
                subtitle_format=subtitle_format
            )
            
            if result['success'] and result['files']:
                # 讀取第一個字幕文件
                with open(result['files'][0], 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return None
    except Exception as e:
        print(f"❌ 獲取字幕文本失敗: {e}")
        return None


def list_available_subtitles(url: str) -> None:
    """
    列出視頻所有可用的字幕
    
    參數:
        url (str): YouTube視頻URL
    """
    subtitles = get_available_subtitles(url)
    
    if not subtitles:
        print("❌ 該視頻沒有可用的字幕")
        return
    
    print(f"\n可用字幕 ({len(subtitles)} 種語言):")
    print("=" * 60)
    for lang, info in subtitles.items():
        sub_type = "手動" if info.get('type') == 'manual' else "自動"
        print(f"  {lang:5s} - {info.get('name', lang):20s} ({sub_type})")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python get_youtube_subtitles.py <YouTube_URL> [語言代碼] [格式]")
        print("\n示例:")
        print("  python get_youtube_subtitles.py https://www.youtube.com/watch?v=VIDEO_ID")
        print("  python get_youtube_subtitles.py https://www.youtube.com/watch?v=VIDEO_ID en")
        print("  python get_youtube_subtitles.py https://www.youtube.com/watch?v=VIDEO_ID en srt")
        print("  python get_youtube_subtitles.py https://www.youtube.com/watch?v=VIDEO_ID zh,en")
        print("\n支持的格式: srt, vtt, ttml, json3")
        sys.exit(1)
    
    url = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else None
    subtitle_format = sys.argv[3] if len(sys.argv) > 3 else 'srt'
    
    # 如果提供了語言，可能是多個語言（用逗號分隔）
    if language:
        languages = [lang.strip() for lang in language.split(',')]
    else:
        languages = None
    
    print("=" * 60)
    print("YouTube 字幕獲取器")
    print("=" * 60)
    
    # 先列出可用字幕
    list_available_subtitles(url)
    
    # 下載字幕
    if languages:
        result = get_youtube_subtitles(
            url,
            languages=languages,
            subtitle_format=subtitle_format
        )
    else:
        # 如果沒有指定語言，下載所有可用字幕
        available = get_available_subtitles(url)
        if available:
            result = get_youtube_subtitles(
                url,
                languages=list(available.keys()),
                subtitle_format=subtitle_format
            )
        else:
            print("\n❌ 沒有可用的字幕")
            sys.exit(1)
    
    if result['success']:
        print(f"\n✓ 成功！字幕文件已保存")
        print(f"視頻: {result['video_title']}")
        print(f"文件數量: {len(result['files'])}")
    else:
        print(f"\n❌ 失敗: {result.get('error', '未知錯誤')}")

