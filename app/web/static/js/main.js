// 获取DOM元素
const urlForm = document.getElementById('urlForm');
const fetchBtn = document.getElementById('fetchBtn');
const youtubeUrlInput = document.getElementById('youtube_url');
const inputSection = document.getElementById('inputSection');
const videoInfoSection = document.getElementById('videoInfoSection');
const downloadBtn = document.getElementById('downloadBtn');
const statusDiv = document.getElementById('status');
const progressDiv = document.getElementById('progress');
const progressFill = document.getElementById('progressFill');
const stepsDiv = document.getElementById('steps');
const downloadPathInput = document.getElementById('download_path');
const downloadPathLabel = document.getElementById('downloadPathLabel');
const chooseDownloadPathBtn = document.getElementById('chooseDownloadPath');
const clearDownloadPathBtn = document.getElementById('clearDownloadPath');
const pathModal = document.getElementById('pathModal');
const pathList = document.getElementById('pathList');
const modalCloseButtons = document.querySelectorAll('.modal-close');
const newFolderInput = document.getElementById('newFolderInput');
const applyNewFolderBtn = document.getElementById('applyNewFolder');

// 存储当前视频信息
let currentVideoInfo = null;
let currentVideoUrl = '';

// 下载类型选项
const downloadTypeRadios = document.querySelectorAll('input[name="download_type"]');
const videoFormatOptions = document.getElementById('videoFormatOptions');
const audioFormatOptions = document.getElementById('audioFormatOptions');
const subtitleFormatOptions = document.getElementById('subtitleFormatOptions');

let cachedDownloadPaths = null;

// 处理下载类型切换
downloadTypeRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
        const type = e.target.value;
        // 隐藏所有格式选项
        videoFormatOptions.style.display = 'none';
        audioFormatOptions.style.display = 'none';
        subtitleFormatOptions.style.display = 'none';
        
        // 移除所有选中状态的样式
        document.querySelectorAll('.radio-label').forEach(label => {
            label.classList.remove('selected');
        });
        
        // 添加选中状态的样式
        e.target.closest('.radio-label').classList.add('selected');
        
        // 显示对应的格式选项
        if (type === 'video') {
            videoFormatOptions.style.display = 'block';
        } else if (type === 'audio') {
            audioFormatOptions.style.display = 'block';
        } else if (type === 'subtitle') {
            subtitleFormatOptions.style.display = 'block';
        }
    });
    
    // 初始化选中状态
    if (radio.checked) {
        radio.closest('.radio-label').classList.add('selected');
        const type = radio.value;
        if (type === 'video') {
            videoFormatOptions.style.display = 'block';
        } else if (type === 'audio') {
            audioFormatOptions.style.display = 'block';
        } else if (type === 'subtitle') {
            subtitleFormatOptions.style.display = 'block';
        }
    }
});

function updateDownloadPathLabel() {
    const value = downloadPathInput ? downloadPathInput.value.trim() : '';
    if (!downloadPathLabel) return;
    if (!value) {
        downloadPathLabel.textContent = '默认 (downloads)';
        downloadPathLabel.classList.remove('custom-path');
    } else {
        downloadPathLabel.textContent = value;
        downloadPathLabel.classList.add('custom-path');
    }
}

updateDownloadPathLabel();

function escapeHtml(str) {
    if (typeof str !== 'string') {
        return '';
    }
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

async function fetchDownloadPaths() {
    if (cachedDownloadPaths) {
        return cachedDownloadPaths;
    }
    try {
        const response = await fetch('/download/paths');
        const data = await response.json();
        if (data.success && Array.isArray(data.paths)) {
            cachedDownloadPaths = data.paths;
            return cachedDownloadPaths;
        }
        throw new Error(data.error || '无法获取目录列表');
    } catch (error) {
        showStatus('error', '加载目录列表失败: ' + error.message);
        return [];
    }
}

function openPathModal() {
    if (!pathModal) return;
    pathModal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closePathModal() {
    if (!pathModal) return;
    pathModal.classList.remove('show');
    document.body.style.overflow = '';
}

function renderPathList(paths) {
    if (!pathList) return;
    if (!Array.isArray(paths) || paths.length === 0) {
        pathList.innerHTML = '<div class="path-empty">当前没有子目录，您可以使用下方输入框创建。</div>';
        return;
    }
    const current = downloadPathInput.value.trim();
    const items = paths.map((path) => {
        const label = path === '' ? '默认 (downloads)' : path;
        const isActive = current === path;
        const dataAttr = escapeHtml(path);
        const labelHtml = escapeHtml(label);
        return `<button type="button" class="path-option ${isActive ? 'active' : ''}" data-path="${dataAttr}">
            <span class="path-text">${labelHtml}</span>
        </button>`;
    });
    pathList.innerHTML = items.join('');
}

if (chooseDownloadPathBtn) {
    chooseDownloadPathBtn.addEventListener('click', async () => {
        const paths = await fetchDownloadPaths();
        renderPathList(paths);
        openPathModal();
        if (newFolderInput) {
            newFolderInput.value = '';
        }
    });
}

if (clearDownloadPathBtn) {
    clearDownloadPathBtn.addEventListener('click', () => {
        downloadPathInput.value = '';
        updateDownloadPathLabel();
        showStatus('info', '已恢复默认下载目录');
    });
}

if (modalCloseButtons && modalCloseButtons.length > 0) {
    modalCloseButtons.forEach((btn) => {
        btn.addEventListener('click', closePathModal);
    });
}

if (pathModal) {
    pathModal.addEventListener('click', (event) => {
        if (event.target === pathModal) {
            closePathModal();
        }
    });
}

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && pathModal && pathModal.classList.contains('show')) {
        closePathModal();
    }
});

if (pathList) {
    pathList.addEventListener('click', (event) => {
        const button = event.target.closest('.path-option');
        if (!button) return;
        const selectedPath = button.getAttribute('data-path') || '';
        downloadPathInput.value = selectedPath;
        updateDownloadPathLabel();
        closePathModal();
        showStatus('success', selectedPath ? `已选择目录: ${selectedPath}` : '已恢复默认目录');
    });
}

if (applyNewFolderBtn) {
    applyNewFolderBtn.addEventListener('click', () => {
        if (!newFolderInput) return;
        const value = newFolderInput.value.trim();
        if (!value) {
            showStatus('error', '请输入要创建的子目录名称');
            return;
        }
        if (value.includes('..')) {
            showStatus('error', '路径不能包含 ..');
            return;
        }
        downloadPathInput.value = value;
        updateDownloadPathLabel();
        if (cachedDownloadPaths && !cachedDownloadPaths.includes(value)) {
            cachedDownloadPaths.push(value);
            cachedDownloadPaths.sort();
        }
        closePathModal();
        showStatus('success', `已设置目录: ${value}`);
    });
}

// 处理URL表单提交
urlForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const url = youtubeUrlInput.value.trim();
    if (!url) {
        showStatus('error', '请输入YouTube链接');
        return;
    }
    
    // 验证是否为YouTube链接
    if (!isYouTubeUrl(url)) {
        showStatus('error', '请输入有效的YouTube链接');
        return;
    }
    
    currentVideoUrl = url;
    fetchBtn.disabled = true;
    fetchBtn.textContent = '获取中...';
    showStatus('info', '正在获取视频信息...');
    
    try {
        const response = await fetch(`/video/info?url=${encodeURIComponent(url)}`);
        const data = await response.json();
        
        if (data.success) {
            currentVideoInfo = data;
            displayVideoInfo(data, url);
            videoInfoSection.style.display = 'block';
            showStatus('success', '视频信息获取成功');
        } else {
            showStatus('error', data.error || '获取视频信息失败');
        }
    } catch (error) {
        showStatus('error', '获取视频信息失败: ' + error.message);
    } finally {
        fetchBtn.disabled = false;
        fetchBtn.textContent = '获取视频信息';
    }
});

// 验证YouTube URL
function isYouTubeUrl(url) {
    const patterns = [
        /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
        /^https?:\/\/youtu\.be\/[\w-]+/,
        /^https?:\/\/(www\.)?youtube\.com\/embed\/[\w-]+/
    ];
    return patterns.some(pattern => pattern.test(url));
}

// 提取YouTube视频ID
function extractVideoId(url) {
    const patterns = [
        /[?&]v=([\w-]+)/,
        /youtu\.be\/([\w-]+)/,
        /embed\/([\w-]+)/
    ];
    
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match) {
            return match[1];
        }
    }
    return null;
}

// 显示视频信息
function displayVideoInfo(info, url) {
    const videoId = extractVideoId(url);
    
    // 设置内嵌播放器
    const player = document.getElementById('youtubePlayer');
    if (videoId) {
        player.src = `https://www.youtube.com/embed/${videoId}`;
    }
    
    // 显示视频详情
    document.getElementById('videoTitle').textContent = info.title || '未知标题';
    document.getElementById('videoUploader').textContent = info.uploader || '未知上传者';
    document.getElementById('videoDuration').textContent = info.duration_formatted || '未知时长';
    document.getElementById('videoViews').textContent = `${info.view_count_formatted || 'N/A'} 次观看`;
    document.getElementById('videoDate').textContent = info.upload_date || '未知日期';
    
    const description = document.getElementById('videoDescription');
    if (info.description) {
        description.textContent = info.description;
    } else {
        description.textContent = '暂无描述';
    }
}

// 处理下载按钮
downloadBtn.addEventListener('click', async () => {
    if (!currentVideoUrl || !currentVideoInfo) {
        showStatus('error', '请先获取视频信息');
        return;
    }
    
    const downloadType = document.querySelector('input[name="download_type"]:checked').value;
    const options = {
        url: currentVideoUrl,
        type: downloadType
    };

    const downloadPath = downloadPathInput.value.trim();
    if (downloadPath) {
        options.download_path = downloadPath;
    }
    
    // 根据下载类型获取选项
    if (downloadType === 'video') {
        options.format = document.getElementById('video_format').value;
        options.quality = document.getElementById('video_quality').value;
        options.compress = document.getElementById('compress_video').checked;
    } else if (downloadType === 'audio') {
        options.format = document.getElementById('audio_format').value;
        options.quality = document.getElementById('audio_quality').value;
        options.compress = document.getElementById('compress_audio').checked;
    } else if (downloadType === 'subtitle') {
        options.format = document.getElementById('subtitle_format').value;
        options.language = document.getElementById('subtitle_language').value;
    }
    
    // 开始下载
    downloadBtn.disabled = true;
    downloadBtn.textContent = '下载中...';
    showStatus('info', '正在准备下载...');
    stepsDiv.style.display = 'block';
    progressDiv.style.display = 'block';
    updateProgress(0);
    
    try {
        const response = await fetch('/download/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(options)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 如果有下载链接，直接下载
            if (data.download_url) {
                window.location.href = data.download_url;
                showStatus('success', '下载已开始');
            } else if (data.task_id) {
                // 如果有任务ID，监听进度
                setupSSEConnection(data.task_id);
            } else {
                showStatus('success', '下载任务已创建');
            }
        } else {
            showStatus('error', data.error || '下载失败');
            downloadBtn.disabled = false;
            downloadBtn.textContent = '开始下载';
        }
    } catch (error) {
        showStatus('error', '下载失败: ' + error.message);
        downloadBtn.disabled = false;
        downloadBtn.textContent = '开始下载';
    }
});

// SSE连接处理进度
function setupSSEConnection(taskId) {
    const eventSource = new EventSource(`/stream/${taskId}`);
    
    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            
            // 更新进度条
            if (data.progress !== undefined) {
                updateProgress(data.progress);
            }
            
            // 更新步骤状态
            if (data.step) {
                updateStepStatus(data.step, data.message);
            }
            
            // 更新状态消息
            if (data.message) {
                showStatus('info', data.message);
            }
            
            // 检查是否完成
            if (data.status === 'completed') {
                eventSource.close();
                if (data.download_url) {
                    window.location.href = data.download_url;
                }
                showStatus('success', '下载完成！');
                downloadBtn.disabled = false;
                downloadBtn.textContent = '开始下载';
            } else if (data.status === 'error') {
                eventSource.close();
                showStatus('error', '错误: ' + (data.message || '未知错误'));
                downloadBtn.disabled = false;
                downloadBtn.textContent = '开始下载';
            }
        } catch (error) {
            console.error('解析SSE消息失败:', error);
        }
    };
    
    eventSource.onerror = (error) => {
        console.error('SSE连接错误:', error);
        eventSource.close();
    };
}

function updateStepStatus(step, message) {
    const step1 = document.getElementById('step1');
    step1.innerHTML = `<strong>步骤:</strong> ${message || '处理中...'}`;
    step1.classList.add('active');
}

function updateProgress(percent) {
    progressFill.style.width = percent + '%';
    progressFill.textContent = percent + '%';
}

function showStatus(type, message) {
    statusDiv.className = 'status ' + type;
    statusDiv.textContent = message;
    statusDiv.style.display = 'block';
}
