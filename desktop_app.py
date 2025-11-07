"""
桌面应用启动器
使用pywebview将Flask Web应用包装为桌面应用
"""
import os
import sys
import threading
import time
import socket
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    import webview
except ImportError:
    print("❌ 错误: 未安装 pywebview")
    print("请运行: uv add pywebview")
    sys.exit(1)

# 导入Flask应用
from app.web import app


def find_free_port(start_port=5000, max_attempts=10):
    """查找可用端口"""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return 5001  # 默认备用端口


def start_flask_server(port):
    """在后台线程中启动Flask服务器"""
    try:
        app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"❌ Flask服务器启动失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    # 查找可用端口
    port = find_free_port()
    url = f'http://127.0.0.1:{port}'
    
    print("=" * 60)
    print("YouTube视频总结工具 - 桌面应用")
    print("=" * 60)
    print(f"\n正在启动服务器: {url}")
    print("\n注意事项:")
    print("1. 确保已设置API密钥 (API_KEY_302_AI 或 OPENAI_API_KEY)")
    print("2. 首次使用需要下载转录模型")
    print("3. 处理时间取决于视频长度和选择的模型")
    print("=" * 60)
    
    # 在后台线程中启动Flask服务器
    server_thread = threading.Thread(
        target=start_flask_server,
        args=(port,),
        daemon=True
    )
    server_thread.start()
    
    # 等待服务器启动
    max_wait = 10
    for i in range(max_wait):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('127.0.0.1', port)) == 0:
                    print(f"✓ 服务器已启动")
                    break
        except:
            pass
        time.sleep(0.5)
    else:
        print("⚠ 警告: 服务器可能未完全启动，但将继续尝试打开窗口")
    
    # 创建窗口
    try:
        # 设置窗口标题和大小
        window = webview.create_window(
            title='🎥 音频视频总结工具',
            url=url,
            width=1200,
            height=800,
            min_size=(800, 600),
            resizable=True,
            fullscreen=False,
            on_top=False,
            shadow=True,
            text_select=True,  # 允许选择文本
            easy_drag=True,   # 允许拖拽
        )
        
        # 启动webview
        print("\n正在打开应用窗口...")
        print("提示: 关闭窗口即可退出应用")
        webview.start(debug=False)
        
    except KeyboardInterrupt:
        print("\n\n应用已关闭")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

