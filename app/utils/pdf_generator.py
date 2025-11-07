"""
PDF生成工具
"""
import os
from pathlib import Path
from typing import List, Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors


class PDFGenerator:
    """PDF生成器类"""
    
    @staticmethod
    def register_apple_fonts() -> str:
        """注册Apple系统字体"""
        apple_font_paths = [
            '/System/Library/Fonts/PingFang.ttc',
            '/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/Supplemental/STHeiti Medium.ttc',
            '/System/Library/Fonts/STSong.ttc',
            '/System/Library/Fonts/STKaiti.ttc',
            '/System/Library/Fonts/Helvetica.ttc',
            '/System/Library/Fonts/SFNS.ttf',
        ]
        
        for font_path in apple_font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('AppleChinese', font_path))
                    return 'AppleChinese'
                except Exception:
                    continue
        
        return 'Helvetica'
    
    @classmethod
    def generate_transcript_pdf(cls, segments: List[Dict[str, Any]], 
                               output_path: str, has_speakers: bool = False,
                               title: str = "转录文本") -> None:
        """生成转录文本PDF"""
        doc = SimpleDocTemplate(
            output_path, 
            pagesize=A4,
            leftMargin=1.5*cm, 
            rightMargin=1.5*cm,
            topMargin=1.5*cm, 
            bottomMargin=1.5*cm
        )
        story = []
        
        font_name = cls.register_apple_fonts()
        
        title_style = ParagraphStyle(
            'TitleStyle',
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            spaceBefore=0,
            fontName=font_name,
            leading=22
        )
        
        speaker_style = ParagraphStyle(
            'SpeakerStyle',
            fontSize=10,
            textColor=colors.HexColor('#3498db'),
            spaceAfter=2,
            fontName=font_name,
            leading=12
        )
        
        time_style = ParagraphStyle(
            'TimeStyle',
            fontSize=9,
            textColor=colors.HexColor('#7f8c8d'),
            spaceAfter=2,
            fontName=font_name,
            leading=11
        )
        
        text_style = ParagraphStyle(
            'TextStyle',
            fontSize=11,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            fontName=font_name,
            leading=15
        )
        
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.3*cm))
        
        for segment in segments:
            text = segment.get('text', '').strip()
            if not text:
                continue
            
            start_time = segment.get('start', 0)
            end_time = segment.get('end', 0)
            
            hours = int(start_time // 3600)
            minutes = int((start_time % 3600) // 60)
            secs = int(start_time % 60)
            start_str = f"{hours}:{minutes:02d}:{secs:02d}" if hours > 0 else f"{minutes}:{secs:02d}"
            
            end_hours = int(end_time // 3600)
            end_minutes = int((end_time % 3600) // 60)
            end_secs = int(end_time % 60)
            end_str = f"{end_hours}:{end_minutes:02d}:{end_secs:02d}" if end_hours > 0 else f"{end_minutes}:{end_secs:02d}"
            
            time_str = f"{start_str} - {end_str}"
            story.append(Paragraph(f"<b>{time_str}</b>", time_style))
            
            if has_speakers and segment.get('speaker'):
                speaker = segment.get('speaker', '')
                story.append(Paragraph(f"<b>[{speaker}]</b>", speaker_style))
            
            text_escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(text_escaped, text_style))
            story.append(Spacer(1, 0.15*cm))
        
        doc.build(story)
    
    @classmethod
    def generate_bilingual_pdf(cls, segments: List[Dict[str, Any]], 
                               translations: List[str], output_path: str,
                               has_speakers: bool = False, 
                               title: str = "转录文本（含翻译）") -> None:
        """生成双语PDF"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=1.5*cm,
            rightMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        story = []
        
        font_name = cls.register_apple_fonts()
        
        title_style = ParagraphStyle(
            'TitleStyle',
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            spaceBefore=0,
            fontName=font_name,
            leading=22
        )
        
        speaker_style = ParagraphStyle(
            'SpeakerStyle',
            fontSize=10,
            textColor=colors.HexColor('#3498db'),
            spaceAfter=2,
            fontName=font_name,
            leading=12
        )
        
        time_style = ParagraphStyle(
            'TimeStyle',
            fontSize=9,
            textColor=colors.HexColor('#7f8c8d'),
            spaceAfter=2,
            fontName=font_name,
            leading=11
        )
        
        original_style = ParagraphStyle(
            'OriginalStyle',
            fontSize=11,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=4,
            alignment=TA_JUSTIFY,
            fontName=font_name,
            leading=15
        )
        
        translation_style = ParagraphStyle(
            'TranslationStyle',
            fontSize=11,
            textColor=colors.HexColor('#e74c3c'),
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            fontName=font_name,
            leading=15,
            leftIndent=0.3*cm
        )
        
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.3*cm))
        
        for segment, translation in zip(segments, translations):
            text = segment.get('text', '').strip()
            translated_text = translation.strip() if translation else ''
            
            if not text:
                continue
            
            start_time = segment.get('start', 0)
            end_time = segment.get('end', 0)
            
            hours = int(start_time // 3600)
            minutes = int((start_time % 3600) // 60)
            secs = int(start_time % 60)
            start_str = f"{hours}:{minutes:02d}:{secs:02d}" if hours > 0 else f"{minutes}:{secs:02d}"
            
            end_hours = int(end_time // 3600)
            end_minutes = int((end_time % 3600) // 60)
            end_secs = int(end_time % 60)
            end_str = f"{end_hours}:{end_minutes:02d}:{end_secs:02d}" if end_hours > 0 else f"{end_minutes}:{end_secs:02d}"
            
            time_str = f"{start_str} - {end_str}"
            story.append(Paragraph(f"<b>{time_str}</b>", time_style))
            
            if has_speakers and segment.get('speaker'):
                speaker = segment.get('speaker', '')
                story.append(Paragraph(f"<b>[{speaker}]</b>", speaker_style))
            
            text_escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(f"<b>原文:</b><br/>{text_escaped}", original_style))
            
            if translated_text:
                translation_escaped = translated_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(f"<b>翻译:</b><br/>{translation_escaped}", translation_style))
            
            story.append(Spacer(1, 0.2*cm))
        
        doc.build(story)

