# 宏观仪表盘 SPEC.md

## 1. 项目概述

**项目名称**：Macro Dashboard（宏观仪表盘）
**项目类型**：量化投研系统（数据采集→信号计算→观点映射→自动简报）
**核心功能**：中国视角全球大类资产宏观量化展示 + 观点映射 + 信号合成 + 自动简报
**目标用户**：投顾从业者、机构投资者

---

## 2. 设计目标

| 目标 | 说明 |
|---|---|
| **全链路自动化** | 数据采集 → 指标计算 → 信号生成 → 观点输出，全流程无需人工干预 |
| **中国视角优先** | 所有指标围绕中国投资者的资产配置决策链组织 |
| **可解释性** | 每个指标输出附带观点映射（signal/view/narrative），直接服务客户沟通 |
| **零商业数据依赖** | 100%基于公开数据源（FRED + AKShare + yfinance） |

---

## 3. 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│  展示层（前端）                                            │
│  React + ECharts                                          │
│  读取后端 API + GitHub Raw JSON                           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│  Agent 交互层                                             │
│  观点合成引擎 + 自然语言查询 + 自动简报生成                 │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│  计算与信号层（核心）                                      │
│  指标计算引擎 + 信号合成引擎 + 观点映射引擎                │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│  数据采集层                                                │
│  FRED 适配器 + AKShare 适配器 + yfinance 适配器           │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. API 设计

### 4.1 统一全景接口（首屏使用）

`GET /api/v1/dashboard`

```json
{
  "meta": {
    "updated_at": "2026-06-21T09:00:00+08:00",
    "data_date": "2026-06-20",
    "status": "success"
  },
  "overview": {
    "bias": "RISK_ON",
    "confidence": 68,
    "score": 1.2,
    "primary_driver": ["中美利差收窄", "M1-M2剪刀差改善", "VIX正常"],
    "suggestions": {
      "equity": 65,
      "bond": 25,
      "gold": 10,
      "cash": 0
    },
    "narrative": "国内流动性改善叠加外部压力缓解，温和复苏延续...",
    "factor_details": {
      "cn_us_spread": { "signal": 1, "weight": 0.20, "contribution": 0.20 },
      "m1_m2_spread": { "signal": 1, "weight": 0.25, "contribution": 0.25 },
      "vix": { "signal": 1, "weight": 0.15, "contribution": 0.15 },
      "north_money": { "signal": 0, "weight": 0.15, "contribution": 0 },
      "credit_spread": { "signal": 0, "weight": 0.25, "contribution": 0 }
    }
  },
  "china_core": { ... },
  "global_macro": { ... },
  "fx_liquidity": { ... },
  "assets": { ... },
  "risk_monitor": { ... },
  "events": [ ... ]
}
```

### 4.2 独立模块接口

| 端点 | 返回内容 |
|---|---|
| `GET /api/v1/overview` | 顶层决策锚点（bias/confidence/score/primary_driver/仓位建议/narrative） |
| `GET /api/v1/china-core` | PMI、CPI/PPI、社融、M1-M2剪刀差、LPR |
| `GET /api/v1/global-macro` | 美国ISM PMI、核心PCE、美联储资产负债表、ON RRP |
| `GET /api/v1/fx-liquidity` | DXY、中美利差、USD/CNH、USD/JPY |
| `GET /api/v1/assets` | 标普500、沪深300、黄金、原油、10Y美债 |
| `GET /api/v1/risk` | VIX、MOVE、高收益债利差、A股隐含波动率 |
| `GET /api/v1/events` | 经济日历、实时快讯 |

### 4.3 字段命名规范

**后端存储/传输**：使用数据字典英文 ID（如 `cn_pmi_official`、`cn_us_10y_spread`）
**对客展示**：中文简称（如"官方制造业PMI"、"中美利差"）

---

## 5. 信号合成引擎

### 5.1 各因子打分（-2 到 +2）

| 因子 | +2 | +1 | 0 | -1 | -2 |
|---|---|---|---|---|---|
| **中美利差信号** | >-150bp且收窄 | -200~-150bp且收窄 | -250~-200bp持平 | <-250bp走阔 | <-300bp加速走阔 |
| **M1-M2剪刀差信号** | 收窄且>-3% | 收窄但<-3% | 持平 | 走阔但>-8% | 走阔且<-8% |
| **VIX信号** | <14 | 14-18 | 18-22 | 22-28 | >28 |
| **北向资金信号** | 3日累计>100亿 | >50亿 | -50~+50亿 | <-50亿 | <-100亿 |
| **信用利差信号** | <350bp | 350-450bp | 450-550bp | 550-700bp | >700bp |

### 5.2 权重配置

| 因子 | 权重 | 理由 |
|---|---|---|
| 中美利差信号 | 20% | 决定外资行为，是当前市场核心矛盾 |
| M1-M2剪刀差信号 | 25% | 决定国内增量资金，权重最高 |
| VIX信号 | 15% | 反映全球风险偏好 |
| 北向资金信号 | 15% | 反映外资即时态度 |
| 信用利差信号 | 25% | 系统性风险开关 |

### 5.3 仓位映射

| 总分范围 | 权益仓位 | 叙事标签 |
|---|---|---|
| +1.5 ~ +2.0 | 80% ~ 100% | 全面扩张 |
| +0.5 ~ +1.5 | 60% ~ 80% | 温和复苏 |
| -0.5 ~ +0.5 | 40% ~ 60% | 结构分化 |
| -1.5 ~ -0.5 | 20% ~ 40% | 收缩压力 |
| -2.0 ~ -1.5 | 0% ~ 20% | 系统性风险 |

---

## 6. 数据字典（完整字段）

### 6.1 顶层概览（决策锚点层）

| 字段名（英文ID） | 中文简称 | 模块归属 | 数据源 | 更新频率 |
|---|---|---|---|---|
| `vix` | VIX恐慌指数 | 顶层概览 | FRED (`VIXCLS`) | 日频/实时 |
| `move_idx` | MOVE债券波动率 | 顶层概览 | FRED (`MOVE`) | 日频 |
| `gpr_idx` | 地缘政治风险指数 | 顶层概览 | Iacoviello/FRED | 月频 |
| `north_money_3d` | 北向资金（3日累计） | 顶层概览 | AKShare | 日频 |
| `south_money` | 南向资金（当日） | 顶层概览 | AKShare | 日频 |

### 6.2 中国内核

| 字段名（英文ID） | 中文简称 | 数据源 | 更新频率 |
|---|---|---|---|
| `cn_pmi_official` | 官方制造业PMI | AKShare | 月频 |
| `cn_pmi_caixin` | 财新制造业PMI | AKShare | 月频 |
| `cn_cpi_yy` | CPI同比 | AKShare | 月频 |
| `cn_ppi_yy` | PPI同比 | AKShare | 月频 |
| `cn_social_financing` | 社融存量同比 | AKShare | 月频 |
| `cn_m1_m2_spread` | M1-M2增速剪刀差 | AKShare | 月频 |
| `cn_lpr_1y` | 1年期LPR | AKShare | 月频 |
| `cn_repo_7d` | 7天逆回购利率 | PBOC/AKShare | 不定时 |

### 6.3 全球宏观

| 字段名（英文ID） | 中文简称 | 数据源 | 更新频率 |
|---|---|---|---|
| `us_ism_pmi` | 美国ISM制造业PMI | FRED (`NAPM`) | 月频 |
| `us_core_pce_yy` | 美国核心PCE同比 | FRED (`PCEPILFE`) | 月频 |
| `us_cpi_yy` | 美国CPI同比 | FRED (`CPIAUCSL`) | 月频 |
| `fed_balance_sheet` | 美联储资产负债表规模 | FRED (`WALCL`) | 周频 |
| `on_rrp_balance` | ON RRP隔夜逆回购 | FRED (`RRPONTSYD`) | 日频 |
| `fed_funds_rate` | 联邦基金利率 | FRED (`FEDFUNDS`) | 不定时 |

### 6.4 美元与流动性

| 字段名（英文ID） | 中文简称 | 数据源 | 更新频率 |
|---|---|---|---|
| `dxy_idx` | DXY美元指数 | FRED (`DTWEXBGS`) | 日频/实时 |
| `cn_us_10y_spread` | 中美利差(10Y) | 中债+FRED | 日频 |
| `usd_cnh` | USD/CNH | Yahoo/AKShare | 实时 |
| `usd_jpy` | USD/JPY | Yahoo/AKShare | 实时 |
| `cfets_idx` | CFETS人民币汇率指数 | 货币网爬虫 | 周频 |

### 6.5 全球核心资产

| 字段名（英文ID） | 中文简称 | 数据源 | 更新频率 |
|---|---|---|---|
| `spx` | 标普500 | FRED/Yahoo | 实时 |
| `hs300` | 沪深300 | AKShare | 实时 |
| `hsi` | 恒生指数 | Yahoo/AKShare | 实时 |
| `nk225` | 日经225 | Yahoo | 实时 |
| `us_10y_yield` | 10Y美债收益率 | FRED (`DGS10`) | 日频 |
| `cn_10y_yield` | 10Y中债收益率 | 中债信息网/AKShare | 日频 |
| `gold_spot` | 黄金现货 | Yahoo/AKShare | 实时 |
| `wti_oil` | WTI原油 | Yahoo/AKShare | 实时 |
| `btc_usd` | 比特币 | FRED/Yahoo | 实时 |

### 6.6 波动率与风险

| 字段名（英文ID） | 中文简称 | 数据源 | 更新频率 |
|---|---|---|---|
| `hy_spread_oas` | 美国高收益债利差 | FRED (`BAMLH0A0HYM2`) | 日频 |
| `ted_spread` | TED利差 | FRED (`TEDRATE`) | 日频 |
| `cn_vix` | A股隐含波动率 | 中证指数/爬虫 | 日频 |

---

## 7. 每日宏观简报模板

### 7.1 结构（三段式）

| 板块 | 内容 | 目的 |
|---|---|---|
| 一句话观点（封面） | 宏观状态标签 + 总分 + 核心结论 | 3秒知道结论 |
| 逻辑拆解（内页） | 各因子得分 + 变化方向 + 归因 | 知道为什么 |
| 配置建议（结尾） | 股/债/金/现仓位比例 + 风险提示 | 知道怎么做 |

### 7.2 模板

```
📋 每日宏观简报 · {{DATE}}

{{MACRO_LABEL}} · 总分 {{SCORE}} / 2.0 · 权益建议仓位 {{EQUITY_PCT}}%

核心观点：{{ONE_SENTENCE_SUMMARY}}

📌 逻辑拆解

| 因子 | 信号 | 变化 | 简评 |
|---|---|---|---|
| 中美利差 | {{SPREAD_SIGNAL}} | {{SPREAD_TREND}} | {{SPREAD_COMMENT}} |
| M1-M2剪刀差 | {{M1_SIGNAL}} | {{M1_TREND}} | {{M1_COMMENT}} |
| VIX | {{VIX_SIGNAL}} | {{VIX_TREND}} | {{VIX_COMMENT}} |
| 北向资金 | {{NORTH_SIGNAL}} | {{NORTH_TREND}} | {{NORTH_COMMENT}} |
| 信用利差 | {{CREDIT_SIGNAL}} | {{CREDIT_TREND}} | {{CREDIT_COMMENT}} |

主要驱动：{{PRIMARY_DRIVERS}}

🎯 配置建议

| 资产类别 | 建议仓位 | 说明 |
|---|---|---|
| 权益（A股） | {{EQUITY_PCT}}% | {{EQUITY_NOTE}} |
| 债券 | {{BOND_PCT}}% | {{BOND_NOTE}} |
| 黄金 | {{GOLD_PCT}}% | {{GOLD_NOTE}} |
| 现金 | {{CASH_PCT}}% | {{CASH_NOTE}} |

风险提示：{{RISK_WARNING}}

*数据来源：FRED / AKShare / 中债信息网 · 数据日期 {{DATA_DATE}}*
```

---

## 8. 页面结构（7大模块）

| 模块 | 内容 |
|---|---|
| **顶部状态栏** | RISK ON/OFF + 置信度 + 主要驱动因素 + 权益仓位建议 |
| **模块一：顶层概览** | VIX、MOVE、北向资金3日累计、Risk Score可视化 |
| **模块二：中国内核** | PMI、CPI/PPI、社融、M1-M2剪刀差、LPR + 观点话术 |
| **模块三：全球宏观** | 美国ISM PMI、核心PCE、美联储资产负债表 + 观点话术 |
| **模块四：美元与流动性** | DXY、中美利差、USD/CNH、USD/JPY + 观点话术 |
| **模块五：全球核心资产** | 标普500、沪深300、黄金、原油、10Y美债 + 观点话术 |
| **模块六：波动率与风险** | 高收益债利差、MOVE、A股隐含波动率 + 观点话术 |
| **模块七：事件流** | 经济日历、实时快讯 |

---

## 9. 设计风格

- **主色**：深色背景（#0a0e17 / #111827）
- **强调色**：金色（#f0b90b / #ffd700）
- **辅助色**：绿色（#00d26a 看多）、红色（#f6465d 看空）
- **字体**：JetBrains Mono（数字）、Inter（正文）

---

## 10. 部署架构

| 组件 | 部署方式 |
|---|---|
| 数据采集脚本 | 本地 Windows + Cron |
| FastAPI 后端 | Render 免费层级 |
| 前端 | Vercel 静态部署 |

---

## 11. 成本

| 项目 | 成本 |
|---|---|
| FRED API | 免费 |
| AKShare | 免费 |
| yfinance | 免费 |
| Render | 免费 |
| Vercel | 免费 |
| **合计** | **0元** |
