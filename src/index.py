"""
Vercel Python 入口（简化测试版）
- Vercel 应自动识别 src/index.py 并启用 Python runtime
- 测试是否能跑起来
"""
from fastapi import FastAPI

app = FastAPI()


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "runtime": "vercel-python", "version": "1.0.0"}
