"""
任务管理服务
"""
import time
import queue
from typing import Dict, Any, Optional
from threading import Thread


class TaskService:
    """任务管理服务类"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.progress_queues: Dict[str, queue.Queue] = {}
    
    def create_task(self, task_id: Optional[str] = None) -> str:
        """创建新任务"""
        if task_id is None:
            task_id = f"task_{int(time.time())}"
        
        self.tasks[task_id] = {
            'status': 'processing',
            'step': 'init',
            'progress': 0,
            'message': '正在初始化...',
            'transcript': '',
            'segments': [],
            'summary': '',
            'error': None,
            'summary_file': None,
            'transcript_file': None,
            'transcript_pdf_file': None,
            'has_speakers': False
        }
        
        self.progress_queues[task_id] = queue.Queue()
        return task_id
    
    def update_progress(self, task_id: str, step: str, progress: int, message: str):
        """更新任务进度"""
        if task_id not in self.tasks:
            return
        
        self.tasks[task_id]['step'] = step
        self.tasks[task_id]['progress'] = progress
        self.tasks[task_id]['message'] = message
        
        if task_id in self.progress_queues:
            try:
                self.progress_queues[task_id].put({
                    'step': step,
                    'progress': progress,
                    'message': message,
                    'status': self.tasks[task_id]['status']
                }, timeout=0.1)
            except queue.Full:
                pass
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        return self.tasks.get(task_id)
    
    def complete_task(self, task_id: str):
        """完成任务"""
        if task_id in self.tasks:
            self.tasks[task_id]['status'] = 'completed'
            self.update_progress(task_id, 'completed', 100, '✓ 全部完成！')
            if task_id in self.progress_queues:
                self.progress_queues[task_id].put(None)
    
    def fail_task(self, task_id: str, error: str):
        """任务失败"""
        if task_id in self.tasks:
            self.tasks[task_id]['status'] = 'error'
            self.tasks[task_id]['error'] = error
            self.update_progress(task_id, 'error', 0, f'❌ 错误: {error}')
            if task_id in self.progress_queues:
                self.progress_queues[task_id].put(None)
    
    def get_progress_queue(self, task_id: str) -> Optional[queue.Queue]:
        """获取进度队列"""
        return self.progress_queues.get(task_id)

