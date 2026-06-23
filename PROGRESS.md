# 宏观仪表盘 · 工作进度

> 最后更新：2026-06-23

## 当前阶段：收尾 & 部署验证

---

## 已完成

### 后端 - 数据源修复（2026-06-23）
- [x] `backend/main.py` — 新增 akshare 备援层，yfinance 限流时自动切换
  - 沪深300: `stock_zh_index_daily("sh000300")` ✅ 已验证
  - 恒生指数: `stock_hk_index_daily_sina("HSI")` ✅ 已验证
  - 黄金: 无可靠替代源（`spot_golden_benchmark_sge` 数据只到 2016年）
- [x] `backend/requirements.txt` — 添加 `akshare>=1.12.0`
- [x] `backend/get_assets` 端点也接入 akshare 备援

### 前端 - 新鲜度感知（2026-06-23）
- [x] `macroApi.js` — `normalizeGithubData()` 新增 `data_freshness` 计算
  - 当天数据 → `fresh`，昨天 → `stale`，更旧 → `expired`

### 数据状态（2026-06-23 本地验证）
| 资产 | 状态 | 来源 |
|---|---|---|
| 沪深300 | ✅ 5059.66 | AKShare |
| 恒生指数 | ✅ 23768.52 | AKShare |
| 标普500 | ✅ 7472.79 | FRED |
| 比特币 | ✅ 63932.91 | FRED |
| 日经225 | ❌ null | 无替代 |
| 黄金 | ❌ null | 无替代 |
| WTI原油 | ✅ 84.65 | FRED |
| USD/CNH | ❌ null | 无替代 |
| USD/JPY | ❌ null | 无替代 |

---

## 待完成

### P0
- [ ] Vercel 部署验证
- [ ] 验证 GitHub Actions 定时数据正常更新

### P1
- [ ] VIX 历史走势图
- [ ] 页面叙事优化
- [ ] 错误态/空态 UI 完善

### P2
- [ ] 黄金、USD/CNH、USD/JPY、日经225可靠数据源（等 yfinance 解限）
- [ ] 南向资金、CFETS指数

---

## Git 状态
```
89fc9eb fix: akshare fallback for hs300/hsi assets + data_freshness in frontend
2bbaa3f chore: 更新宏观数据 2026-06-23 10:44
```
