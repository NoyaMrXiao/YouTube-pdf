"""
视频和播客处理函数
"""
import os
import time
from pathlib import Path
from app.core.download_youtube_audio import download_youtube_audio
from app.core.download_podcast import parse_rss_feed
from app.core.transcribe_audio import transcribe_audio, get_audio_duration, estimate_transcription_time
from app.core.summarize_text import summarize_text
from app.core.translate_text import translate_list_parallel
from app.utils.pdf_generator import PDFGenerator
from config import get_settings


def process_youtube_video(task_service, task_id, url, model_name, language, 
                         enable_diarize=False, enable_translate=False, translate_lang='zh-cn'):
    """处理YouTube视频的主函数"""
    settings = get_settings()
    tasks = task_service.tasks
    
    def update_progress(step, progress, message):
        """更新进度"""
        task_service.update_progress(task_id, step, progress, message)
    
    try:
        # 步骤1: 下载音频
        update_progress('download', 5, '正在获取视频信息...')
        output_dir = settings.DOWNLOADS_DIR
        output_dir.mkdir(exist_ok=True)
        
        # 定义下载进度回调函数
        def download_progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percent = 5 + int((downloaded / total) * 20)
                    download_percent = (downloaded / total) * 100
                    speed = d.get('speed', 0)
                    if speed:
                        speed_mb = speed / 1024 / 1024
                        message = f'正在下载音频: {download_percent:.1f}% ({speed_mb:.1f} MB/s)'
                    else:
                        message = f'正在下载音频: {download_percent:.1f}%'
                    update_progress('download', percent, message)
            elif d['status'] == 'finished':
                update_progress('download', 25, '下载完成，正在转换音频格式...')
        
        audio_file = download_youtube_audio(
            url, 
            output_dir=str(output_dir),
            progress_hook=download_progress_hook
        )
        if not audio_file:
            raise Exception("音频下载失败")
        
        update_progress('download', 30, '✓ 音频下载完成')
        time.sleep(0.5)
        
        # 获取音频时长和预计转录时间
        import torch
        audio_duration = get_audio_duration(audio_file)
        device = "cpu"
        try:
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                device = "cpu"  # WhisperX不支持MPS
        except:
            pass
        
        estimated_time = estimate_transcription_time(audio_duration, model_name, device)
        tasks[task_id]['audio_duration'] = audio_duration
        tasks[task_id]['estimated_transcription_time'] = estimated_time
        
        duration_str = f"{int(audio_duration//60)}分{int(audio_duration%60)}秒"
        est_time_str = f"{int(estimated_time//60)}分{int(estimated_time%60)}秒"
        update_progress('transcribe', 35, f'音频时长: {duration_str}，预计转录时间: {est_time_str}')
        
        # 步骤2: 转录
        def transcription_progress(current, total, message):
            progress = 35 + int((current / total) * 35)
            update_progress('transcribe', progress, message)
        
        hf_token = os.getenv("HF_TOKEN") if enable_diarize else None
        if enable_diarize and not hf_token:
            update_progress('transcribe', 40, '⚠️ 说话人检测需要 HF_TOKEN，跳过说话人检测...')
            enable_diarize = False
        
        if enable_diarize:
            update_progress('transcribe', 70, '正在进行说话人分离...')
        
        result = transcribe_audio(
            audio_file,
            model_name=model_name,
            language=language if language else None,
            output_dir=str(output_dir),
            diarize=enable_diarize,
            hf_token=hf_token,
            enable_chunking=True,
            chunk_duration=60.0,
            max_workers=4,
            progress_callback=transcription_progress
        )
        
        update_progress('transcribe', 65, '✓ 转录完成，正在提取文本...')
        
        # 提取转录文本和段落信息
        transcript_text = ''
        segments_data = []
        total_segments = len(result.get('segments', []))
        has_speakers = False
        
        if total_segments > 0:
            for idx, segment in enumerate(result.get('segments', [])):
                text = segment.get('text', '').strip()
                transcript_text += text + ' '
                
                segment_info = {
                    'text': text,
                    'start': segment.get('start', 0),
                    'end': segment.get('end', 0),
                    'speaker': segment.get('speaker', '')
                }
                segments_data.append(segment_info)
                
                if segment.get('speaker'):
                    has_speakers = True
                
                if idx % 5 == 0 or idx == total_segments - 1:
                    progress = 65 + int((idx / total_segments) * 5)
                    update_progress('transcribe', progress,
                                   f'正在提取文本: {idx + 1}/{total_segments} 段落 ({(idx + 1) / total_segments * 100:.1f}%)')
        else:
            transcript_text = ''
        
        tasks[task_id]['transcript'] = transcript_text.strip()
        tasks[task_id]['segments'] = segments_data
        tasks[task_id]['has_speakers'] = has_speakers
        
        # 保存转录文本文件
        base_name = Path(audio_file).stem
        transcript_txt_file = output_dir / f"{base_name}_transcript.txt"
        with open(transcript_txt_file, 'w', encoding='utf-8') as f:
            if has_speakers:
                for seg in segments_data:
                    speaker = seg.get('speaker', '')
                    text = seg.get('text', '').strip()
                    if speaker:
                        f.write(f"[{speaker}] {text}\n")
                    else:
                        f.write(f"{text}\n")
            else:
                for seg in segments_data:
                    f.write(f"{seg.get('text', '').strip()}\n")
        tasks[task_id]['transcript_file'] = str(transcript_txt_file)
        
        # 生成PDF文件
        transcript_pdf_file = output_dir / f"{base_name}_transcript.pdf"
        
        if enable_translate:
            try:
                update_progress('transcribe', 72, f'正在翻译文本到 {translate_lang}...')
                texts_to_translate = [seg.get('text', '').strip() for seg in segments_data]
                
                translated_texts = translate_list_parallel(
                    texts_to_translate,
                    dest=translate_lang,
                    batch_size=15,
                    max_workers=5
                )
                
                if not translated_texts or len(translated_texts) != len(texts_to_translate):
                    translated_texts = texts_to_translate
                
                update_progress('transcribe', 73, '✓ 翻译完成，正在生成双语PDF...')
                
                PDFGenerator.generate_bilingual_pdf(
                    segments_data,
                    translated_texts,
                    str(transcript_pdf_file),
                    has_speakers=has_speakers,
                    title=f"转录文本（含翻译） - {base_name}"
                )
                
                if transcript_pdf_file.exists():
                    tasks[task_id]['transcript_pdf_file'] = str(transcript_pdf_file.absolute())
                else:
                    tasks[task_id]['transcript_pdf_file'] = None
            except Exception as e:
                print(f"⚠ 翻译或生成双语PDF失败: {e}")
                try:
                    PDFGenerator.generate_transcript_pdf(
                        segments_data, 
                        str(transcript_pdf_file),
                        has_speakers=has_speakers,
                        title=f"转录文本 - {base_name}"
                    )
                    if transcript_pdf_file.exists():
                        tasks[task_id]['transcript_pdf_file'] = str(transcript_pdf_file.absolute())
                except:
                    tasks[task_id]['transcript_pdf_file'] = None
        else:
            try:
                PDFGenerator.generate_transcript_pdf(
                    segments_data, 
                    str(transcript_pdf_file),
                    has_speakers=has_speakers,
                    title=f"转录文本 - {base_name}"
                )
                if transcript_pdf_file.exists():
                    tasks[task_id]['transcript_pdf_file'] = str(transcript_pdf_file.absolute())
            except Exception as e:
                print(f"⚠ 生成PDF失败: {e}")
                tasks[task_id]['transcript_pdf_file'] = None
        
        speaker_msg = f'，检测到 {len(set([s["speaker"] for s in segments_data if s["speaker"]]))} 个说话人' if has_speakers else ''
        update_progress('transcribe', 70, f'✓ 文本提取完成 ({total_segments} 段落{speaker_msg})')
        time.sleep(0.5)
        
        # 步骤3: 总结
        update_progress('summarize', 75, '正在准备总结...')
        
        api_key = settings.get_api_key()
        if not api_key:
            tasks[task_id]['summary'] = "⚠️ 未设置API密钥，无法生成总结。请设置环境变量 API_KEY_302_AI 或 OPENAI_API_KEY"
            update_progress('summarize', 100, '⚠️ 跳过总结（缺少API密钥）')
        else:
            update_progress('summarize', 80, '正在分块文本（充分利用 GPT-4o 的 128k tokens 上下文）...')
            
            summary = summarize_text(
                text=transcript_text,
                api_key=api_key,
                chunk_size=100000,
                chunk_overlap=300,
                enable_async=True,
                max_workers=5,
                show_progress=False
            )
            
            tasks[task_id]['summary'] = summary
            
            summary_file = output_dir / f"{base_name}_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            tasks[task_id]['summary_file'] = str(summary_file)
            
            update_progress('summarize', 100, '✓ 总结完成')
        
        task_service.complete_task(task_id)
        
    except Exception as e:
        task_service.fail_task(task_id, str(e))


def process_podcast_rss(task_service, task_id, rss_url, model_name, language,
                        enable_diarize=False, enable_translate=False, translate_lang='zh-cn'):
    """处理播客RSS的主函数"""
    settings = get_settings()
    tasks = task_service.tasks
    
    def update_progress(step, progress, message):
        """更新进度"""
        task_service.update_progress(task_id, step, progress, message)
    
    try:
        # 步骤1: 解析RSS并下载音频
        update_progress('download', 5, '正在解析RSS feed...')
        output_dir = settings.DOWNLOADS_DIR
        output_dir.mkdir(exist_ok=True)
        
        try:
            episodes = parse_rss_feed(rss_url)
        except Exception as e:
            raise Exception(f"RSS feed解析失败: {str(e)}")
        
        if not episodes:
            raise Exception("RSS feed中未找到播客集数")
        
        update_progress('download', 10, f'✓ 找到 {len(episodes)} 个播客集数，正在下载最新一集...')
        
        selected_episode = episodes[0]
        audio_url = selected_episode.get('audio_url', '')
        
        if not audio_url:
            raise Exception("播客集数中没有找到音频URL")
        
        update_progress('download', 15, f'正在下载: {selected_episode.get("title", "未知标题")[:50]}...')
        
        import requests
        response = requests.get(audio_url, stream=True, timeout=120)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        filename = selected_episode.get('title', 'podcast_episode')
        filename = ''.join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = filename[:100]
        
        ext = '.mp3'
        content_type = response.headers.get('content-type', '').lower()
        if 'mp3' in content_type:
            ext = '.mp3'
        elif 'm4a' in content_type or 'mp4' in content_type:
            ext = '.m4a'
        elif 'ogg' in content_type:
            ext = '.ogg'
        elif 'wav' in content_type:
            ext = '.wav'
        
        output_path = output_dir / f"{filename}{ext}"
        
        counter = 1
        while output_path.exists():
            output_path = output_dir / f"{filename}_{counter}{ext}"
            counter += 1
        
        start_time = time.time()
        downloaded_size = 0
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    if total_size > 0:
                        download_percent = (downloaded_size / total_size) * 100
                        progress = 15 + int((downloaded_size / total_size) * 15)
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 0:
                            speed = downloaded_size / elapsed_time
                            speed_mb = speed / 1024 / 1024
                            message = f'正在下载音频: {download_percent:.1f}% ({speed_mb:.1f} MB/s)'
                        else:
                            message = f'正在下载音频: {download_percent:.1f}%'
                        update_progress('download', progress, message)
        
        audio_file = str(output_path)
        update_progress('download', 30, '✓ 音频下载完成')
        time.sleep(0.5)
        
        # 获取音频时长和预计转录时间
        import torch
        audio_duration = get_audio_duration(audio_file)
        device = "cpu"
        try:
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                device = "cpu"
        except:
            pass
        
        estimated_time = estimate_transcription_time(audio_duration, model_name, device)
        tasks[task_id]['audio_duration'] = audio_duration
        tasks[task_id]['estimated_transcription_time'] = estimated_time
        
        duration_str = f"{int(audio_duration//60)}分{int(audio_duration%60)}秒"
        est_time_str = f"{int(estimated_time//60)}分{int(estimated_time%60)}秒"
        update_progress('transcribe', 35, f'音频时长: {duration_str}，预计转录时间: {est_time_str}')
        
        # 步骤2: 转录（与YouTube处理相同）
        def transcription_progress(current, total, message):
            progress = 35 + int((current / total) * 35)
            update_progress('transcribe', progress, message)
        
        hf_token = os.getenv("HF_TOKEN") if enable_diarize else None
        if enable_diarize and not hf_token:
            update_progress('transcribe', 40, '⚠️ 说话人检测需要 HF_TOKEN，跳过说话人检测...')
            enable_diarize = False
        
        if enable_diarize:
            update_progress('transcribe', 70, '正在进行说话人分离...')
        
        result = transcribe_audio(
            audio_file,
            model_name=model_name,
            language=language if language else None,
            output_dir=str(output_dir),
            diarize=enable_diarize,
            hf_token=hf_token,
            enable_chunking=True,
            chunk_duration=60.0,
            max_workers=4,
            progress_callback=transcription_progress
        )
        
        update_progress('transcribe', 65, '✓ 转录完成，正在提取文本...')
        
        # 提取转录文本（与YouTube处理相同）
        transcript_text = ''
        segments_data = []
        total_segments = len(result.get('segments', []))
        has_speakers = False
        
        if total_segments > 0:
            for idx, segment in enumerate(result.get('segments', [])):
                text = segment.get('text', '').strip()
                transcript_text += text + ' '
                
                segment_info = {
                    'text': text,
                    'start': segment.get('start', 0),
                    'end': segment.get('end', 0),
                    'speaker': segment.get('speaker', '')
                }
                segments_data.append(segment_info)
                
                if segment.get('speaker'):
                    has_speakers = True
                
                if idx % 5 == 0 or idx == total_segments - 1:
                    progress = 65 + int((idx / total_segments) * 5)
                    update_progress('transcribe', progress,
                                   f'正在提取文本: {idx + 1}/{total_segments} 段落 ({(idx + 1) / total_segments * 100:.1f}%)')
        else:
            transcript_text = ''
        
        tasks[task_id]['transcript'] = transcript_text.strip()
        tasks[task_id]['segments'] = segments_data
        tasks[task_id]['has_speakers'] = has_speakers
        
        # 保存转录文本文件
        base_name = Path(audio_file).stem
        transcript_txt_file = output_dir / f"{base_name}_transcript.txt"
        with open(transcript_txt_file, 'w', encoding='utf-8') as f:
            if has_speakers:
                for seg in segments_data:
                    speaker = seg.get('speaker', '')
                    text = seg.get('text', '').strip()
                    if speaker:
                        f.write(f"[{speaker}] {text}\n")
                    else:
                        f.write(f"{text}\n")
            else:
                for seg in segments_data:
                    f.write(f"{seg.get('text', '').strip()}\n")
        tasks[task_id]['transcript_file'] = str(transcript_txt_file)
        
        # 生成PDF文件（与YouTube处理相同）
        transcript_pdf_file = output_dir / f"{base_name}_transcript.pdf"
        
        if enable_translate:
            try:
                update_progress('transcribe', 72, f'正在翻译文本到 {translate_lang}...')
                texts_to_translate = [seg.get('text', '').strip() for seg in segments_data]
                
                translated_texts = translate_list_parallel(
                    texts_to_translate,
                    dest=translate_lang,
                    batch_size=15,
                    max_workers=5
                )
                
                if not translated_texts or len(translated_texts) != len(texts_to_translate):
                    translated_texts = texts_to_translate
                
                update_progress('transcribe', 73, '✓ 翻译完成，正在生成双语PDF...')
                
                PDFGenerator.generate_bilingual_pdf(
                    segments_data,
                    translated_texts,
                    str(transcript_pdf_file),
                    has_speakers=has_speakers,
                    title=f"转录文本（含翻译） - {base_name}"
                )
                
                if transcript_pdf_file.exists():
                    tasks[task_id]['transcript_pdf_file'] = str(transcript_pdf_file.absolute())
                else:
                    tasks[task_id]['transcript_pdf_file'] = None
            except Exception as e:
                print(f"⚠ 翻译或生成双语PDF失败: {e}")
                try:
                    PDFGenerator.generate_transcript_pdf(
                        segments_data, 
                        str(transcript_pdf_file),
                        has_speakers=has_speakers,
                        title=f"转录文本 - {base_name}"
                    )
                    if transcript_pdf_file.exists():
                        tasks[task_id]['transcript_pdf_file'] = str(transcript_pdf_file.absolute())
                except:
                    tasks[task_id]['transcript_pdf_file'] = None
        else:
            try:
                PDFGenerator.generate_transcript_pdf(
                    segments_data, 
                    str(transcript_pdf_file),
                    has_speakers=has_speakers,
                    title=f"转录文本 - {base_name}"
                )
                if transcript_pdf_file.exists():
                    tasks[task_id]['transcript_pdf_file'] = str(transcript_pdf_file.absolute())
            except Exception as e:
                print(f"⚠ 生成PDF失败: {e}")
                tasks[task_id]['transcript_pdf_file'] = None
        
        speaker_msg = f'，检测到 {len(set([s["speaker"] for s in segments_data if s["speaker"]]))} 个说话人' if has_speakers else ''
        update_progress('transcribe', 70, f'✓ 文本提取完成 ({total_segments} 段落{speaker_msg})')
        time.sleep(0.5)
        
        # 步骤3: 总结
        update_progress('summarize', 75, '正在准备总结...')
        
        api_key = settings.get_api_key()
        if not api_key:
            tasks[task_id]['summary'] = "⚠️ 未设置API密钥，无法生成总结。请设置环境变量 API_KEY_302_AI 或 OPENAI_API_KEY"
            update_progress('summarize', 100, '⚠️ 跳过总结（缺少API密钥）')
        else:
            update_progress('summarize', 80, '正在分块文本（充分利用 GPT-4o 的 128k tokens 上下文）...')
            
            summary = summarize_text(
                text=transcript_text,
                api_key=api_key,
                chunk_size=100000,
                chunk_overlap=300,
                enable_async=True,
                max_workers=5,
                show_progress=False
            )
            
            tasks[task_id]['summary'] = summary
            
            summary_file = output_dir / f"{base_name}_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            tasks[task_id]['summary_file'] = str(summary_file)
            
            update_progress('summarize', 100, '✓ 总结完成')
        
        task_service.complete_task(task_id)
        
    except Exception as e:
        task_service.fail_task(task_id, str(e))

