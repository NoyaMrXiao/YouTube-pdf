"""
YouTube视频转文本并总结 - Web应用
使用蓝图和模块化结构
"""
import os
from flask import Flask
from pathlib import Path

# 加载.env文件
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ 已加载.env文件")
except ImportError:
    print("⚠ python-dotenv未安装，无法自动加载.env文件")

# 导入服务
from app.services.task_service import TaskService
from app.services.youtube_service import YouTubeService
from app.services.podcast_service import PodcastService
from app.utils.pdf_generator import PDFGenerator
from config import get_settings

# 导入路由蓝图
from app.web.routes.main import main_bp
from app.web.routes.chapters import chapters_bp
from app.web.routes.api import api_bp, init_api_routes


def create_app():
    """创建Flask应用（工厂模式）"""
    # 获取当前文件所在目录
    base_dir = Path(__file__).parent
    
    app = Flask(__name__, 
                template_folder=str(base_dir / 'templates'),
                static_folder=str(base_dir / 'static'),
                static_url_path='/static')
    
    # 初始化服务
    task_service = TaskService()
    youtube_service = YouTubeService()
    podcast_service = PodcastService()
    pdf_generator = PDFGenerator()
    settings = get_settings()
    
    # 将服务存储到app配置中（供蓝图使用）
    app.config['task_service'] = task_service
    app.config['youtube_service'] = youtube_service
    app.config['podcast_service'] = podcast_service
    app.config['pdf_generator'] = pdf_generator
    app.config['settings'] = settings
    
    # 初始化API路由（需要task_service）
    init_api_routes(task_service)
    
    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(chapters_bp)
    
    return app


# 为了向后兼容，创建全局app实例
app = create_app()


if __name__ == '__main__':
    import socket
    from config import get_settings
    
    settings = get_settings()
    
    # 尝试找到可用端口
    def find_free_port(start_port=5000, max_attempts=10):
        for port in range(start_port, start_port + max_attempts):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('127.0.0.1', port)) != 0:
                    return port
        return 5001  # 默认备用端口
    
    port = find_free_port(settings.WEB_PORT)
    
    print("=" * 60)
    print("YouTube视频总结工具 - Web服务")
    print("=" * 60)
    print(f"\n访问地址: http://127.0.0.1:{port}")
    print("\n注意事项:")
    print("1. 确保已设置API密钥 (API_KEY_302_AI 或 OPENAI_API_KEY)")
    print("2. 首次使用需要下载转录模型")
    print("3. 处理时间取决于视频长度和选择的模型")
    if settings.WEB_DEBUG:
        print("4. 已开启调试模式，代码改动会自动热加载")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 60)
    
    app.run(
        host=settings.WEB_HOST,
        port=port,
        debug=settings.WEB_DEBUG,
        use_reloader=settings.WEB_DEBUG
    )

