# Python 學習項目

這是一個功能豐富的Python學習項目，整合了YouTube音頻下載、語音轉文本、文本總結、翻譯、播客下載等多種功能，並提供Web界面進行一站式操作。

## 📁 項目結構

```
.
├── src/                           # 主要功能源代碼
│   ├── download_youtube_audio.py  # YouTube音頻下載功能
│   ├── get_youtube_subtitles.py  # YouTube字幕獲取功能
│   ├── get_youtube_chapters.py   # YouTube章節獲取功能
│   ├── parse_subtitle.py          # 字幕文件解析功能
│   ├── download_podcast.py        # 播客RSS下載功能
│   ├── transcribe_audio.py        # WhisperX語音轉文本
│   ├── youtube_to_text.py         # YouTube完整流程（優先字幕，回退轉錄）
│   ├── summarize_text.py          # 文本總結功能
│   ├── translate_text.py          # 文本翻譯功能
│   └── chat_completion.py         # AI聊天完成功能
│
├── scripts/                       # 工具腳本
│   ├── generate_flowchart.py     # 生成流程圖
│   ├── generate_pdf.py           # 生成PDF文檔
│   ├── convert_to_traditional.py # 簡體轉繁體工具
│   └── convert_scripts_to_traditional.py
│
├── docs/                          # 文檔目錄
│   ├── 需求文档.md                # 需求文檔（Markdown）
│   ├── 需求文檔與流程圖.pdf       # 完整PDF文檔
│   ├── user_flow.mmd              # Mermaid流程圖源文件
│   ├── YOUTUBE_DOWNLOAD_README.md # YouTube下載功能說明
│   ├── WHISPERX_README.md         # WhisperX轉錄功能說明
│   └── README_OLD.md              # 舊版README
│
├── outputs/                       # 生成的輸出文件
│   ├── user_flowchart.png         # 流程圖PNG
│   └── flowchart_viewer.html      # HTML流程圖查看器
│
├── downloads/                     # 下載的文件（YouTube音頻、播客等）
│
├── main.py                        # 主程序（BBC新聞搜索示例）
├── web_app.py                     # Web應用程序（Flask）
├── pyproject.toml                 # 項目配置和依賴
├── uv.lock                        # 依賴鎖定文件
└── README.md                      # 本文件
```

## 🚀 功能模塊

### 1. YouTube 音頻下載

下載YouTube視頻的音頻軌道並轉換為MP3格式。

**使用方法：**
```python
from src.download_youtube_audio import download_youtube_audio_simple

url = "https://www.youtube.com/watch?v=VIDEO_ID"
audio_file = download_youtube_audio_simple(url)
```

**詳細說明：** 參見 [docs/YOUTUBE_DOWNLOAD_README.md](docs/YOUTUBE_DOWNLOAD_README.md)

### 1.5. YouTube 字幕獲取 🆕

直接獲取YouTube視頻的字幕，支持手動上傳和自動生成的字幕。

**使用方法：**
```python
from src.get_youtube_subtitles import (
    get_youtube_subtitles,
    get_available_subtitles,
    get_subtitle_text,
    list_available_subtitles
)

url = "https://www.youtube.com/watch?v=VIDEO_ID"

# 列出所有可用字幕
list_available_subtitles(url)

# 下載指定語言的字幕
result = get_youtube_subtitles(
    url,
    languages=['en', 'zh'],  # 可以下載多種語言
    subtitle_format='srt'    # 支持 srt, vtt, ttml, json3
)

# 直接獲取字幕文本（不下載文件）
subtitle_text = get_subtitle_text(url, language='en')
```

**功能特點：**
- 支持手動上傳和自動生成的字幕
- 支持多種字幕格式（SRT, VTT, TTML, JSON3）
- 可同時下載多種語言的字幕
- 自動檢測可用字幕語言
- 優先使用手動字幕（更準確）

**命令行使用：**
```bash
# 列出所有可用字幕
python src/get_youtube_subtitles.py <YouTube_URL>

# 下載指定語言的字幕
python src/get_youtube_subtitles.py <YouTube_URL> en

# 下載多種語言
python src/get_youtube_subtitles.py <YouTube_URL> en,zh

# 指定格式
python src/get_youtube_subtitles.py <YouTube_URL> en srt
```

### 1.6. YouTube 章節獲取 🆕

獲取YouTube視頻的章節時間戳和標題信息。

**使用方法：**
```python
from src.get_youtube_chapters import (
    get_youtube_chapters,
    get_chapters_with_timestamps,
    print_chapters,
    save_chapters_to_file
)

url = "https://www.youtube.com/watch?v=VIDEO_ID"

# 獲取章節信息
chapters = get_youtube_chapters(url)

# 打印章節信息
print_chapters(chapters)

# 獲取帶格式化時間戳的章節
chapters_with_ts = get_chapters_with_timestamps(url)

# 保存章節到文件
save_chapters_to_file(url, "chapters.txt", format="txt")  # txt, json, csv
```

**功能特點：**
- 自動獲取視頻章節信息
- 支持多種輸出格式（TXT, JSON, CSV）
- 包含開始時間、結束時間、持續時間
- 格式化時間戳顯示

**命令行使用：**
```bash
# 顯示章節信息
python src/get_youtube_chapters.py <YouTube_URL>

# 保存為文本文件
python src/get_youtube_chapters.py <YouTube_URL> chapters.txt

# 保存為JSON格式
python src/get_youtube_chapters.py <YouTube_URL> chapters.json json

# 保存為CSV格式
python src/get_youtube_chapters.py <YouTube_URL> chapters.csv csv
```

### 2. 播客下載

支持通過RSS feed下載播客音頻文件。

**使用方法：**
```python
from src.download_podcast import download_podcast_simple, parse_rss_feed

# 解析RSS feed
episodes = parse_rss_feed("https://example.com/podcast.rss")

# 下載最新一集
audio_file = download_podcast_simple(episodes[0]['audio_url'])
```

**功能特點：**
- 自動解析RSS feed
- 支持多種音頻格式（MP3, M4A, OGG等）
- 自動清理文件名
- 下載進度顯示

### 3. 語音轉文本 (WhisperX)

使用WhisperX進行高精度語音轉文本，支持詞級時間戳和說話人分離。

**使用方法：**
```python
from src.transcribe_audio import transcribe_audio_simple

audio_file = "path/to/audio.mp3"
result = transcribe_audio_simple(audio_file, model_name="base")
```

**完整流程（YouTube直接轉文本）：**
```python
from src.youtube_to_text import youtube_to_text

url = "https://www.youtube.com/watch?v=VIDEO_ID"
result = youtube_to_text(url, model_name="base")
```

**功能特點：**
- 🆕 **優先使用字幕**：自動檢測並使用YouTube字幕（更快更準確）
- **智能回退**：如果字幕不可用，自動回退到音頻轉錄方法
- 支持多種Whisper模型（tiny, base, small, medium, large）
- 支持說話人分離（需要HF_TOKEN，僅在轉錄模式下）
- 支持分塊轉錄（處理長音頻）
- 自動生成帶時間戳的轉錄文本
- 支持生成PDF格式的轉錄文檔

**字幕優先模式：**
```python
# 優先使用字幕（默認）
result = youtube_to_text(url, prefer_subtitles=True)

# 強制使用音頻轉錄（跳過字幕）
result = youtube_to_text(url, prefer_subtitles=False)
```

**詳細說明：** 參見 [docs/WHISPERX_README.md](docs/WHISPERX_README.md)

### 4. 文本總結

使用AI（GPT-4o）對長文本進行智能總結，支持分塊處理和並發處理。

**使用方法：**
```python
from src.summarize_text import summarize_text

# 需要設置 API_KEY_302_AI 或 OPENAI_API_KEY 環境變量
summary = summarize_text(
    text=long_text,
    api_key=os.getenv("API_KEY_302_AI"),
    chunk_size=100000,  # 充分利用 GPT-4o 的 128k tokens
    enable_async=True,  # 啟用異步並發
    max_workers=5
)
```

**功能特點：**
- 支持超長文本（利用GPT-4o的128k上下文）
- 分塊處理和並發處理
- 自動保存總結到文件
- 支持進度顯示和日誌記錄

### 5. 文本翻譯

使用googletrans進行多語言文本翻譯，支持並發翻譯。

**使用方法：**
```python
from src.translate_text import translate_text, translate_list_parallel

# 單個文本翻譯
result = translate_text("Hello, world!", dest="zh-cn")

# 批量並發翻譯
texts = ["Hello", "World", "Python"]
translated = translate_list_parallel(texts, dest="zh-cn", max_workers=5)
```

**支持的語言：**
- 中文（簡體/繁體）
- 英語、日語、韓語
- 西班牙語、法語、德語
- 以及更多語言

### 6. AI聊天完成

使用OpenAI API進行對話式AI交互。

**使用方法：**
```python
from src.chat_completion import chat_completion_simple

response = chat_completion_simple(
    messages=[
        {"role": "user", "content": "你好！"}
    ],
    api_key=os.getenv("API_KEY_302_AI")
)
```

### 7. Web應用程序 🆕

提供基於Flask的Web界面，整合所有功能於一體。

**啟動方法：**
```bash
uv run python web_app.py
```

然後在瀏覽器中訪問 `http://127.0.0.1:5000`

### 7.1. 桌面應用程序 🆕

使用pywebview將Web應用包裝為桌面應用，無需瀏覽器即可使用。

**啟動方法：**
```bash
uv run python desktop_app.py
```

**桌面應用特點：**
- 🖥️ 原生桌面窗口體驗
- 🚀 自動啟動本地服務器
- 🎨 與Web版本相同的功能
- 📦 無需手動打開瀏覽器
- 🔒 本地運行，數據安全

**系統要求：**
- macOS: 需要安裝WebKit（通常已預裝）
- Windows: 需要安裝Microsoft Edge WebView2 Runtime
- Linux: 需要安裝WebKitGTK

**安裝依賴：**
```bash
uv add pywebview
```

**Web應用功能：**
- 📥 支持YouTube視頻和播客RSS下載
- 🎙️ 實時音頻轉錄（帶進度顯示）
- 📝 自動生成文本總結
- 🌍 支持文本翻譯（生成雙語PDF）
- 👥 支持說話人分離（需HF_TOKEN）
- 📄 自動生成轉錄文本（TXT和PDF格式）
- 📊 實時進度追蹤（Server-Sent Events）
- ⏱️ 預計處理時間顯示

**Web界面特點：**
- 現代化UI設計
- 響應式佈局
- 實時進度更新
- 文件下載功能

### 8. 流程圖生成

根據需求文檔生成用戶流程圖。

**使用方法：**
```bash
uv run python scripts/generate_flowchart.py
```

生成的流程圖會保存在 `outputs/user_flowchart.png`

### 9. PDF 文檔生成

將Markdown需求文檔和流程圖合併生成PDF。

**使用方法：**
```bash
uv run python scripts/generate_pdf.py
```

生成的PDF會保存在 `outputs/需求文檔與流程圖.pdf`

### 10. 文檔轉換工具

將簡體中文文檔轉換為繁體中文。

**使用方法：**
```bash
uv run python scripts/convert_to_traditional.py
```

## 🔐 環境變量配置

項目需要配置以下環境變量（可選，取決於使用的功能）：

### 必需（用於文本總結和AI聊天）

```bash
# 方式1：使用 .env 文件（推薦）
API_KEY_302_AI=your-api-key-here
# 或
OPENAI_API_KEY=your-openai-api-key-here
```

### 可選（用於說話人分離）

```bash
# 用於WhisperX說話人分離功能
HF_TOKEN=your-huggingface-token-here
```

### 環境變量設置方法

**方法1：使用.env文件（推薦）**
```bash
# 在項目根目錄創建 .env 文件
echo "API_KEY_302_AI=your-key" > .env
echo "HF_TOKEN=your-token" >> .env
```

**方法2：在終端中設置**
```bash
# macOS/Linux
export API_KEY_302_AI='your-api-key'
export HF_TOKEN='your-token'

# Windows (PowerShell)
$env:API_KEY_302_AI='your-api-key'
$env:HF_TOKEN='your-token'
```

## 📦 安裝依賴

本項目使用 `uv` 作為包管理器：

```bash
# 安裝所有依賴
uv sync
```

如果沒有安裝 `uv`，可以先安裝：

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv
```

## 🔧 系統要求

### Python版本
- Python >= 3.12

### 外部工具
- **FFmpeg** (用於YouTube音頻下載和轉換)
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt-get install ffmpeg`
  - Windows: 從 [FFmpeg官網](https://ffmpeg.org/download.html) 下載

## 📋 依賴項列表

主要依賴：
- `selenium` - 網頁自動化
- `matplotlib` - 圖表繪製
- `numpy` - 數值計算
- `reportlab` - PDF生成
- `yt-dlp` - YouTube下載
- `whisperx` - 語音轉文本
- `torch` - 深度學習框架（WhisperX需要）
- `zhconv` - 簡繁轉換
- `flask` - Web框架
- `googletrans` - 文本翻譯
- `python-dotenv` - 環境變量管理
- `requests` - HTTP請求

完整列表見 `pyproject.toml`

## 🎯 快速開始

### 1. 安裝依賴

```bash
uv sync
```

### 2. 配置環境變量（可選）

創建 `.env` 文件並設置必要的API密鑰。

### 3. 使用Web應用（推薦）

```bash
uv run python web_app.py
```

在瀏覽器中訪問顯示的地址（通常是 `http://127.0.0.1:5000`）

### 4. 命令行使用

**下載YouTube音頻：**
```bash
uv run python -c "from src.download_youtube_audio import download_youtube_audio_simple; download_youtube_audio_simple('YOUR_URL')"
```

**轉錄音頻為文本：**
```bash
# 轉錄本地音頻
uv run python src/transcribe_audio.py audio.mp3 base

# 或直接從YouTube轉文本
uv run python src/youtube_to_text.py https://www.youtube.com/watch?v=VIDEO_ID base
```

**生成流程圖：**
```bash
uv run python scripts/generate_flowchart.py
```

**生成PDF文檔：**
```bash
uv run python scripts/generate_pdf.py
```

## 📝 使用示例

### 完整工作流程示例

```python
from src.youtube_to_text import youtube_to_text
from src.summarize_text import summarize_text
from src.translate_text import translate_list_parallel
import os

# 1. 從YouTube下載並轉錄
url = "https://www.youtube.com/watch?v=VIDEO_ID"
result = youtube_to_text(url, model_name="base")

# 2. 提取轉錄文本
transcript = " ".join([seg['text'] for seg in result['segments']])

# 3. 生成總結
api_key = os.getenv("API_KEY_302_AI")
summary = summarize_text(transcript, api_key=api_key)

# 4. 翻譯（可選）
segments = result['segments']
texts = [seg['text'] for seg in segments]
translations = translate_list_parallel(texts, dest="zh-cn", max_workers=5)

print(f"轉錄完成：{len(segments)} 個段落")
print(f"總結：{summary[:200]}...")
```

## 📝 文檔說明

- **需求文檔**: `docs/需求文档.md` - 應用需求規格說明
- **流程圖**: `docs/user_flow.mmd` - Mermaid格式流程圖源文件
- **PDF文檔**: `docs/需求文檔與流程圖.pdf` - 完整的PDF文檔
- **YouTube下載說明**: `docs/YOUTUBE_DOWNLOAD_README.md`
- **WhisperX轉錄說明**: `docs/WHISPERX_README.md`

## 🔍 項目特點

- ✅ 模塊化設計，功能清晰分離
- ✅ 完整的文檔和註釋（繁體中文）
- ✅ 支持多種輸出格式（PNG, PDF, HTML, TXT）
- ✅ Web界面整合所有功能
- ✅ 支持並發處理，提高效率
- ✅ 實時進度追蹤
- ✅ 易於擴展和使用
- ✅ 支持說話人分離和雙語輸出

## 🛠️ 故障排除

### 常見問題

1. **FFmpeg未找到**
   ```bash
   # macOS
   brew install ffmpeg
   
   # Linux
   sudo apt-get install ffmpeg
   ```

2. **Whisper模型下載緩慢**
   - 首次使用會自動下載模型
   - 建議使用較小的模型（tiny或base）進行測試

3. **API密鑰錯誤**
   - 確保正確設置 `API_KEY_302_AI` 或 `OPENAI_API_KEY`
   - 檢查.env文件是否在項目根目錄

4. **說話人分離失敗**
   - 需要設置 `HF_TOKEN` 環境變量
   - 需要有效的HuggingFace帳號

## 📄 許可證

本項目僅供學習使用。

## 🤝 貢獻

歡迎提交Issue和Pull Request！

---

**注意：** 
- 請遵守相關平台的使用條款和版權法律，僅下載允許下載的公開內容
- API使用可能產生費用，請注意控制使用量
- 翻譯功能依賴外部服務，可能受到速率限制
