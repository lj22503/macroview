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

---

## neat-freak 收尾 — 2026-07-30

> 本段由 neat-freak 收尾执行，承接 06-23 之后的真实状态

### 06-23 → 07-30 之间的关键 commits（PROGRESS 漏记 37 天）

| commit | 日期 | 摘要 |
|--------|------|------|
| 4d947d8 | 2026-07-06 | feat: API 层迁移 Vercel + 数据采集脚本增强 |
| 55e36d9 | 2026-07-06 后 | fix(vercel): declare Python runtime |
| 2a95773 | 2026-07 | fix(vercel): use builds field explicitly |
| 58dc56f | 2026-07 | fix(vercel): move Python entry to src/index.py |
| 7d67d5b | 2026-07 | fix(vercel): explicit dual builds |
| 12e8db1 | 2026-07 | test(vercel): minimal FastAPI app |
| e442e77 | 2026-07 | chore: 测试 SSH 推送 |
| ~5 个 | 2026-07-13~19 | `chore: 更新宏观数据 YYYY-MM-DD HH:MM`（每日自动数据推送） |
| 844519f | 2026-07-24 | neat-freak: 宏观仪表盘 知识收尾 2026-07-24 |

### 部署真实状态（修正 07-24 报告中的不准确描述）

- **后端** Vercel Python Serverless（`src/index.py` + Mangum，非原 Render）
- **前端** Vercel 静态构建
- **数据采集** 本地 AKShare 脚本 → GitHub Raw commit
- 见 `VERCEL_MIGRATION.md` §三「实际方案」了解 5 次迭代后的最终配置

### 本轮（07-30）执行项（来自 07-24 neat-freak 报告 §五）

| 项 | 动作 | 状态 |
|----|------|------|
| `data/all_indicators.json + data/meta.json` 修改未提交 | ✅ commit（CLAUDE.md §31 规定，data 是当日 09:05 新鲜） | ✅ |
| PROGRESS.md 37 天未同步 | 追加 06-23→07-30 段（本段） | ✅ |
| `.gitignore` 末尾空白 + UTF-16 LE + BOM 编码异常 | 重写为 UTF-8 + 清理末尾 | ✅ |
| `VERCEL_MIGRATION.md` vs `vercel.json` 不一致 | 改 VERCEL_MIGRATION.md：加 §三「实际方案」描述 5 次迭代 | ✅ |
| `README.md` 14 行残缺 | 重写：从 SPEC §3/§4/§5 提炼，正文 14 行→完整章节 | ✅ |
| 命名 `宏观仪表盘 / macroview`（跨项目 4 处之一） | 不改名（queue.md 已列待跨项目统一），此处仅标注 | 注 |

### 跨项目命名状态（本项目部分）

queue.md 列 4 处命名待统一：

| idx | 本地目录 | GitHub remote |
|----:|----------|--------------|
|  5 | investment-advisory-skills | SoloAdvisor-Toolkit |
|  6 | narrative-skill | diaolong-skill |
|  8 | mangofolio | mangofolio-skill |
| **10** | **宏观仪表盘**（中文） | **macroview**（英文）|

### 07-24 §六 遗留处置

| 项 | 07-30 状态 |
|----|-----------|
| SPEC.md 12.6KB 未读全文 | 未读，文章节级指向已并入 README.md |
| docs/ 子目录内容未读 | 未读，本轮不展开 |
| VERCEL_MIGRATION.md 完整内容未读 | ✅ 07-30 读 + 改 |
| 5 因子信号权重（20/25/15/15/25）实际是否运行 | 未实测，本轮不展开 |

### 待办（沿用 07-24 §五 + 本轮新识别）

- **P0**：验证 Vercel 部署 + GitHub Actions 每日数据 cron 仍在触发（07-19 后无新 `chore: 更新数据` commit，可能 cron 断了，**待查**）
- **P1**：黄金/USD/CNH/USD/JPY/日经225 可靠源（等 yfinance 解限）
- **P1**：南向资金、CFETS 指数
- **P1**：VIX 历史走势图、错误态/空态 UI 完善
- **跨项目 P2**：4 处命名不一致统一决策

---

*neat-freak 收尾按 07-24 报告 §五 + 用户 2 次决策（改 VERCEL_MIGRATION / 补 README），共动 5 文件：`.gitignore`（UTF-16 → UTF-8）/ `README.md`（14 行 → 80 行）/ `VERCEL_MIGRATION.md`（加实际方案章节）/ `PROGRESS.md`（追加 07-30 段）/ `data/*.json`（commit 当日新鲜数据）。*
