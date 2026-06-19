"""
本地宏观数据拉取脚本
同时拉取：中国数据（AKShare）+ 美国数据（FRED + yfinance）
生成 JSON → push 到 GitHub

使用方法：
  python fetch_all_data.py

依赖：
  pip install akshare requests yfinance pandas
"""

import os
import json
import subprocess
from datetime import datetime

import requests
import yfinance as yf

try:
    import akshare as ak
except ImportError:
    print("错误：请先安装 AKShare: pip install akshare")
    exit(1)


# ============ FRED API 配置 ============
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "lj22503")
GITHUB_REPO = os.getenv("GITHUB_REPO", "macroview")


# ============ FRED 数据拉取 ============
def fetch_fred(series_id: str) -> float | None:
    """从 FRED 获取单个指标最新值"""
    if not FRED_API_KEY:
        print(f"  [WARN] FRED_API_KEY 未设置，跳过 {series_id}")
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


# ============ yfinance 数据拉取 ============
def fetch_yfinance(symbol: str) -> float | None:
    """从 yfinance 获取资产价格"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        price = info.get("last_price") or info.get("previous_close")
        return round(price, 2) if price else None
    except Exception as e:
        print(f"  [ERROR] yfinance {symbol}: {e}")
    return None


# ============ AKShare 中国数据拉取 ============
def fetch_china_data():
    """使用 AKShare 拉取中国宏观数据"""
    data = {}

    try:
        df = ak.realthime_china_pmi()
        if not df.empty and "value" in df.columns:
            data["pmi"] = {"value": float(df.iloc[0]["value"]), "name": "中国 PMI"}
            print("  ✓ PMI")
    except Exception as e:
        print(f"  ✗ PMI: {e}")

    try:
        df = ak.money_supply()
        if not df.empty:
            m1 = df.iloc[0].get("m1_yoy")
            m2 = df.iloc[0].get("m2_yoy")
            if m1 is not None and m2 is not None:
                data["m1m2"] = {
                    "m1_yoy": float(m1),
                    "m2_yoy": float(m2),
                    "spread": float(m2 - m1),
                    "name": "M1-M2 剪刀差",
                }
            print("  ✓ M1/M2")
    except Exception as e:
        print(f"  ✗ M1/M2: {e}")

    try:
        df = ak.loan_lpr()
        if not df.empty and "lpr_1y" in df.columns:
            val = df.iloc[0]["lpr_1y"]
            if val is not None:
                data["lpr"] = {"value": float(val), "name": "LPR (1年期)"}
            print("  ✓ LPR")
    except Exception as e:
        print(f"  ✗ LPR: {e}")

    try:
        df = ak.economic_figure(indicator="cpi")
        if not df.empty and "cpi" in df.columns:
            data["cpi"] = {"value": float(df.iloc[0]["cpi"]), "name": "CPI"}
            print("  ✓ CPI")
    except Exception as e:
        print(f"  ✗ CPI: {e}")

    try:
        df = ak.economic_figure(indicator="ppi")
        if not df.empty and "ppi" in df.columns:
            data["ppi"] = {"value": float(df.iloc[0]["ppi"]), "name": "PPI"}
            print("  ✓ PPI")
    except Exception as e:
        print(f"  ✗ PPI: {e}")

    try:
        df = ak.social_financing()
        if not df.empty and "增量" in df.columns:
            val = df.iloc[0]["增量"]
            if val is not None:
                data["social"] = {"value": float(val) / 10000, "name": "社融增量 (万亿)"}
            print("  ✓ 社融")
    except Exception as e:
        print(f"  ✗ 社融: {e}")

    return data


# ============ 主函数 ============
def main():
    print("=" * 60)
    print("开始拉取宏观数据...")
    print("=" * 60)

    # 1. 中国数据
    print("\n[中国数据 - AKShare]")
    china = fetch_china_data()

    # 2. FRED 美国宏观数据
    print("\n[美国宏观数据 - FRED]")
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
            print(f"  ✓ {v['name']}: {v['value']}")

    # 3. yfinance 资产价格
    print("\n[全球资产价格 - yfinance]")
    assets_data = {
        "sp500": {"value": fetch_yfinance("SPY"), "name": "标普500"},
        "hs300": {"value": fetch_yfinance("000300.SS"), "name": "沪深300"},
        "gold": {"value": fetch_yfinance("GC=F"), "name": "黄金"},
        "crude": {"value": fetch_yfinance("CL=F"), "name": "原油"},
        "usd_cnh": {"value": fetch_yfinance("CNHF=X"), "name": "USD/CNH"},
    }
    for k, v in assets_data.items():
        if v["value"]:
            print(f"  ✓ {v['name']}: {v['value']}")

    # 4. 合并输出
    result = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "china": china,
        "fred": fred_data,
        "assets": assets_data,
    }

    # 5. 保存并推送
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)

    file_path = os.path.join(data_dir, "all_indicators.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n✓ 数据已保存: {file_path}")

    # Git push
    try:
        subprocess.run(["git", "add", "data/all_indicators.json"], cwd=project_root, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"更新宏观数据 {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
            cwd=project_root,
            check=True,
        )
        subprocess.run(["git", "push"], cwd=project_root, check=True)
        print("✓ 已推送到 GitHub")
    except subprocess.CalledProcessError as e:
        print(f"✗ Git 操作失败: {e}")
        print("提示：请确保已配置 git remote 和 SSH key")

    print("\n" + "=" * 60)
    print("完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()