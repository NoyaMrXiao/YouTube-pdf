"""
Web应用入口点
"""
from app.web import app

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
    
    port = find_free_port()
    
    print("=" * 60)
    print("YouTube视频总结工具 - Web服务")
    print("=" * 60)
    print(f"\n访问地址: http://127.0.0.1:{port}")
    print("\n注意事项:")
    print("1. 确保已设置API密钥 (API_KEY_302_AI 或 OPENAI_API_KEY)")
    print("2. 首次使用需要下载转录模型")
    print("3. 处理时间取决于视频长度和选择的模型")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 60)
    
    app.run(host=settings.WEB_HOST, port=port, debug=settings.WEB_DEBUG)
