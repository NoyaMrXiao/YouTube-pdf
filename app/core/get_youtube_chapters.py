"""
獲取YouTube視頻章節信息
使用yt-dlp庫獲取視頻的章節時間戳和標題
"""
import yt_dlp
from typing import List, Dict, Optional, Any


def get_youtube_chapters(url: str) -> Dict[str, Any]:
    """
    獲取YouTube視頻的章節信息
    
    參數:
        url (str): YouTube視頻URL
    
    返回:
        dict: 包含章節信息的字典
            {
                'success': bool,
                'chapters': List[Dict],  # 章節列表，每個包含 start_time, title, end_time
                'video_title': str,
                'video_id': str,
                'duration': float,  # 視頻總時長（秒）
                'chapter_count': int
            }
    """
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            
            video_title = info.get('title', 'Unknown')
            video_id = info.get('id', 'Unknown')
            duration = info.get('duration', 0)
            
            # 獲取章節信息
            chapters = info.get('chapters', [])
            
            # 處理章節數據
            processed_chapters = []
            for idx, chapter in enumerate(chapters):
                start_time = chapter.get('start_time', 0)
                title = chapter.get('title', f'Chapter {idx + 1}')
                end_time = chapter.get('end_time')
                
                # 如果沒有結束時間，使用下一個章節的開始時間，或視頻總時長
                if end_time is None:
                    if idx + 1 < len(chapters):
                        end_time = chapters[idx + 1].get('start_time', duration)
                    else:
                        end_time = duration
                
                processed_chapters.append({
                    'index': idx + 1,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time,
                    'title': title
                })
            
            result = {
                'success': len(processed_chapters) > 0,
                'chapters': processed_chapters,
                'video_title': video_title,
                'video_id': video_id,
                'duration': duration,
                'chapter_count': len(processed_chapters)
            }
            
            return result
            
    except yt_dlp.utils.DownloadError as e:
        error_msg = f"獲取章節失敗: {e}"
        return {
            'success': False,
            'error': error_msg,
            'chapters': [],
            'video_title': '',
            'video_id': '',
            'duration': 0,
            'chapter_count': 0
        }
    except Exception as e:
        error_msg = f"發生錯誤: {e}"
        return {
            'success': False,
            'error': error_msg,
            'chapters': [],
            'video_title': '',
            'video_id': '',
            'duration': 0,
            'chapter_count': 0
        }


def format_timestamp(seconds: float) -> str:
    """
    將秒數格式化為時間戳字符串 (HH:MM:SS)
    
    參數:
        seconds (float): 秒數
    
    返回:
        str: 格式化的時間戳，例如 "01:23:45"
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def format_timestamp_ms(seconds: float) -> str:
    """
    將秒數格式化為時間戳字符串 (HH:MM:SS.mmm)
    
    參數:
        seconds (float): 秒數
    
    返回:
        str: 格式化的時間戳，例如 "01:23:45.123"
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    else:
        return f"{minutes:02d}:{secs:02d}.{millis:03d}"


def print_chapters(chapters_result: Dict[str, Any], show_timestamps: bool = True) -> None:
    """
    打印章節信息
    
    參數:
        chapters_result (dict): get_youtube_chapters返回的結果
        show_timestamps (bool): 是否顯示時間戳
    """
    if not chapters_result['success']:
        print("❌ 該視頻沒有章節信息")
        if 'error' in chapters_result:
            print(f"錯誤: {chapters_result['error']}")
        return
    
    print(f"\n視頻: {chapters_result['video_title']}")
    print(f"視頻ID: {chapters_result['video_id']}")
    print(f"總時長: {format_timestamp(chapters_result['duration'])}")
    print(f"章節數量: {chapters_result['chapter_count']}")
    print("=" * 80)
    
    for chapter in chapters_result['chapters']:
        if show_timestamps:
            start_str = format_timestamp(chapter['start_time'])
            end_str = format_timestamp(chapter['end_time'])
            duration_str = format_timestamp(chapter['duration'])
            print(f"{chapter['index']:2d}. [{start_str} - {end_str}] ({duration_str}) {chapter['title']}")
        else:
            print(f"{chapter['index']:2d}. {chapter['title']}")
    
    print("=" * 80)


def get_chapters_as_dict(url: str) -> List[Dict[str, Any]]:
    """
    獲取章節信息並返回為字典列表（簡化版本）
    
    參數:
        url (str): YouTube視頻URL
    
    返回:
        List[Dict]: 章節列表，每個包含 start_time, end_time, title, duration
    """
    result = get_youtube_chapters(url)
    return result.get('chapters', [])


def get_chapters_with_timestamps(url: str) -> List[Dict[str, str]]:
    """
    獲取章節信息，包含格式化的時間戳字符串
    
    參數:
        url (str): YouTube視頻URL
    
    返回:
        List[Dict]: 章節列表，每個包含：
            - index: 章節序號
            - start_time: 開始時間（秒）
            - end_time: 結束時間（秒）
            - start_timestamp: 格式化的開始時間戳 (HH:MM:SS)
            - end_timestamp: 格式化的結束時間戳 (HH:MM:SS)
            - duration: 持續時間（秒）
            - duration_str: 格式化的持續時間 (MM:SS)
            - title: 章節標題
    """
    result = get_youtube_chapters(url)
    
    if not result['success']:
        return []
    
    chapters_with_timestamps = []
    for chapter in result['chapters']:
        chapters_with_timestamps.append({
            'index': chapter['index'],
            'start_time': chapter['start_time'],
            'end_time': chapter['end_time'],
            'start_timestamp': format_timestamp(chapter['start_time']),
            'end_timestamp': format_timestamp(chapter['end_time']),
            'duration': chapter['duration'],
            'duration_str': format_timestamp(chapter['duration']),
            'title': chapter['title']
        })
    
    return chapters_with_timestamps


def save_chapters_to_file(
    url: str,
    output_file: Optional[str] = None,
    format: str = 'txt'
) -> Optional[str]:
    """
    將章節信息保存到文件
    
    參數:
        url (str): YouTube視頻URL
        output_file (str, optional): 輸出文件路徑，如果為None則自動生成
        format (str): 輸出格式，可選: 'txt', 'json', 'csv'
    
    返回:
        str: 保存的文件路徑，如果失敗則返回None
    """
    result = get_youtube_chapters(url)
    
    if not result['success']:
        print("❌ 該視頻沒有章節信息")
        return None
    
    import os
    from pathlib import Path
    
    # 如果沒有指定輸出文件，自動生成
    if output_file is None:
        video_title = result['video_title'].replace(' ', '_')[:50]
        video_id = result['video_id']
        output_file = f"{video_title}_{video_id}_chapters.{format}"
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if format == 'txt':
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"視頻: {result['video_title']}\n")
                f.write(f"視頻ID: {result['video_id']}\n")
                f.write(f"總時長: {format_timestamp(result['duration'])}\n")
                f.write(f"章節數量: {result['chapter_count']}\n")
                f.write("=" * 80 + "\n\n")
                
                for chapter in result['chapters']:
                    start_str = format_timestamp(chapter['start_time'])
                    end_str = format_timestamp(chapter['end_time'])
                    duration_str = format_timestamp(chapter['duration'])
                    f.write(f"{chapter['index']:2d}. [{start_str} - {end_str}] ({duration_str}) {chapter['title']}\n")
        
        elif format == 'json':
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        
        elif format == 'csv':
            import csv
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['序號', '開始時間(秒)', '結束時間(秒)', '持續時間(秒)', '開始時間戳', '結束時間戳', '標題'])
                for chapter in result['chapters']:
                    writer.writerow([
                        chapter['index'],
                        chapter['start_time'],
                        chapter['end_time'],
                        chapter['duration'],
                        format_timestamp(chapter['start_time']),
                        format_timestamp(chapter['end_time']),
                        chapter['title']
                    ])
        
        else:
            print(f"❌ 不支持的格式: {format}")
            return None
        
        print(f"✓ 章節信息已保存到: {output_path}")
        return str(output_path)
        
    except Exception as e:
        print(f"❌ 保存文件失敗: {e}")
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python get_youtube_chapters.py <YouTube_URL> [輸出文件] [格式]")
        print("\n示例:")
        print("  python get_youtube_chapters.py https://www.youtube.com/watch?v=VIDEO_ID")
        print("  python get_youtube_chapters.py https://www.youtube.com/watch?v=VIDEO_ID chapters.txt")
        print("  python get_youtube_chapters.py https://www.youtube.com/watch?v=VIDEO_ID chapters.json json")
        print("  python get_youtube_chapters.py https://www.youtube.com/watch?v=VIDEO_ID chapters.csv csv")
        print("\n支持的格式: txt, json, csv")
        sys.exit(1)
    
    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    format_type = sys.argv[3] if len(sys.argv) > 3 else 'txt'
    
    print("=" * 80)
    print("YouTube 視頻章節獲取器")
    print("=" * 80)
    
    # 獲取章節信息
    result = get_youtube_chapters(url)
    
    # 打印章節信息
    print_chapters(result)
    
    # 如果指定了輸出文件，保存到文件
    if output_file or format_type != 'txt':
        save_chapters_to_file(url, output_file, format_type)

