"""
Vercel Serverless Function 入口
- 适配 FastAPI app 到 Vercel Python runtime
- 位置：src/index.py（Vercel 支持的标准入口点）
"""
import sys
import os

# 把 backend 目录加入 PYTHONPATH，让 main.py / signal_engine.py 可被 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app  # Vercel 自动识别 FastAPI app 实例（必须叫 app）