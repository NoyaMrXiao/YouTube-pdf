"""
应用配置管理
"""
import os
from pathlib import Path
from typing import Optional
from functools import lru_cache


def _env_bool(name: str, default: bool = False) -> bool:
    """将环境变量解析为布尔值"""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    """应用配置类"""
    
    # 项目根目录
    BASE_DIR = Path(__file__).parent.parent
    
    # 目录配置
    DOWNLOADS_DIR = BASE_DIR / "downloads"
    OUTPUTS_DIR = BASE_DIR / "outputs"
    
    # API密钥配置
    API_KEY_302_AI: Optional[str] = os.getenv("API_KEY_302_AI")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")
    
    # 默认模型配置
    DEFAULT_WHISPER_MODEL = "base"
    DEFAULT_LANGUAGE = "en"
    
    # 转录配置
    DEFAULT_CHUNK_DURATION = 60.0
    DEFAULT_MAX_WORKERS = 4
    
    # 总结配置
    DEFAULT_CHUNK_SIZE = 100000
    DEFAULT_CHUNK_OVERLAP = 300
    DEFAULT_SUMMARY_WORKERS = 5
    
    # 翻译配置
    DEFAULT_TRANSLATE_BATCH_SIZE = 15
    DEFAULT_TRANSLATE_WORKERS = 5
    
    # Web应用配置（支持环境变量覆盖）
    WEB_HOST = os.getenv("WEB_HOST", "127.0.0.1")
    WEB_PORT = int(os.getenv("WEB_PORT", "5000"))
    WEB_DEBUG = _env_bool("WEB_DEBUG", default=True) or _env_bool("DEBUG", False)
    
    @classmethod
    def get_api_key(cls) -> Optional[str]:
        """获取API密钥（优先使用API_KEY_302_AI）"""
        return cls.API_KEY_302_AI or cls.OPENAI_API_KEY
    
    @classmethod
    def ensure_directories(cls):
        """确保必要的目录存在"""
        cls.DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例）"""
    settings = Settings()
    settings.ensure_directories()
    return settings
