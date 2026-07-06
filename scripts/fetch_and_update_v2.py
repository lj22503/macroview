"""
每日数据拉取脚本 v2 — 多源备份版
拉取 FRED + yfinance + AKShare → merge → 分层存储 → 推送 GitHub
"""

import base64, os, sys, json, requests
from datetime import date, datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
sys.path.insert(0, str(SCRIPT_DIR))

from source_adapters.fred_adapter import fetch_all_fred
from source_adapters.yfinance_adapter import fetch_all_yfinance
from source_adapters.akshare_adapter import fetch_all_akshare
import merge, storage

FRED_API_KEY = os.getenv("FRED_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "lj22503")
GITHUB_REPO = os.getenv("GITHUB_REPO", "macroview")
GITHUB_BRANCH = "main"


def fetch_china_data() -> dict:
    print("\n[China/AKShare] 拉取中国数据...")
    try:
        import akshare as ak, pandas as pd
    except ImportError:
        print("  [WARN] akshare 未安装")
        return {}

    result = {}

    # PMI
    try:
        df = ak.macro_china_pmi()
        if df is not None and len(df) > 0:
            cols = df.columns.tolist()
            result["cn_pmi_official"] = {"value": float(df.iloc[0][cols[1]]), "name": "官方制造业PMI", "source": "AKShare"}
            result["cn_pmi_caixin"] = {"value": float(df.iloc[0][cols[3]]), "name": "财新制造业PMI", "source": "AKShare"}
            print(f"  cn_pmi_official: {result['cn_pmi_official']['value']}")
            print(f"  cn_pmi_caixin: {result['cn_pmi_caixin']['value']}")
    except Exception as e:
        print(f"  [ERROR] PMI: {e}")
        result["cn_pmi_official"] = {"value": None, "name": "官方制造业PMI", "source": "AKShare"}
        result["cn_pmi_caixin"] = {"value": None, "name": "财新制造业PMI", "source": "AKShare"}

    # CPI
    try:
        df = ak.macro_china_cpi()
        if df is not None and len(df) > 0:
            cols = df.columns.tolist()
            yoy_col = [c for c in cols if '同比' in str(c)][0]
            result["cn_cpi_yy"] = {"value": float(df.iloc[0][yoy_col]), "name": "CPI同比", "source": "AKShare"}
            print(f"  cn_cpi_yy: {result['cn_cpi_yy']['value']}%")
    except Exception as e:
        print(f"  [ERROR] CPI: {e}")
        result["cn_cpi_yy"] = {"value": None, "name": "CPI同比", "source": "AKShare"}

    # PPI
    try:
        df = ak.macro_china_ppi()
        if df is not None and len(df) > 0:
            cols = df.columns.tolist()
            yoy_col = [c for c in cols if '同比' in str(c)][0]
            result["cn_ppi_yy"] = {"value": float(df.iloc[0][yoy_col]), "name": "PPI同比", "source": "AKShare"}
            print(f"  cn_ppi_yy: {result['cn_ppi_yy']['value']}%")
    except Exception as e:
        print(f"  [ERROR] PPI: {e}")
        result["cn_ppi_yy"] = {"value": None, "name": "PPI同比", "source": "AKShare"}

    # M1/M2
    try:
        df = ak.macro_china_money_supply()
        if df is not None and len(df) > 0:
            cols = df.columns.tolist()
            m1_col = [c for c in cols if 'M1' in str(c) and '同比' in str(c)][0]
            m2_col = [c for c in cols if 'M2' in str(c) and '同比' in str(c)][0]
            m1_yoy = float(df.iloc[0][m1_col])
            m2_yoy = float(df.iloc[0][m2_col])
            spread = round(m1_yoy - m2_yoy, 1)
            result["cn_m1_m2_spread"] = {"value": spread, "m1_yoy": m1_yoy, "m2_yoy": m2_yoy, "spread": spread, "trend": "收窄" if spread > -3 else "持平", "name": "M1-M2剪刀差", "source": "AKShare"}
            print(f"  cn_m1_m2_spread: {spread}%")
    except Exception as e:
        print(f"  [ERROR] M1/M2: {e}")
        result["cn_m1_m2_spread"] = {"value": None, "name": "M1-M2剪刀差", "source": "AKShare"}

    # LPR
    try:
        df = ak.macro_china_lpr()
        if df is not None and len(df) > 0:
            for i in range(len(df)):
                if pd.notna(df.iloc[i]["LPR1Y"]):
                    result["cn_lpr_1y"] = {"value": float(df.iloc[i]["LPR1Y"]), "name": "1年期LPR", "source": "AKShare"}
                    print(f"  cn_lpr_1y: {result['cn_lpr_1y']['value']}%")
                    break
            if "cn_lpr_1y" not in result:
                result["cn_lpr_1y"] = {"value": None, "name": "1年期LPR", "source": "AKShare"}
    except Exception as e:
        print(f"  [ERROR] LPR: {e}")
        result["cn_lpr_1y"] = {"value": None, "name": "1年期LPR", "source": "AKShare"}

    # 中债收益率
    try:
        df = ak.bond_china_yield()
        if df is not None and len(df) > 0:
            for i in range(len(df)):
                row = df.iloc[i]
                if '国债' in str(row.get('债券类型', '')):
                    val_10y = row.get('10年')
                    if pd.notna(val_10y):
                        result["cn_10y_yield"] = {"value": float(val_10y) / 100, "name": "10Y中债收益率", "source": "AKShare"}
                        print(f"  cn_10y_yield: {result['cn_10y_yield']['value']}%")
                        break
            if "cn_10y_yield" not in result:
                result["cn_10y_yield"] = {"value": None, "name": "10Y中债收益率", "source": "AKShare"}
    except Exception as e:
        print(f"  [ERROR] 中债收益率: {e}")
        result["cn_10y_yield"] = {"value": None, "name": "10Y中债收益率", "source": "AKShare"}

    # 北向资金
    try:
        df = ak.stock_hsgt_hist_em(symbol='北向资金')
        if df is not None and len(df) >= 1:
            cols = df.columns.tolist()
            net_col = [c for c in cols if '净买额' in str(c)][0]
            north_today = float(df.iloc[0][net_col])
            north_3d = sum([float(df.iloc[i][net_col]) for i in range(min(3, len(df)))])
            result["north_money_3d"] = {"value": round(north_3d, 2), "name": "北向资金3日累计", "source": "AKShare"}
            result["north_money"] = {"value": round(north_today, 2), "name": "北向资金当日", "source": "AKShare"}
            print(f"  north_money_3d: {north_3d}亿")
    except Exception as e:
        print(f"  [ERROR] 北向资金: {e}")
        result["north_money_3d"] = {"value": None, "name": "北向资金3日累计", "source": "AKShare"}
        result["north_money"] = {"value": None, "name": "北向资金当日", "source": "AKShare"}

    print("  [INFO] 社融数据跳过（API不稳定）")
    result["cn_social_financing"] = {"value": None, "name": "社融增量", "source": "AKShare"}
    return result


def calculate_signals(fred_merged: dict, china_data: dict) -> dict:
    print("\n[Signal] 计算信号...")
    WEIGHTS = {"cn_us_spread": 0.20, "m1_m2_spread": 0.25, "vix": 0.15, "north_money": 0.15, "credit_spread": 0.25}
    cn_10y = china_data.get("cn_10y_yield", {}).get("value")
    us_10y = fred_merged.get("us_10y_yield", {}).get("value")
    cn_us_spread = (cn_10y - us_10y) * 100 if cn_10y and us_10y else None

    def score(s, thresholds):
        if s is None: return 0
        for i, t in enumerate(sorted(thresholds)):
            if s < t: return len(thresholds) - i - 1
        return 0

    vix_val = fred_merged.get("vix", {}).get("value")
    signals = {
        "cn_us_spread": score(cn_us_spread, [-250, -200, -150]),
        "m1_m2_spread": score(china_data.get("cn_m1_m2_spread", {}).get("spread"), [-8, -5, -3]),
        "vix": score(vix_val, [14, 18, 22, 28]),
        "north_money": score(china_data.get("north_money_3d", {}).get("value"), [-100, -50, 50]),
        "credit_spread": score(fred_merged.get("hy_spread_oas", {}).get("value"), [350, 450, 550]),
    }
    total_score = sum(signals[f] * WEIGHTS[f] for f in WEIGHTS)
    bias = "RISK_ON" if total_score > 0.3 else "RISK_OFF" if total_score < -0.3 else "NEUTRAL"
    return {"bias": bias, "score": round(total_score, 2), "factor_details": {}}


def push_to_github(data: dict, filename: str = "all_indicators.json") -> bool:
    if not GITHUB_TOKEN:
        storage.save_latest(data)
        return False
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/data/{filename}"
    sha = None
    try:
        resp = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"}, timeout=10)
        if resp.status_code == 200:
            sha = resp.json().get("sha")
    except Exception:
        pass
    content = json.dumps(data, ensure_ascii=False, indent=2)
    payload = {"message": f"chore: 更新宏观数据 {datetime.now().strftime('%Y-%m-%d %H:%M')}", "content": base64.b64encode(content.encode()).decode(), "branch": GITHUB_BRANCH}
    if sha:
        payload["sha"] = sha
    try:
        resp = requests.put(url, headers={"Authorization": f"token {GITHUB_TOKEN}"}, json=payload, timeout=15)
        if resp.status_code in [200, 201]:
            print(f"  [SUCCESS] 已推送 {filename}")
            return True
        print(f"  [ERROR] GitHub push failed: {resp.status_code}")
    except Exception as e:
        print(f"  [ERROR] GitHub push: {e}")
    return False


def main():
    print("=" * 50)
    print("宏观仪表盘 v2 — 多源备份版")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    print("\n[FRED] 拉取 FRED 数据...")
    fred_results = fetch_all_fred()
    for k, r in fred_results.items():
        print(f"  {k}: {r.value} ({r.source}, {r.quality})")

    print("\n[yfinance] 拉取 yfinance 数据...")
    yf_results = fetch_all_yfinance()
    for k, r in yf_results.items():
        print(f"  {k}: {r.value} ({r.source})" if r.is_valid() else f"  {k}: NULL ({r.quality})")

    print("\n[AKShare] 拉取 AKShare 资产备用...")
    ak_results = fetch_all_akshare()
    for k, r in ak_results.items():
        print(f"  {k}: {r.value} ({r.source})" if r.is_valid() else f"  {k}: NULL ({r.error})")

    china_data = fetch_china_data()

    print("\n[Merge] 合并多源数据...")
    merged = merge.merge_results(fred_results, yf_results, ak_results)

    fred_for_signals = merge.build_fred(merged)
    assets_out = merge.build_assets(merged)
    overview = calculate_signals(fred_for_signals, china_data)

    output = {
        "meta": {"updated_at": datetime.now().isoformat(), "data_date": date.today().isoformat(), "status": "success"},
        "overview": overview,
        "china": china_data,
        "fred": fred_for_signals,
        "assets": assets_out,
    }

    freshness = storage.assess_freshness(output["meta"]["updated_at"])
    valid = sum(1 for v in merged.values() if v["value"] is not None)
    total = len(merged)
    print(f"\n  覆盖: {valid}/{total} ({freshness})")

    print("\n[Storage] 分层存储...")
    storage.save_latest(output, freshness=freshness)
    storage.save_archive(output)
    storage.update_meta(date.today().isoformat(), freshness, {k: v["source"] for k, v in merged.items()}, total, valid)
    print(f"  已保存: data/all_indicators.json")

    print("\n[Push] 推送 GitHub...")
    pushed = push_to_github(output)
    if not pushed:
        print("  [WARN] GitHub 推送失败，数据已存本地")

    print("\n" + "=" * 50)
    print("完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
