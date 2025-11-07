"""
获取YouTube视频详细信息
使用yt-dlp库获取视频的标题、时长、缩略图等信息
"""
import yt_dlp
from typing import Dict, Optional, Any


def get_youtube_info(url: str) -> Dict[str, Any]:
    """
    获取YouTube视频的详细信息
    
    参数:
        url (str): YouTube视频URL
    
    返回:
        dict: 包含视频信息的字典
            {
                'success': bool,
                'video_id': str,
                'title': str,
                'duration': float,  # 视频总时长（秒）
                'thumbnail': str,  # 缩略图URL
                'description': str,  # 视频描述
                'uploader': str,  # 上传者
                'view_count': int,  # 观看次数
                'upload_date': str,  # 上传日期
                'error': str  # 错误信息（如果失败）
            }
    """
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            
            video_id = info.get('id', 'Unknown')
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            description = info.get('description', '')
            uploader = info.get('uploader', 'Unknown')
            view_count = info.get('view_count', 0)
            upload_date = info.get('upload_date', '')
            
            # 获取缩略图（优先使用最高质量的）
            thumbnails = info.get('thumbnails', [])
            thumbnail = ''
            if thumbnails:
                # 选择最高质量的缩略图
                thumbnail = thumbnails[-1].get('url', '')
            else:
                # 如果没有缩略图列表，尝试使用默认的缩略图URL格式
                thumbnail = f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
            
            # 格式化上传日期
            if upload_date and len(upload_date) == 8:
                formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
            else:
                formatted_date = upload_date
            
            result = {
                'success': True,
                'video_id': video_id,
                'title': title,
                'duration': duration,
                'thumbnail': thumbnail,
                'description': description[:500] if description else '',  # 限制描述长度
                'uploader': uploader,
                'view_count': view_count,
                'upload_date': formatted_date
            }
            
            return result
            
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        return {
            'success': False,
            'error': f'获取视频信息失败: {error_msg}',
            'video_id': '',
            'title': '',
            'duration': 0,
            'thumbnail': '',
            'description': '',
            'uploader': '',
            'view_count': 0,
            'upload_date': ''
        }
    except Exception as e:
        error_msg = str(e)
        return {
            'success': False,
            'error': f'发生错误: {error_msg}',
            'video_id': '',
            'title': '',
            'duration': 0,
            'thumbnail': '',
            'description': '',
            'uploader': '',
            'view_count': 0,
            'upload_date': ''
        }


def format_duration(seconds: float) -> str:
    """
    将秒数格式化为时长字符串 (HH:MM:SS 或 MM:SS)
    
    参数:
        seconds (float): 秒数
    
    返回:
        str: 格式化的时长字符串
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"

