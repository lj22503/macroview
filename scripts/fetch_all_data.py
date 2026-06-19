"""
本地宏观数据拉取脚本
同时拉取：中国数据（AKShare）+ 美国数据（FRED + yfinance）
生成 JSON -> push 到 GitHub
"""

import os
import sys
import json
import subprocess
from datetime import datetime

# Windows 控制台编码修复
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import requests
import yfinance as yf

try:
    import akshare as ak
except ImportError:
    print("ERROR: Please install AKShare: pip install akshare")
    exit(1)


FRED_API_KEY = os.getenv("FRED_API_KEY", "")


def fetch_fred(series_id: str) -> float | None:
    if not FRED_API_KEY:
        return None
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if "observations" in data and data["observations"]:
            val = data["observations"][0]["value"]
            return float(val) if val != "." else None
    except Exception as e:
        print(f"  [ERROR] FRED {series_id}: {e}")
    return None


def fetch_yfinance(symbol: str) -> float | None:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")
        if not hist.empty:
            price = hist["Close"].dropna().iloc[-1]
            return round(float(price), 2)
    except Exception as e:
        print(f"  [ERROR] yfinance {symbol}: {e}")
    return None


def fetch_china_data():
    data = {}

    # PMI
    try:
        df = ak.macro_china_pmi()
        if not df.empty:
            val = df.iloc[0]["pmi"] if "pmi" in df.columns else df.iloc[0].iloc[0]
            data["pmi"] = {"value": float(val), "name": "中国 PMI"}
            print("  [OK] PMI")
    except Exception as e:
        print(f"  [FAIL] PMI: {e}")

    # M1/M2
    try:
        df = ak.macro_china_money_supply()
        if not df.empty:
            cols = df.columns.tolist()
            m1_col = next((c for c in cols if "m1" in c.lower() and "yoy" in c.lower()), None)
            m2_col = next((c for c in cols if "m2" in c.lower() and "yoy" in c.lower()), None)
            if m1_col and m2_col:
                m1 = float(df.iloc[0][m1_col])
                m2 = float(df.iloc[0][m2_col])
                data["m1m2"] = {
                    "m1_yoy": m1,
                    "m2_yoy": m2,
                    "spread": round(m2 - m1, 1),
                    "name": "M1-M2 剪刀差",
                }
            print("  [OK] M1/M2")
    except Exception as e:
        print(f"  [FAIL] M1/M2: {e}")

    # LPR
    try:
        df = ak.macro_china_lpr()
        if not df.empty:
            cols = df.columns.tolist()
            lpr_col = next((c for c in cols if "1y" in c.lower() or "一年" in c.lower()), None)
            if lpr_col:
                data["lpr"] = {"value": float(df.iloc[0][lpr_col]), "name": "LPR (1年期)"}
            print("  [OK] LPR")
    except Exception as e:
        print(f"  [FAIL] LPR: {e}")

    return data


def main():
    print("=" * 60)
    print("Start fetching macro data...")
    print("=" * 60)

    print("\n[China Data - AKShare]")
    china = fetch_china_data()

    print("\n[US Macro Data - FRED]")
    fred_data = {
        "vix": {"value": fetch_fred("VIXCLS"), "name": "VIX"},
        "dgs10": {"value": fetch_fred("DGS10"), "name": "10Y美债", "unit": "%"},
        "dgs2": {"value": fetch_fred("DGS2"), "name": "2Y美债", "unit": "%"},
        "pce": {"value": fetch_fred("PCEPILFE"), "name": "核心PCE", "unit": "%"},
        "ism": {"value": fetch_fred("ISMINDUS"), "name": "ISM PMI"},
        "dxy": {"value": fetch_fred("DTWEXBGS"), "name": "DXY美元指数"},
        "baml": {"value": fetch_fred("BAMLM0A0CM"), "name": "高收益债利差", "unit": "bp"},
    }
    for k, v in fred_data.items():
        if v["value"]:
            print(f"  [OK] {v['name']}: {v['value']}")

    print("\n[Global Assets - yfinance]")
    assets_data = {
        "sp500": {"value": fetch_yfinance("SPY"), "name": "S&P 500"},
        "hs300": {"value": fetch_yfinance("000300.SS"), "name": "沪深300"},
        "gold": {"value": fetch_yfinance("GC=F"), "name": "黄金"},
        "crude": {"value": fetch_yfinance("CL=F"), "name": "原油"},
        "usd_cnh": {"value": fetch_yfinance("CNHF=X"), "name": "USD/CNH"},
    }
    for k, v in assets_data.items():
        if v["value"]:
            print(f"  [OK] {v['name']}: {v['value']}")

    result = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "china": china,
        "fred": fred_data,
        "assets": assets_data,
    }

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)

    file_path = os.path.join(data_dir, "all_indicators.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n[Saved] {file_path}")

    # Git push
    try:
        subprocess.run(["git", "add", "data/all_indicators.json"], cwd=project_root, check=True, shell=True)
        subprocess.run(
            ["git", "commit", "-m", f"Update macro data {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
            cwd=project_root, check=True, shell=True
        )
        subprocess.run(["git", "push"], cwd=project_root, check=True, shell=True)
        print("[Pushed] to GitHub")
    except subprocess.CalledProcessError as e:
        print(f"[Git Error] {e}")
        print("Tip: Make sure git remote and SSH key are configured")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()