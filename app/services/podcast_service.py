"""
播客服务层
"""
from typing import Optional, Dict, Any, List
from app.core.download_podcast import (
    download_podcast_from_rss,
    download_podcast_simple,
    parse_rss_feed
)
from app.core.transcribe_audio import transcribe_audio
from config import get_settings


class PodcastService:
    """播客服务类"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def parse_rss(self, rss_url: str) -> List[Dict[str, Any]]:
        """解析RSS feed"""
        return parse_rss_feed(rss_url)
    
    def download_from_rss(self, rss_url: str, episode_index: int = 0,
                          latest: bool = True) -> Optional[str]:
        """从RSS下载播客"""
        output_dir = str(self.settings.DOWNLOADS_DIR)
        return download_podcast_from_rss(
            rss_url,
            output_dir=output_dir,
            episode_index=episode_index,
            latest=latest
        )
    
    def download_simple(self, url: str) -> Optional[str]:
        """简单下载（自动检测URL类型）"""
        output_dir = str(self.settings.DOWNLOADS_DIR)
        return download_podcast_simple(url)
    
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

