"""
解析字幕文件（SRT, VTT等）並轉換為轉錄結果格式
"""
import re
from typing import Dict, List, Any, Optional
from pathlib import Path


def parse_srt_file(srt_file: str) -> List[Dict[str, Any]]:
    """
    解析SRT字幕文件
    
    參數:
        srt_file (str): SRT文件路徑
    
    返回:
        List[Dict]: 段落列表，每個段落包含 start, end, text
    """
    segments = []
    
    try:
        with open(srt_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # 嘗試其他編碼
        with open(srt_file, 'r', encoding='gbk') as f:
            content = f.read()
    
    # SRT格式：序號、時間戳、文本、空行
    # 使用更靈活的正則表達式來匹配SRT格式
    pattern = r'(\d+)\s*\n\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*\n(.*?)(?=\n\s*\d+\s*\n|\Z)'
    
    matches = re.finditer(pattern, content, re.DOTALL | re.MULTILINE)
    
    for match in matches:
        index = match.group(1)
        start_time = match.group(2)
        end_time = match.group(3)
        text = match.group(4).strip()
        
        # 移除HTML標籤和格式標記
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\{[^}]+\}', '', text)
        # 將多個換行和空格合併為單個空格
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        if text:
            segments.append({
                'start': srt_time_to_seconds(start_time),
                'end': srt_time_to_seconds(end_time),
                'text': text
            })
    
    return segments


def parse_vtt_file(vtt_file: str) -> List[Dict[str, Any]]:
    """
    解析VTT字幕文件
    
    參數:
        vtt_file (str): VTT文件路徑
    
    返回:
        List[Dict]: 段落列表，每個段落包含 start, end, text
    """
    segments = []
    
    try:
        with open(vtt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(vtt_file, 'r', encoding='gbk') as f:
            lines = f.readlines()
    
    # VTT格式：時間戳 --> 時間戳，然後是文本
    pattern = r'(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})'
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        match = re.match(pattern, line)
        
        if match:
            start_time = match.group(1)
            end_time = match.group(2)
            
            # 收集下一行的文本（直到空行或下一個時間戳）
            text_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(pattern, lines[i].strip()):
                text_lines.append(lines[i].strip())
                i += 1
            
            text = ' '.join(text_lines)
            # 移除HTML標籤和格式標記
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'\{[^}]+\}', '', text)
            text = text.strip()
            
            if text:
                segments.append({
                    'start': vtt_time_to_seconds(start_time),
                    'end': vtt_time_to_seconds(end_time),
                    'text': text
                })
        else:
            i += 1
    
    return segments


def srt_time_to_seconds(time_str: str) -> float:
    """
    將SRT時間格式 (HH:MM:SS,mmm) 轉換為秒數
    
    參數:
        time_str (str): 時間字符串，例如 "00:01:23,456" 或 "00:01:23.456"
    
    返回:
        float: 秒數
    """
    # 處理逗號或點作為小數點分隔符
    time_str = time_str.replace(',', '.')
    parts = time_str.split(':')
    
    if len(parts) != 3:
        return 0.0
    
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    
    return hours * 3600 + minutes * 60 + seconds


def vtt_time_to_seconds(time_str: str) -> float:
    """
    將VTT時間格式 (HH:MM:SS.mmm) 轉換為秒數
    
    參數:
        time_str (str): 時間字符串，例如 "00:01:23.456"
    
    返回:
        float: 秒數
    """
    return srt_time_to_seconds(time_str)


def subtitle_to_transcription_result(
    subtitle_file: str,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    將字幕文件轉換為轉錄結果格式（與transcribe_audio返回格式兼容）
    
    參數:
        subtitle_file (str): 字幕文件路徑
        language (str, optional): 語言代碼
    
    返回:
        dict: 轉錄結果，格式與transcribe_audio返回的格式相同
            {
                'segments': [
                    {
                        'start': float,
                        'end': float,
                        'text': str
                    }
                ],
                'language': str
            }
    """
    file_path = Path(subtitle_file)
    file_ext = file_path.suffix.lower()
    
    segments = []
    
    if file_ext == '.srt':
        segments = parse_srt_file(subtitle_file)
    elif file_ext == '.vtt':
        segments = parse_vtt_file(subtitle_file)
    else:
        # 嘗試作為SRT解析
        try:
            segments = parse_srt_file(subtitle_file)
        except:
            raise ValueError(f"不支持的字幕格式: {file_ext}")
    
    # 檢測語言（如果未提供）
    if not language:
        # 簡單的語言檢測：檢查是否包含中文字符
        all_text = ' '.join([seg['text'] for seg in segments])
        if re.search(r'[\u4e00-\u9fff]', all_text):
            language = 'zh'
        else:
            language = 'en'
    
    return {
        'segments': segments,
        'language': language
    }

