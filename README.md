# 宏观仪表盘 (Macro Dashboard)

中国视角全球大类资产宏观量化仪表盘，数据全部来自公开源（FRED + AKShare + yfinance）。

> 完整规格定义在 [SPEC.md](SPEC.md)，部署历史在 [VERCEL_MIGRATION.md](VERCEL_MIGRATION.md)。

---

## 一句话定位

**「数据采集 → 信号计算 → 观点映射 → 自动简报」** —— 全流程零人工干预，给投顾 / 机构投资者做中国视角的全球资产配置决策链。

---

## 技术架构

```
┌──────────────────────────────┐
│ 前端（React + ECharts）       │ ← Vercel 静态部署
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│ 后端 FastAPI（API 路由）      │ ← Vercel Python Serverless（Mangum）
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│ 数据层                       │
│ • FRED   — 美联储宏观/资产    │
│ • AKShare — 中国/港股/商品    │
│ • yfinance — 全球资产补      │
└──────────────────────────────┘
```

本地数据采集脚本每日拉新数据 → 推送到 GitHub Raw → 前端 + 后端读取。

---

## 7 大模块（页面 / API）

| 路径 | API 端点 | 内容 |
|------|---------|------|
| `/` 顶层概览 | `GET /api/v1/overview` | RISK ON/OFF + 置信度 + 仓位建议 + 5 因子打分 |
| `/china` 中国内核 | `GET /api/v1/china-core` | PMI、CPI/PPI、社融、M1-M2、LPR |
| `/global` 全球宏观 | `GET /api/v1/global-macro` | 美国 ISM PMI / 核心 PCE / 美联储资产负债表 |
| `/fx` 美元与流动性 | `GET /api/v1/fx-liquidity` | DXY、中美利差、USD/CNH、USD/JPY |
| `/assets` 全球资产 | `GET /api/v1/assets` | 标普500、沪深300、黄金、原油、10Y 美债 |
| `/risk` 波动率与风险 | `GET /api/v1/risk` | VIX、MOVE、高收益债利差、A 股隐含波动率 |
| `/events` 事件流 | `GET /api/v1/events` | 经济日历、实时快讯 |
| 全景 | `GET /api/v1/dashboard` | 顶层接口，返回所有模块聚合 |

---

## 信号合成规则（5 因子）

每因子打分 -2 到 +2，按权重合成总分（-2.0 ~ +2.0）→ 映射到权益仓位。

| 因子 | 权重 |
|------|-----:|
| 中美利差 | 20% |
| M1-M2 剪刀差 | 25% |
| VIX | 15% |
| 北向资金 | 15% |
| 信用利差 | 25% |

详细阈值规则见 SPEC.md §5。

---

## 部署

| 组件 | 部署方式 |
|------|---------|
| 前端（React） | Vercel 静态 |
| 后端（FastAPI） | Vercel Python Serverless（`api/index.py` → Mangum） |
| 数据采集脚本 | 本地 cron，每日 09:05 后推 GitHub Raw |

详细迁移过程见 [VERCEL_MIGRATION.md](VERCEL_MIGRATION.md)。

---

## 成本

| 项目 | 成本 |
|------|------|
| FRED API | 免费 |
| AKShare | 免费 |
| yfinance | 免费 |
| Vercel | 免费层（无绑卡） |
| **合计** | **0 元** |

---

## 字段命名规范

- **后端存储 / API 传输**：英文 ID（`cn_pmi_official`、`cn_us_10y_spread` …）
- **前端对客展示**：中文简称（"官方制造业PMI"、"中美利差" …）

完整字段定义见 [SPEC.md §6 数据字典](SPEC.md)。

---

## 本地开发

数据采集：

```bash
pip install -r requirements.txt
python scripts/collect_all.py    # 拉数据 → 更新 data/*.json → 推 GitHub Raw
```

后端（Vercel 本地模拟）：

```bash
# 用 vercel dev 或本地 uvicorn
uvicorn backend.main:app --port 8000
```

前端：

```bash
cd frontend && npm install && npm run dev
```

---

**最后更新**：2026-07-30（neat-freak 第二轮补全）
