"""
API路由
"""
import threading
from flask import Blueprint, request, jsonify, send_file, Response, stream_with_context
from app.services.task_service import TaskService
from app.web.views.processors import process_youtube_video, process_podcast_rss
from app.core.get_youtube_info import get_youtube_info, format_duration
from app.core.download_youtube import download_youtube_video, download_youtube_audio_custom, download_youtube_subtitle_custom
from config import get_settings
from pathlib import Path
import os

api_bp = Blueprint('api', __name__)


def init_api_routes(task_service: TaskService):
    """初始化API路由（需要task_service实例）"""
    
    @api_bp.route('/video/info', methods=['GET'])
    def get_video_info():
        """获取YouTube视频信息"""
        url = request.args.get('url')
        if not url:
            return jsonify({'error': '请提供YouTube链接'}), 400
        
        try:
            info = get_youtube_info(url)
            if info['success']:
                # 格式化时长
                info['duration_formatted'] = format_duration(info['duration'])
                # 格式化观看次数
                if info['view_count']:
                    if info['view_count'] >= 1000000:
                        info['view_count_formatted'] = f"{info['view_count'] / 1000000:.1f}M"
                    elif info['view_count'] >= 1000:
                        info['view_count_formatted'] = f"{info['view_count'] / 1000:.1f}K"
                    else:
                        info['view_count_formatted'] = str(info['view_count'])
                else:
                    info['view_count_formatted'] = 'N/A'
            return jsonify(info)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @api_bp.route('/process', methods=['POST'])
    def process_video():
        """处理YouTube视频或播客RSS"""
        data = request.json
        url = data.get('url')
        input_type = data.get('input_type', 'youtube')
        model_name = data.get('model_name', 'base')
        language = data.get('language')
        enable_diarize = data.get('enable_diarize', False)
        enable_translate = data.get('enable_translate', False)
        translate_lang = data.get('translate_lang', 'zh-cn')
        
        if not url:
            return jsonify({'error': '请提供链接'}), 400
        
        # 创建任务
        task_id = task_service.create_task()
        
        # 在后台线程中处理
        if input_type == 'rss':
            thread = threading.Thread(
                target=process_podcast_rss,
                args=(task_service, task_id, url, model_name, language, enable_diarize, enable_translate, translate_lang)
            )
        else:
            thread = threading.Thread(
                target=process_youtube_video,
                args=(task_service, task_id, url, model_name, language, enable_diarize, enable_translate, translate_lang)
            )
        thread.daemon = True
        thread.start()
        
        return jsonify({'task_id': task_id})
    
    @api_bp.route('/status/<task_id>')
    def get_status(task_id):
        """获取任务状态"""
        task = task_service.get_task(task_id)
        if task is None:
            return jsonify({'error': '任务不存在'}), 404
        
        return jsonify(task)
    
    @api_bp.route('/stream/<task_id>')
    def stream_progress(task_id):
        """SSE流式推送进度更新"""
        import json
        
        def generate():
            queue_obj = task_service.get_progress_queue(task_id)
            if queue_obj is None:
                yield f"data: {json.dumps({'error': '任务不存在'})}\n\n"
                return
            while True:
                try:
                    # 从队列获取进度更新
                    message = queue_obj.get(timeout=1)
                    if message is None:  # 结束信号
                        break
                    yield f"data: {json.dumps(message)}\n\n"
                except Exception:
                    # 发送心跳保持连接
                    yield f": heartbeat\n\n"
                    continue
        
        return Response(stream_with_context(generate()), mimetype='text/event-stream')
    
    @api_bp.route('/download/<task_id>/summary')
    def download_summary(task_id):
        """下载总结文件"""
        task = task_service.get_task(task_id)
        if task is None:
            return jsonify({'error': '任务不存在'}), 404
        
        summary_file = task.get('summary_file')
        if not summary_file or not __import__('os').path.exists(summary_file):
            return jsonify({'error': '文件不存在'}), 404
        
        return send_file(summary_file, as_attachment=True)
    
    @api_bp.route('/download/<task_id>/transcript')
    def download_transcript(task_id):
        """下载转录文本文件"""
        task = task_service.get_task(task_id)
        if task is None:
            return jsonify({'error': '任务不存在'}), 404
        
        transcript_file = task.get('transcript_file')
        if not transcript_file or not __import__('os').path.exists(transcript_file):
            return jsonify({'error': '文件不存在'}), 404
        
        return send_file(transcript_file, as_attachment=True)
    
    @api_bp.route('/download/<task_id>/transcript_pdf')
    def download_transcript_pdf(task_id):
        """下载转录PDF文件"""
        import os
        task = task_service.get_task(task_id)
        if task is None:
            return jsonify({'error': '任务不存在'}), 404
        
        transcript_pdf_file = task.get('transcript_pdf_file')
        if not transcript_pdf_file:
            return jsonify({'error': 'PDF文件路径未设置'}), 404
        
        # 尝试使用绝对路径或相对路径
        pdf_path = transcript_pdf_file
        if not os.path.isabs(pdf_path):
            pdf_path = os.path.abspath(pdf_path)
        
        if not os.path.exists(pdf_path):
            return jsonify({'error': f'PDF文件不存在: {pdf_path}'}), 404
        
        return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')
    
    @api_bp.route('/download/paths', methods=['GET'])
    def list_download_paths():
        """列出可用的下载目录（位于downloads根目录下）"""
        settings = get_settings()
        base_dir = Path(settings.DOWNLOADS_DIR).resolve()
        base_dir.mkdir(parents=True, exist_ok=True)

        paths = ['']
        max_entries = 500

        try:
            for root, dirs, _ in os.walk(base_dir):
                for directory in dirs:
                    rel_path = Path(root).joinpath(directory).relative_to(base_dir)
                    rel_str = str(rel_path).replace('\\', '/')
                    if rel_str and rel_str not in paths:
                        paths.append(rel_str)
                        if len(paths) >= max_entries:
                            break
                if len(paths) >= max_entries:
                    break
            paths.sort()
            return jsonify({'success': True, 'paths': paths, 'base': str(base_dir)} )
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @api_bp.route('/download/start', methods=['POST'])
    def start_download():
        """开始下载YouTube视频/音频/字幕"""
        data = request.json
        url = data.get('url')
        download_type = data.get('type', 'video')  # video, audio, subtitle
        
        if not url:
            return jsonify({'success': False, 'error': '请提供YouTube链接'}), 400
        
        settings = get_settings()
        base_download_dir = Path(settings.DOWNLOADS_DIR).resolve()
        download_path = (data.get('download_path') or '').strip()

        try:
            if download_path:
                candidate = Path(download_path)
                if not candidate.is_absolute():
                    candidate = (base_download_dir / candidate).resolve()
                else:
                    candidate = candidate.resolve()

                # 确保目标目录在下载根目录内
                if not str(candidate).startswith(str(base_download_dir)):
                    return jsonify({
                        'success': False,
                        'error': '下载路径必须位于服务器的 downloads 目录内'
                    }), 400
                output_dir = candidate
            else:
                output_dir = base_download_dir

            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'无效的下载路径: {e}'
            }), 400
        
        # 创建任务
        task_id = task_service.create_task()
        
        # 在后台线程中处理下载
        def download_task():
            try:
                progress_queue = task_service.get_progress_queue(task_id)
                
                def progress_hook(d):
                    if d['status'] == 'downloading':
                        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                        downloaded = d.get('downloaded_bytes', 0)
                        if total > 0:
                            percent = int((downloaded / total) * 100)
                            speed = d.get('speed', 0)
                            if speed:
                                speed_mb = speed / 1024 / 1024
                                message = f'正在下载: {percent}% ({speed_mb:.1f} MB/s)'
                            else:
                                message = f'正在下载: {percent}%'
                            task_service.update_progress(task_id, 'download', percent, message)
                    elif d['status'] == 'finished':
                        task_service.update_progress(task_id, 'download', 90, '下载完成，正在处理...')
                
                file_path = None
                
                if download_type == 'video':
                    format = data.get('format', 'mp4')
                    quality = data.get('quality', 'best')
                    compress = data.get('compress', False)
                    file_path = download_youtube_video(
                        url, str(output_dir), format, quality, compress, progress_hook
                    )
                elif download_type == 'audio':
                    format = data.get('format', 'mp3')
                    quality = data.get('quality', '192')
                    compress = data.get('compress', False)
                    file_path = download_youtube_audio_custom(
                        url, str(output_dir), format, quality, compress, progress_hook
                    )
                elif download_type == 'subtitle':
                    format = data.get('format', 'srt')
                    language = data.get('language', 'auto')
                    file_path = download_youtube_subtitle_custom(
                        url, str(output_dir), format, language, progress_hook
                    )
                else:
                    raise ValueError('不支持的下载类型')
                
                if file_path and os.path.exists(file_path):
                    # 更新任务状态
                    task = task_service.get_task(task_id)
                    task['status'] = 'completed'
                    task['download_file'] = file_path
                    task['download_url'] = f'/download/file/{task_id}'
                    task_service.update_progress(task_id, 'download', 100, '下载完成！')
                    # 发送完成信号
                    if progress_queue:
                        progress_queue.put({
                            'status': 'completed',
                            'progress': 100,
                            'message': f'下载完成！已保存到: {file_path}',
                            'download_url': f'/download/file/{task_id}'
                        })
                else:
                    raise Exception('下载失败：无法找到下载的文件')
                    
            except Exception as e:
                task_service.update_progress(task_id, 'download', 0, f'错误: {str(e)}')
                progress_queue = task_service.get_progress_queue(task_id)
                if progress_queue:
                    progress_queue.put({
                        'status': 'error',
                        'message': str(e)
                    })
        
        thread = threading.Thread(target=download_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id
        })
    
    @api_bp.route('/download/file/<task_id>')
    def download_file(task_id):
        """下载文件"""
        task = task_service.get_task(task_id)
        if task is None:
            return jsonify({'error': '任务不存在'}), 404
        
        download_file_path = task.get('download_file')
        if not download_file_path or not os.path.exists(download_file_path):
            return jsonify({'error': '文件不存在'}), 404
        
        return send_file(download_file_path, as_attachment=True)

