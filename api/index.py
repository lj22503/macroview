"""
Vercel Serverless Function 入口
适配 FastAPI app 到 AWS Lambda / Vercel Serverless
"""
import sys
import os

# 把 backend 目录加入 PYTHONPATH，让 main.py / signal_engine.py 可被 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from mangum import Mangum
from main import app

# lifespan="off" 避免 Vercel Serverless 环境下的 startup/shutdown 事件问题
handler = Mangum(app, lifespan="off")