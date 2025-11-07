"""
章节相关路由
"""
import os
import tempfile
from flask import Blueprint, request, jsonify, send_file
from urllib.parse import unquote
from app.core.get_youtube_chapters import get_youtube_chapters, get_chapters_with_timestamps, save_chapters_to_file

chapters_bp = Blueprint('chapters', __name__)


@chapters_bp.route('/chapters')
def get_chapters():
    """获取YouTube视频章节信息"""
    url = request.args.get('url')
    if not url:
        return jsonify({'error': '请提供视频URL', 'success': False}), 400
    
    try:
        result = get_youtube_chapters(url)
        if result['success']:
            # 添加格式化的时间戳
            chapters_with_ts = get_chapters_with_timestamps(url)
            result['chapters'] = chapters_with_ts
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@chapters_bp.route('/download/chapters/<path:url>')
def download_chapters(url):
    """下载章节文件"""
    format_type = request.args.get('format', 'txt')
    
    try:
        # 解码URL
        url = unquote(url)
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        
        # 生成文件名
        result = get_youtube_chapters(url)
        if not result['success']:
            return jsonify({'error': result.get('error', '获取章节失败')}), 404
        
        video_title = result.get('video_title', 'video').replace(' ', '_')[:50]
        video_id = result.get('video_id', 'unknown')
        filename = f"{video_title}_{video_id}_chapters.{format_type}"
        file_path = os.path.join(temp_dir, filename)
        
        # 保存文件
        saved_path = save_chapters_to_file(url, file_path, format_type)
        
        if saved_path and os.path.exists(saved_path):
            return send_file(saved_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({'error': '保存文件失败'}), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

