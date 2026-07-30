# 宏观仪表盘 Vercel 迁移方案

**创建日期**：2026-07-06
**目标**：把 Render 后端迁移到 Vercel Serverless（避免绑卡）
**状态**：✅ 已完成（实际部署采用 `builds` + `routes` 字段，与本方案初版略有差异）

---

## 一、为什么迁

- Render 免费层要求绑卡（用户无法用）
- Vercel Serverless 免费、无绑卡
- 现有 vercel.json 已部署前端，只需加后端路由

---

## 二、初始迁移方案（设计初案）

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

### 2.2 vercel.json 设计初版（**未采用** —— 见 §三）

本方案初版计划用 monorepo + rewrites 写法：

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

**实际未采用** —— 见 §三「实际方案」。

### 2.3 环境变量（Vercel Dashboard 配置）

| 变量名 | 值 |
|--------|-----|
| `FRED_API_KEY` | 用户自己的 FRED key |
| `GITHUB_OWNER` | lj22503 |
| `GITHUB_REPO` | macroview |

---

## 三、实际方案（迭代 5 次后落地）

`55e36d9 → 2a95773 → 58dc56f → 7d67d5b → 12e8db1` 5 个 commit 逐步调整 Vercel Python 部署检测。

### 3.1 最终 vercel.json

```json
{
  "builds": [
    { "src": "frontend/package.json", "use": "@vercel/static-build" },
    { "src": "src/index.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "src/index.py" },
    { "src": "/(.*)", "dest": "frontend/$1" }
  ]
}
```

### 3.2 关键调整点

| 项 | 初版方案 | 实际方案 |
|----|---------|---------|
| Python 入口位置 | `api/index.py` | `src/index.py`（Vercel 标准路径） |
| 字段风格 | `rewrites`（Vercel v2 风格） | `builds` + `routes`（Vercel v1 字段，更稳） |
| 框架声明 | `framework: vite` | 省略（避免对 Python build 干扰） |
| 后端路由 | `/api/(.*)` | `/api/(.*)` 保持不变 |
| 双 build 声明 | 单 build | 显式 dual builds（前端 + Python） |

### 3.3 迁移 commit 链

```
4d947d8 feat: API层迁移Vercel + 数据采集脚本增强(金/汇率/PMI备援) + 数据更新
55e36d9 fix(vercel): declare Python runtime for api/index.py + framework null
2a95773 fix(vercel): use builds field to explicitly declare Python function
58dc56f fix(vercel): move Python entry to src/index.py (Vercel standard)
7d67d5b fix(vercel): explicit dual builds (static + Python) with routes
12e8db1 test(vercel): minimal FastAPI app to verify Vercel Python detection
```

---

## 四、文件改动清单（最终落地版）

| 文件 | 操作 |
|------|------|
| `src/index.py` | 新增（Vercel Python 入口，最终路径） |
| `src/requirements.txt` | 新增（Vercel Python 依赖） |
| `vercel.json` | 改：用 `builds` + `routes` 声明 dual builds |
| `backend/render.yaml` | 不再使用（保留作历史） |
| `api/index.py` | 早版存在，后移至 `src/index.py`，旧文件废弃 |

---

## 五、验收标准

1. `https://<域名>/api/v1/health` 返回 200
2. 前端 Dashboard 7 大模块图表正常渲染
3. `https://<域名>/api/v1/dashboard` 返回完整 JSON
4. Vercel 部署日志无错误
5. GitHub Actions 触发数据更新后，前端可看到新数据

---

## 六、风险（已验证无需专项处理）

| 风险 | 缓解 | 实际结论 |
|------|------|---------|
| Vercel Serverless 10s 超时 | FRED/akshare 单次请求 < 5s，无问题 | 实际未触发 |
| 冷启动慢（首次请求） | 免费层可接受 | 可接受 |
| 数据缓存丢失（无状态） | 数据从 GitHub Raw 读，不依赖缓存 | GitHub Raw 正常 |

---

## 七、推进顺序（实际执行链）

1. 写 `src/index.py` + `src/requirements.txt`
2. 迭代 5 次调整 vercel.json（`builds` + `routes` 落地）
3. 在 Vercel Dashboard 配环境变量 + 导入 GitHub 仓库
4. 部署 + 验证 API
5. 验证前端数据流

---

**最后更新**：2026-07-30（neat-freak 第二轮补全：与实际 vercel.json 对齐）