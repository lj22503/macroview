# 宏观仪表盘 · 工作进度

> 最后更新：2026-06-22

## 当前阶段：前端补全 & 数据完善

---

## 已完成

### 文档
- [x] `SPEC.md` — 完整规格说明（7大模块、60+字段、数据字典）
- [x] `docs/页面指标解释.txt` — 小白版字段解释文档（每个字段配"打个比方"）
- [x] `docs/数据字典.txt` — 开发者版完整字段定义（含数据源、更新频率、阈值）
- [x] `docs/观点映射字典.txt` — 信号 → 观点话术映射规则
- [x] `docs/仪表盘架构方案.txt` — 架构设计文档

### 前端（frontend/）
- [x] `Dashboard.jsx` — 7大模块完整渲染，含 FIELD_EXPLANATIONS tooltip
- [x] `macroApi.js` — normalize 函数将 GitHub JSON 转为前端格式
- [x] 字段展示完整度：

| 模块 | 状态 |
|---|---|
| 顶层概览 | ✅ bias/confidence/score/primary_driver/suggestions/narrative |
| 中国内核 | ✅ PMI官方/财新、CPI、PPI、M1-M2、LPR、社融、北向资金、中债收益率 |
| 全球宏观 | ✅ ISM PMI、核心PCE、美CPI、联邦基金利率、美联储资产负债表、隔夜逆回购、2Y美债 |
| 美元与流动性 | ✅ DXY、中美利差、USD/CNH、USD/JPY |
| 全球核心资产 | ✅ 标普500、沪深300、恒生、日经225、黄金、比特币、WTI原油、10Y/2Y美债、中债 |
| 波动率与风险 | ✅ VIX、MOVE、高收益债利差、TED利差、A股VIX |

### 后端（backend/）
- [x] `macro_agent.py` — 数据采集 Agent（FRED + AKShare + yfinance）
- [x] `signal_engine.py` — 5因子打分引擎（中美利差/M1-M2/VIX/北向/信用利差）
- [x] `narrative_engine.py` — 自然语言叙事生成
- [x] `main.py` — FastAPI 服务入口

### 数据管道
- [x] GitHub Raw JSON fallback（前端直接读取 `lj22503/macroview/data/all_indicators.json`）
- [x] GitHub Actions 定时更新数据

---

## 待完成

### P0（上线前必须）
- [ ] GitHub push（网络不稳定，pending commit `721f6de`）
- [ ] Vercel 部署验证
- [ ] 数据完整性和新鲜度验证（月频数据标注月份）

### P1（体验优化）
- [ ] VIX 历史走势图（`VIXChart.jsx` 已存在，需接入真实数据）
- [ ] 页面叙事优化（每个模块加下划线/感叹号等视觉提示）
- [ ] 错误态/空态 UI 完善

### P2（后续迭代）
- [ ] 观点映射话术直接显示在卡片上（signal view narrative）
- [ ] 经济日历 / 事件流模块
- [ ] 自动简报生成（Section 7 模板落地）
- [ ] 南向资金（`south_money`）、CFETS指数、地缘政治风险指数等后续字段

---

## 技术债务
- `frontend/src/styles/dashboard.css` — impeccable 设计建议：侧边色块/overused-font/gradient-text（暂不处理，用户已确认风格）

---

## Git 状态
```
721f6de fix: add missing useEffect import in Dashboard; docs: add 页面指标解释
6565e89 feat: 补全缺失数据字段，优化页面叙事
8b53cb4 feat: redesign dashboard UI - 3-column layout, card grid, risk cards
```
