"""
YouTube服务层
"""
from typing import Optional, Dict, Any
from app.core.download_youtube_audio import download_youtube_audio
from app.core.get_youtube_chapters import get_youtube_chapters, get_chapters_with_timestamps
from app.core.get_youtube_subtitles import get_available_subtitles, get_youtube_subtitles
from app.core.transcribe_audio import transcribe_audio
from app.core.youtube_to_text import youtube_to_text
from config import get_settings


class YouTubeService:
    """YouTube服务类"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def download_audio(self, url: str, output_dir: Optional[str] = None, 
                      progress_hook: Optional[callable] = None) -> Optional[str]:
        """下载YouTube音频"""
        if output_dir is None:
            output_dir = str(self.settings.DOWNLOADS_DIR)
        return download_youtube_audio(url, output_dir=output_dir, progress_hook=progress_hook)
    
    def get_chapters(self, url: str) -> Dict[str, Any]:
        """获取视频章节"""
        return get_youtube_chapters(url)
    
    def get_chapters_with_timestamps(self, url: str) -> list:
        """获取带时间戳的章节"""
        return get_chapters_with_timestamps(url)
    
    def get_subtitles(self, url: str, languages: list = None, 
                     output_dir: Optional[str] = None) -> Dict[str, Any]:
        """获取字幕"""
        if output_dir is None:
            output_dir = str(self.settings.DOWNLOADS_DIR)
        if languages is None:
            languages = ['en']
        return get_youtube_subtitles(url, languages=languages, output_dir=output_dir)
    
    def transcribe(self, audio_file: str, model_name: str = "base",
                   language: Optional[str] = None, diarize: bool = False,
                   hf_token: Optional[str] = None) -> Dict[str, Any]:
        """转录音频"""
        output_dir = str(self.settings.DOWNLOADS_DIR)
        return transcribe_audio(
            audio_file,
            model_name=model_name,
            language=language,
            diarize=diarize,
            hf_token=hf_token,
            output_dir=output_dir
        )
    
    def to_text(self, url: str, model_name: str = "base",
                language: Optional[str] = None, diarize: bool = False,
                hf_token: Optional[str] = None) -> Dict[str, Any]:
        """完整的YouTube转文本流程"""
        output_dir = str(self.settings.DOWNLOADS_DIR)
        return youtube_to_text(
            url,
            model_name=model_name,
            language=language,
            diarize=diarize,
            hf_token=hf_token,
            output_dir=output_dir
        )

