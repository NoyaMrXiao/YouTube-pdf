# Web应用模块结构

## 📁 目录结构

```
app/web/
├── app.py              # Flask应用工厂（主入口）
├── routes/             # 路由蓝图
│   ├── __init__.py
│   ├── main.py        # 主页路由
│   ├── api.py         # API路由（处理、状态、下载等）
│   └── chapters.py    # 章节相关路由
├── views/              # 视图处理函数
│   ├── __init__.py
│   └── processors.py  # 视频/播客处理函数
├── templates/          # HTML模板
│   └── index.html     # 主页模板
└── static/             # 静态文件
    ├── css/
    │   └── style.css  # 样式表
    └── js/
        └── main.js    # JavaScript脚本
```

## 🏗️ 架构设计

### 1. 应用工厂模式 (`app.py`)
- 使用 `create_app()` 工厂函数创建Flask应用
- 初始化所有服务（TaskService, YouTubeService等）
- 注册路由蓝图
- 配置模板和静态文件路径

### 2. 路由蓝图 (`routes/`)
- **main.py**: 主页路由 (`/`)
- **api.py**: API路由
  - `/process` - 处理视频/播客
  - `/status/<task_id>` - 获取任务状态
  - `/stream/<task_id>` - SSE流式推送
  - `/download/<task_id>/summary` - 下载总结
  - `/download/<task_id>/transcript` - 下载转录文本
  - `/download/<task_id>/transcript_pdf` - 下载PDF
- **chapters.py**: 章节相关路由
  - `/chapters` - 获取章节信息
  - `/download/chapters/<url>` - 下载章节文件

### 3. 视图处理函数 (`views/`)
- **processors.py**: 后台处理函数
  - `process_youtube_video()` - 处理YouTube视频
  - `process_podcast_rss()` - 处理播客RSS

### 4. 模板和静态文件
- **templates/index.html**: 主页HTML模板
- **static/css/style.css**: 样式表
- **static/js/main.js**: 前端JavaScript逻辑

## 🔄 工作流程

1. **用户请求** → 路由蓝图 (`routes/`)
2. **路由处理** → 调用视图函数或返回模板
3. **后台处理** → 视图函数 (`views/processors.py`) 在后台线程中执行
4. **进度更新** → 通过TaskService推送进度到前端
5. **前端显示** → JavaScript通过SSE接收并更新UI

## 📝 使用示例

### 启动应用
```python
from app.web import create_app

app = create_app()
app.run()
```

### 添加新路由
```python
# routes/new_route.py
from flask import Blueprint

new_bp = Blueprint('new', __name__)

@new_bp.route('/new')
def new_view():
    return "New Route"

# 在app.py中注册
app.register_blueprint(new_bp)
```

## 🎯 优势

1. **模块化**: 路由、视图、模板分离
2. **可扩展**: 易于添加新功能和路由
3. **可维护**: 代码组织清晰，职责分明
4. **可测试**: 各模块可独立测试
5. **符合Flask最佳实践**: 使用蓝图和工厂模式

