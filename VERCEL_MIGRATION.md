# 宏观仪表盘 Vercel 迁移方案

**创建日期**：2026-07-06
**目标**：把 Render 后端迁移到 Vercel Serverless（避免绑卡）
**范围**：仅后端 + vercel.json，前端代码不动

---

## 一、为什么迁

- Render 免费层要求绑卡（用户无法用）
- Vercel Serverless 免费、无绑卡
- 现有 vercel.json 已部署前端，只需加后端路由

## 二、迁移方案

### 2.1 后端 Mangum 适配

**新增文件**：`api/index.py`（Vercel Serverless 入口）

```python
from mangum import Mangum
from backend.main import app

handler = Mangum(app, lifespan="off")
```

**新增文件**：`api/requirements.txt`（Vercel Python 依赖）

```
fastapi==0.115.0
mangum==0.17.0
uvicorn==0.30.0
requests==2.32.3
yfinance==0.2.40
akshare>=1.12.0
pandas==2.2.2
httpx==0.27.0
python-dotenv==1.0.1
```

### 2.2 vercel.json（monorepo 模式）

```json
{
  "buildCommand": "cd frontend && npm install && node ./node_modules/vite/bin/vite.js build",
  "outputDirectory": "frontend/dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/index" }
  ]
}
```

### 2.3 环境变量（Vercel Dashboard 配置）

| 变量名 | 值 |
|--------|-----|
| `FRED_API_KEY` | 用户自己的 FRED key |
| `GITHUB_OWNER` | lj22503 |
| `GITHUB_REPO` | macroview |

---

## 三、文件改动清单

| 文件 | 操作 |
|------|------|
| `api/index.py` | 新增 |
| `api/requirements.txt` | 新增 |
| `backend/requirements.txt` | 加 `mangum==0.17.0` |
| `vercel.json` | 改：加 rewrites |
| `backend/render.yaml` | 暂留（不再用） |

---

## 四、验收标准

1. `https://<域名>/api/v1/health` 返回 200
2. 前端 Dashboard 7 大模块图表正常渲染
3. `https://<域名>/api/v1/dashboard` 返回完整 JSON
4. Vercel 部署日志无错误
5. GitHub Actions 触发数据更新后，前端可看到新数据

---

## 五、风险

| 风险 | 缓解 |
|------|------|
| Vercel Serverless 10s 超时 | FRED/akshare 单次请求 < 5s，无问题 |
| 冷启动慢（首次请求） | 免费层可接受 |
| 数据缓存丢失（无状态） | 数据从 GitHub Raw 读，不依赖缓存 |

---

## 六、推进顺序

1. 写 api/index.py + api/requirements.txt
2. 改 vercel.json
3. 在 Vercel Dashboard 配环境变量 + 导入 GitHub 仓库
4. 部署 + 验证 API
5. 验证前端数据流

---

**最后更新**：2026-07-06