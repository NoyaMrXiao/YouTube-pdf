"""
下载YouTube视频、音频或字幕
使用yt-dlp库下载，支持格式和质量选项
"""
import yt_dlp
import os
from pathlib import Path
from typing import Optional, Dict, Any, Callable


def download_youtube_video(
    url: str,
    output_dir: Optional[str] = None,
    format: str = 'mp4',
    quality: str = 'best',
    compress: bool = False,
    progress_hook: Optional[Callable] = None
) -> Optional[str]:
    """
    下载YouTube视频
    
    参数:
        url (str): YouTube视频URL
        output_dir (str, optional): 输出目录
        format (str): 视频格式 (mp4, webm, mkv)
        quality (str): 视频质量 (best, 1080p, 720p, 480p, 360p)
        compress (bool): 是否压缩视频
        progress_hook (callable, optional): 进度回调函数
    
    返回:
        str: 下载的视频文件路径，如果失败则返回None
    """
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), 'downloads')
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 构建格式选择器
    if quality == 'best':
        format_selector = f'bestvideo[ext={format}]+bestaudio[ext=m4a]/best[ext={format}]/best'
    else:
        # 根据质量选择格式
        height_map = {
            '1080p': '1080',
            '720p': '720',
            '480p': '480',
            '360p': '360'
        }
        height = height_map.get(quality, '720')
        format_selector = f'bestvideo[height<={height}][ext={format}]+bestaudio[ext=m4a]/best[height<={height}][ext={format}]/best'
    
    ydl_opts = {
        'format': format_selector,
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'progress_hooks': [progress_hook] if progress_hook else [],
    }
    
    # 如果需要压缩，添加后处理选项
    if compress:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': format,
        }]
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'Unknown')
            video_id = info.get('id', 'Unknown')
            
            print(f"正在下载视频: {video_title}")
            print(f"视频ID: {video_id}")
            print(f"格式: {format}, 质量: {quality}")
            
            ydl.download([url])
            
            # 查找下载的文件
            extensions = [format, 'mp4', 'webm', 'mkv']
            for ext in extensions:
                files = list(Path(output_dir).glob(f'*.{ext}'))
                if files:
                    latest_file = max(files, key=os.path.getmtime)
                    print(f"✓ 下载完成: {latest_file}")
                    return str(latest_file)
            
            return None
    except Exception as e:
        print(f"❌ 下载错误: {e}")
        return None


def download_youtube_audio_custom(
    url: str,
    output_dir: Optional[str] = None,
    format: str = 'mp3',
    quality: str = '192',
    compress: bool = False,
    progress_hook: Optional[Callable] = None
) -> Optional[str]:
    """
    下载YouTube音频（自定义格式和质量）
    
    参数:
        url (str): YouTube视频URL
        output_dir (str, optional): 输出目录
        format (str): 音频格式 (mp3, m4a, opus, wav)
        quality (str): 音频质量 (320, 256, 192, 128)
        compress (bool): 是否压缩音频
        progress_hook (callable, optional): 进度回调函数
    
    返回:
        str: 下载的音频文件路径，如果失败则返回None
    """
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), 'downloads')
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format,
            'preferredquality': quality,
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'progress_hooks': [progress_hook] if progress_hook else [],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'Unknown')
            video_id = info.get('id', 'Unknown')
            
            print(f"正在下载音频: {video_title}")
            print(f"视频ID: {video_id}")
            print(f"格式: {format}, 质量: {quality}kbps")
            
            ydl.download([url])
            
            # 查找下载的文件
            extensions = [format, 'mp3', 'm4a', 'opus', 'wav']
            for ext in extensions:
                files = list(Path(output_dir).glob(f'*.{ext}'))
                if files:
                    latest_file = max(files, key=os.path.getmtime)
                    print(f"✓ 下载完成: {latest_file}")
                    return str(latest_file)
            
            return None
    except Exception as e:
        print(f"❌ 下载错误: {e}")
        return None


def download_youtube_subtitle_custom(
    url: str,
    output_dir: Optional[str] = None,
    format: str = 'srt',
    language: str = 'auto',
    progress_hook: Optional[Callable] = None
) -> Optional[str]:
    """
    下载YouTube字幕（自定义格式和语言）
    
    参数:
        url (str): YouTube视频URL
        output_dir (str, optional): 输出目录
        format (str): 字幕格式 (srt, vtt, txt, json)
        language (str): 字幕语言代码，'auto'表示自动检测
        progress_hook (callable, optional): 进度回调函数
    
    返回:
        str: 下载的字幕文件路径，如果失败则返回None
    """
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), 'downloads')
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 获取可用字幕
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})
            available_subs = {}
            # 合并手动字幕和自动字幕
            for lang, subs in subtitles.items():
                if subs:
                    available_subs[lang] = {'name': subs[0].get('name', lang), 'type': 'manual'}
            for lang, subs in automatic_captions.items():
                if lang not in available_subs and subs:
                    available_subs[lang] = {'name': subs[0].get('name', lang), 'type': 'auto'}
    except Exception as e:
        print(f"⚠ 获取字幕列表失败: {e}")
        available_subs = {}
    
    # 确定要下载的语言
    languages_to_download = []
    if language == 'auto':
        # 自动检测：优先选择中文或英语
        if 'zh' in available_subs:
            languages_to_download = ['zh']
        elif 'en' in available_subs:
            languages_to_download = ['en']
        elif available_subs:
            languages_to_download = [list(available_subs.keys())[0]]
    else:
        languages_to_download = [language] if language in available_subs else []
    
    if not languages_to_download:
        print("❌ 没有可用的字幕")
        return None
    
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': languages_to_download,
        'subtitlesformat': format,
        'skip_download': True,
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'progress_hooks': [progress_hook] if progress_hook else [],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'Unknown')
            video_id = info.get('id', 'Unknown')
            
            print(f"正在下载字幕: {video_title}")
            print(f"视频ID: {video_id}")
            print(f"格式: {format}, 语言: {languages_to_download[0]}")
            
            ydl.download([url])
            
            # 查找下载的文件
            extensions = [format, 'srt', 'vtt', 'txt']
            for ext in extensions:
                files = list(Path(output_dir).glob(f'*.{ext}'))
                if files:
                    # 查找包含语言代码的文件
                    for file in files:
                        if any(lang in file.stem.lower() for lang in languages_to_download):
                            print(f"✓ 下载完成: {file}")
                            return str(file)
                    # 如果没有找到，返回最新的文件
                    latest_file = max(files, key=os.path.getmtime)
                    print(f"✓ 下载完成: {latest_file}")
                    return str(latest_file)
            
            return None
    except Exception as e:
        print(f"❌ 下载错误: {e}")
        return None

