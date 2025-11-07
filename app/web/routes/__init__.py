"""
路由蓝图模块
"""
from .main import main_bp
from .api import api_bp
from .chapters import chapters_bp

__all__ = ['main_bp', 'api_bp', 'chapters_bp']

