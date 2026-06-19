# 宏观仪表盘 (Macro Dashboard)

中国视角全球大类资产宏观量化仪表盘，数据全部来自公开源。

## 技术架构

- 前端 (Vercel) ← API (Render FastAPI)
- Render 后端拉取 FRED + yfinance 数据
- 本地 AKShare 脚本拉取中国数据 → push 到 GitHub Raw

## 成本：0元

- FRED API：免费
- AKShare：免费
- yfinance：免费
- Render：免费层级
- Vercel：免费层级