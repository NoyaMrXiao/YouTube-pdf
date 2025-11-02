"""
長文本總結 Agent
支持將長文本分塊，對每個塊進行總結，最後生成整體總結
支持異步並發處理和更大的文本塊
"""
import os
import sys
import logging
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 處理導入路徑
try:
    from .chat_completion import chat_completion_simple
except ImportError:
    # 如果相對導入失敗，嘗試絕對導入
    sys.path.insert(0, str(Path(__file__).parent))
    from chat_completion import chat_completion_simple

# 配置日志
def setup_logger(log_file: Optional[str] = None):
    """
    配置日志记录器
    
    参数:
        log_file (str, optional): 日志文件路径，如果为None则只输出到控制台
    """
    logger = logging.getLogger('summarize_text')
    logger.setLevel(logging.INFO)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件handler（如果指定了日志文件）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def split_text_into_chunks(
    text: str,
    chunk_size: int = 100000,  # GPT-4o 支持 128k tokens，约等于 100k-150k 字符（中文/英文混合）
    chunk_overlap: int = 300  # 相应增大重叠部分以保持上下文连贯性
) -> List[str]:
    """
    將長文本分塊
    
    參數:
        text (str): 要分塊的文本
        chunk_size (int): 每塊的最大字符數，默認為 100000（充分利用 GPT-4o 的 128k tokens 上下文）
        chunk_overlap (int): 塊之間的重疊字符數，默認為 5000
    
    返回:
        List[str]: 文本塊列表
    
    示例:
        >>> text = "很長的文本..."
        >>> chunks = split_text_into_chunks(text, chunk_size=1000)
        >>> print(f"分成 {len(chunks)} 塊")
    """
    if not text:
        return []
    
    text_length = len(text)
    
    # 如果文本長度小於塊大小，直接返回整個文本作為一個塊
    if text_length <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    # 確保每次至少處理一定數量的字符，避免產生過多小塊
    min_chunk_size = max(100, chunk_size // 100)  # 至少100字符或chunk_size的1%
    
    while start < text_length:
        # 計算當前塊的結束位置
        end = min(start + chunk_size, text_length)
        last_end = end  # 記錄原始結束位置
        
        # 如果不是最後一塊，嘗試在句號、換行符等位置切斷
        if end < text_length:
            # 尋找合適的分割點（優先選擇句號、問號、感嘆號、換行符）
            for separator in ['。\n', '。 ', '\n\n', '。', '！', '？', '\n']:
                last_sep = text.rfind(separator, start, end)
                if last_sep != -1:
                    # 確保分割點不會導致塊太小
                    potential_end = last_sep + len(separator)
                    if potential_end - start >= min_chunk_size:
                        end = potential_end
                        break
        
        # 如果剩餘文本不足最小塊大小，直接取到末尾
        if text_length - start < min_chunk_size:
            end = text_length
        
        # 提取當前塊
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # 計算下一個塊的起始位置（考慮重疊）
        # 確保至少向前移動一定距離，避免陷入無限循環
        next_start = max(end - chunk_overlap, start + min(1000, chunk_size // 10))
        prev_start = start  # 記錄前一個start位置
        start = min(next_start, text_length)  # 確保不超過文本長度
        
        # 防止死循環：如果start沒有足夠前進，強制前進到end位置
        if start <= prev_start:
            start = end
            if start >= text_length:
                break
    
    return chunks


def summarize_chunk(
    chunk: str,
    chunk_index: int,
    total_chunks: int,
    api_key: str,
    model: str = "chatgpt-4o-latest",
    language: str = "中文",
    logger: Optional[logging.Logger] = None
) -> str:
    """
    總結單個文本塊
    
    參數:
        chunk (str): 要總結的文本塊
        chunk_index (int): 當前塊的索引（從 1 開始）
        total_chunks (int): 總塊數
        api_key (str): API 密鑰
        model (str): 模型名稱
        language (str): 總結使用的語言，默認為 "中文"
        logger (logging.Logger, optional): 日志记录器
    
    返回:
        str: 該塊的總結
    """
    if logger:
        logger.info(f"開始總結第 {chunk_index}/{total_chunks} 塊（長度: {len(chunk)} 字符）")
    
    system_prompt = f"""你是一個專業的文本總結助手。你的任務是對給定的文本進行深入分析，提取並總結核心觀點和論述。
要求：
1. 重點總結文本中的核心觀點、論證和主張
2. 提供具體的論證過程、案例和數據支持（如果有的話）
3. 使用{language}進行總結
4. 採用分段展示的方式，每個觀點或論述使用獨立段落
5. 保持邏輯清晰，結構完整，避免過於簡化
6. 如果文本涉及特定領域（如技術、科學、商業等），請保持專業性和準確性"""
    
    prompt = f"""請對以下文本（第 {chunk_index}/{total_chunks} 塊）進行深入總結，重點關注觀點和論述：

{chunk}

請按照以下要求提供總結：
1. 提取文本中的核心觀點和主要論述
2. 提供具體的論證過程、案例、數據或例證（如文本中包含）
3. 使用分段展示，每個主要觀點或論述單獨成段
4. 保持內容具體，避免過於抽象或概括
5. 確保邏輯連貫，觀點清晰

請開始總結："""
    
    try:
        summary = chat_completion_simple(
            prompt=prompt,
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            temperature=0.3,  # 較低的溫度以保證總結的一致性和準確性
            max_tokens=8000  # 增大输出 token 限制，充分利用 GPT-4o 的能力
        )
        if logger:
            logger.info(f"成功完成第 {chunk_index}/{total_chunks} 塊的總結（總結長度: {len(summary)} 字符）")
        return summary
    except Exception as e:
        error_msg = f"總結第 {chunk_index} 塊時發生錯誤: {e}"
        if logger:
            logger.error(error_msg, exc_info=True)
        print(f"⚠️ {error_msg}")
        return f"[總結失敗: {str(e)}]"


def summarize_text(
    text: str,
    api_key: Optional[str] = None,
    model: str = "chatgpt-4o-latest",
    chunk_size: int = 100000,  # GPT-4o 支持 128k tokens，约等于 100k-150k 字符
    chunk_overlap: int = 300,  # 相应增大重叠以保持上下文连贯性
    language: str = "中文",
    show_progress: bool = True,
    enable_async: bool = True,
    max_workers: int = 5,  # 并发总结的线程数
    save_chunk_summaries: bool = True,  # 是否保存分块总结
    output_dir: Optional[str] = None  # 输出目录，如果为None则使用默认目录
) -> str:
    """
    總結長文本的主函數
    
    參數:
        text (str): 要總結的長文本
        api_key (str, optional): API 密鑰，如果為 None 則從環境變量讀取
        model (str): 模型名稱，默認為 "chatgpt-4o-latest"
        chunk_size (int): 每塊的最大字符數，默認為 100000（充分利用 GPT-4o 的 128k tokens 上下文）
        chunk_overlap (int): 塊之間的重疊字符數，默認為 5000
        language (str): 總結使用的語言，默認為 "中文"
        show_progress (bool): 是否顯示進度，默認為 True
        enable_async (bool): 是否啟用異步並發總結，默認為 True
        max_workers (int): 並發總結的最大線程數，默認為 5
        save_chunk_summaries (bool): 是否保存分块总结到txt文件，默认为 True
        output_dir (str, optional): 输出目录，如果为None则使用默认的outputs目录
    
    返回:
        str: 最終的文本總結
    
    示例:
        >>> long_text = "很長的文本內容..."
        >>> summary = summarize_text(long_text, api_key="your-api-key")
        >>> print(summary)
    """
    # 設置日志
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "outputs"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成日志文件名（使用时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = output_dir / f"summarize_{timestamp}.log"
    logger = setup_logger(str(log_file))
    
    logger.info("=" * 60)
    logger.info("開始長文本總結任務")
    logger.info("=" * 60)
    logger.info(f"文本長度: {len(text)} 字符")
    logger.info(f"模型: {model}")
    logger.info(f"塊大小: {chunk_size}, 重疊: {chunk_overlap}")
    logger.info(f"語言: {language}")
    logger.info(f"並發處理: {enable_async}, 最大線程數: {max_workers}")
    
    # 獲取 API key
    if api_key is None:
        api_key = os.getenv("API_KEY_302_AI") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            error_msg = "請提供 API 密鑰或設置環境變量 API_KEY_302_AI 或 OPENAI_API_KEY"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    if not text or not text.strip():
        error_msg = "文本不能為空"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # 步驟 1: 將文本分塊
    logger.info("步驟 1: 開始將文本分塊")
    if show_progress:
        print(f"📝 正在將文本分塊（塊大小: {chunk_size}, 重疊: {chunk_overlap}）...")
    
    chunks = split_text_into_chunks(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    if not chunks:
        error_msg = "文本分塊失敗，未生成任何塊"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    total_chunks = len(chunks)
    logger.info(f"文本已分成 {total_chunks} 塊")
    for i, chunk in enumerate(chunks, 1):
        logger.info(f"  塊 {i}: {len(chunk)} 字符")
    
    if show_progress:
        print(f"✓ 文本已分成 {total_chunks} 塊\n")
    
    # 如果只有一塊，直接總結
    if total_chunks == 1:
        logger.info("文本只有一塊，直接進行總結")
        if show_progress:
            print("📊 文本較短，直接進行總結...")
        summary = summarize_chunk(
            chunks[0],
            chunk_index=1,
            total_chunks=1,
            api_key=api_key,
            model=model,
            language=language,
            logger=logger
        )
        # 保存分块总结
        if save_chunk_summaries:
            chunk_summary_file = output_dir / f"chunk_summaries_{timestamp}.txt"
            with open(chunk_summary_file, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("分塊總結（按順序）\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"總塊數: 1\n\n")
                f.write("=" * 60 + "\n")
                f.write("第 1 塊總結:\n")
                f.write("=" * 60 + "\n\n")
                f.write(summary)
            logger.info(f"分塊總結已保存到: {chunk_summary_file}")
            if show_progress:
                print(f"💾 分塊總結已保存到: {chunk_summary_file}")
        return summary
    
    # 步驟 2: 對每個塊進行總結（支持並發）
    logger.info("步驟 2: 開始對各個文本塊進行總結")
    if show_progress:
        if enable_async:
            print(f"📋 開始並發總結各個文本塊（最大 {max_workers} 個線程）...\n")
        else:
            print(f"📋 開始總結各個文本塊...\n")
    
    chunk_summaries = []
    
    if enable_async and total_chunks > 1:
        # 使用線程池並發總結
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_chunk = {}
            
            for i, chunk in enumerate(chunks, start=1):
                future = executor.submit(
                    summarize_chunk,
                    chunk,
                    chunk_index=i,
                    total_chunks=total_chunks,
                    api_key=api_key,
                    model=model,
                    language=language,
                    logger=logger
                )
                future_to_chunk[future] = i
            
            # 收集結果（按順序）
            completed = 0
            results_dict = {}  # 使用字典保存結果，以保持順序
            
            for future in as_completed(future_to_chunk):
                chunk_idx = future_to_chunk[future]
                try:
                    summary = future.result()
                    results_dict[chunk_idx] = summary
                    completed += 1
                    
                    logger.info(f"完成第 {chunk_idx}/{total_chunks} 塊的總結")
                    if show_progress:
                        print(f"  ✓ 完成第 {chunk_idx}/{total_chunks} 塊 ({completed}/{total_chunks})")
                except Exception as e:
                    logger.error(f"總結第 {chunk_idx} 塊時發生錯誤: {e}", exc_info=True)
                    print(f"  ⚠️ 總結第 {chunk_idx} 塊時發生錯誤: {e}")
                    results_dict[chunk_idx] = f"[總結失敗: {str(e)}]"
            
            # 按順序組裝結果
            chunk_summaries = [results_dict[i] for i in range(1, total_chunks + 1) if i in results_dict]
            logger.info(f"所有 {len(chunk_summaries)} 個分塊總結已完成")
    else:
        # 順序處理
        for i, chunk in enumerate(chunks, start=1):
            if show_progress:
                print(f"  處理第 {i}/{total_chunks} 塊...", end=" ", flush=True)
            
            summary = summarize_chunk(
                chunk,
                chunk_index=i,
                total_chunks=total_chunks,
                api_key=api_key,
                model=model,
                language=language,
                logger=logger
            )
            
            chunk_summaries.append(summary)
            logger.info(f"完成第 {i}/{total_chunks} 塊的總結")
            
            if show_progress:
                print("✓")
        
        logger.info(f"所有 {len(chunk_summaries)} 個分塊總結已完成")
    
    # 保存分块总结到txt文件（按顺序）
    if save_chunk_summaries:
        chunk_summary_file = output_dir / f"chunk_summaries_{timestamp}.txt"
        logger.info(f"正在保存分塊總結到文件: {chunk_summary_file}")
        try:
            with open(chunk_summary_file, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("分塊總結（按順序）\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"總塊數: {total_chunks}\n")
                f.write(f"模型: {model}\n")
                f.write(f"語言: {language}\n\n")
                f.write("=" * 60 + "\n\n")
                
                for i, summary in enumerate(chunk_summaries, 1):
                    f.write("=" * 60 + "\n")
                    f.write(f"第 {i} 塊總結:\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(summary)
                    f.write("\n\n")
            
            logger.info(f"分塊總結已成功保存到: {chunk_summary_file}")
            if show_progress:
                print(f"\n💾 分塊總結已保存到: {chunk_summary_file}")
        except Exception as e:
            logger.error(f"保存分塊總結時發生錯誤: {e}", exc_info=True)
            print(f"⚠️ 保存分塊總結時發生錯誤: {e}")
    
    # 步驟 3: 合併所有塊的總結，生成最終總結
    logger.info("步驟 3: 開始生成最終總結")
    if show_progress:
        print(f"\n📑 正在生成最終總結...")
    
    # 合併所有塊的總結
    combined_summaries = "\n\n".join([
        f"第 {i+1} 塊總結：\n{summary}"
        for i, summary in enumerate(chunk_summaries)
    ])
    
    system_prompt = f"""你是一個專業的文本總結助手。你的任務是根據多個文本塊的總結，生成一個完整、連貫、具體的整體總結。
要求：
1. 整合所有塊的總結，形成一個邏輯清晰的整體總結
2. 重點總結文本的核心觀點、論證和主張
3. 提供具體的論證過程、案例、數據或例證
4. 使用分段展示的方式，每個主要觀點或論述使用獨立段落
5. 消除重複信息，但保留重要的觀點細節
6. 保持總結的完整性和連貫性
7. 使用{language}進行總結
8. 確保總結能夠全面、具體地反映原文的核心內容和主要觀點"""
    
    final_prompt = f"""以下是對長文本各個部分的總結：

{combined_summaries}

請根據以上各個部分的總結，生成一個完整、連貫、具體的整體總結。請按照以下要求：
1. 整合所有關鍵信息和觀點，形成邏輯清晰的總結
2. 重點突出核心觀點和主要論述，提供具體的論證過程
3. 如果各部分總結中包含案例、數據或例證，請在最終總結中保留
4. 使用分段展示，每個主要觀點或論述單獨成段，結構清晰
5. 消除重複內容，但保留觀點的具體細節和論證
6. 保持內容具體，避免過於抽象或概括
7. 確保結構完整，語言流暢，觀點清晰

請生成一個分段展示的詳細總結："""
    
    try:
        # 充分利用 GPT-4o 的 128k tokens 上下文，增大 max_tokens 输出限制
        logger.info("調用API生成最終總結")
        final_summary = chat_completion_simple(
            prompt=final_prompt,
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=16000  # 增大以充分利用 GPT-4o 的能力生成更详细的总结
        )
        
        logger.info(f"最終總結生成成功（長度: {len(final_summary)} 字符）")
        logger.info("=" * 60)
        logger.info("長文本總結任務完成")
        logger.info("=" * 60)
        
        if show_progress:
            print("✓ 總結完成！\n")
        
        return final_summary
    except Exception as e:
        error_msg = f"生成最終總結時發生錯誤: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg)


if __name__ == "__main__":
    import sys
    
    # 嘗試加載.env文件
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    print("=" * 60)
    print("長文本總結 Agent")
    print("=" * 60)
    
    # 從環境變量獲取 API key
    api_key = os.getenv("API_KEY_302_AI") or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("\n❌ 錯誤: 請設置環境變量 API_KEY_302_AI 或 OPENAI_API_KEY")
        print("\n使用方法:")
        print("  export API_KEY_302_AI='your-api-key'")
        print("  python summarize_text.py <文本文件路徑>")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("\n使用方法:")
        print("  python summarize_text.py <文本文件路徑> [塊大小] [模型名稱]")
        print("\n示例:")
        print("  python summarize_text.py document.txt")
        print("  python summarize_text.py document.txt 2000 chatgpt-4o-latest")
        sys.exit(1)
    
    file_path = sys.argv[1]
    chunk_size = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    model = sys.argv[3] if len(sys.argv) > 3 else "chatgpt-4o-latest"
    
    try:
        # 讀取文本文件
        print(f"\n📖 讀取文件: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text.strip():
            print("❌ 錯誤: 文件為空")
            sys.exit(1)
        
        print(f"✓ 文件長度: {len(text)} 字符\n")
        
        # 執行總結
        summary = summarize_text(
            text=text,
            api_key=api_key,
            model=model,
            chunk_size=chunk_size,
            show_progress=True
        )
        
        print("=" * 60)
        print("最終總結:")
        print("=" * 60)
        print(summary)
        print("\n" + "=" * 60)
        
        # 可選：保存總結到文件
        output_file = file_path.rsplit('.', 1)[0] + "_summary.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("長文本總結\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"原文文件: {file_path}\n")
            f.write(f"原文長度: {len(text)} 字符\n\n")
            f.write("=" * 60 + "\n")
            f.write("總結:\n")
            f.write("=" * 60 + "\n\n")
            f.write(summary)
        
        print(f"\n💾 總結已保存到: {output_file}")
        
    except FileNotFoundError:
        print(f"\n❌ 錯誤: 找不到文件 '{file_path}'")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

