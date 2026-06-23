"""
宏观仪表盘 FastAPI 后端
- FRED API 拉取美国宏观数据
- yfinance 拉取全球资产价格
- 从 GitHub Raw 读取中国宏观数据 JSON
- 信号合成引擎计算 RISK ON/OFF
"""

import os
import json
from datetime import datetime, date
from typing import Optional, Dict, Any

import requests
import yfinance as yf
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from signal_engine import (
    calculate_risk_score,
    WEIGHTS,
    score_vix,
    score_cn_us_spread,
    score_m1_m2_spread,
    score_north_money_3d,
    score_credit_spread,
)

app = FastAPI(title="宏观仪表盘 API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ 配置 ============
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "lj22503")
GITHUB_REPO = os.getenv("GITHUB_REPO", "macroview")
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main/data"

# ============ FRED 数据获取 ============
FRED_SERIES = {
    # 全球风险
    "vix": "VIXCLS",
    "move_idx": "MOVE",
    # 美债与利率
    "us_10y_yield": "DGS10",
    "us_2y_yield": "DGS2",
    # 美国宏观
    "us_core_pce_yy": "PCEPILFE",
    "us_cpi_yy": "CPIAUCSL",
    "us_ism_pmi": "ISMINDUS",
    # 美联储
    "fed_balance_sheet": "WALCL",
    "on_rrp_balance": "RRPONTSYD",
    "fed_funds_rate": "FEDFUNDS",
    # 汇率与美元
    "dxy_idx": "DTWEXBGS",
    # 信用利差
    "hy_spread_oas": "BAMLH0A0HYM2",
    "ted_spread": "TEDRATE",
    # 资产价格
    "spx": "SP500",
    "btc_usd": "CBBTCUSD",
}

def fetch_fred(series_id: str) -> Optional[float]:
    """从 FRED 获取单个指标最新值"""
    if not FRED_API_KEY:
        return None
    url = "https://api.stlouisfed.org/fred/series/observations"
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
        if "error" not in data and "observations" in data and data["observations"]:
            val = data["observations"][0]["value"]
            return float(val) if val != "." else None
    except Exception as e:
        print(f"FRED fetch error for {series_id}: {e}")
    return None

def fetch_fred_series(series_id: str, days: int = 30) -> list:
    """获取历史数据"""
    if not FRED_API_KEY:
        return []
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": days,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if "error" not in data and "observations" in data:
            return [
                {"date": obs["date"], "value": float(obs["value"]) if obs["value"] != "." else None}
                for obs in reversed(data["observations"])
            ]
    except Exception as e:
        print(f"FRED history error for {series_id}: {e}")
    return []

# ============ yfinance 数据获取 ============
YF_SYMBOLS = {
    "spx": "SPY",
    "hs300": "000300.SS",
    "hsi": "^HSI",
    "nk225": "^N225",
    "gold_spot": "GC=F",
    "wti_oil": "CL=F",
    "usd_cnh": "CNHF=X",
    "usd_jpy": "JPY=X",
}

def fetch_akshare(key: str) -> Optional[dict]:
    """
    用 akshare 备援获取资产价格（yfinance 失败时调用）
    仅覆盖已验证可用的资产：沪深300、恒生指数
    """
    try:
        import akshare as ak
    except ImportError:
        return None

    try:
        if key == "hs300":
            df = ak.stock_zh_index_daily(symbol="sh000300")
            if not df.empty:
                row = df.iloc[-1]
                return {"price": round(float(row["close"]), 2), "currency": "CNY"}
        elif key == "hsi":
            df = ak.stock_hk_index_daily_sina(symbol="HSI")
            if not df.empty:
                row = df.iloc[-1]
                return {"price": round(float(row["close"]), 2), "currency": "HKD"}
    except Exception as e:
        print(f"akshare fallback error for {key}: {e}")
    return None


def fetch_yfinance(symbol: str) -> Optional[dict]:
    """从 yfinance 获取资产价格"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        price = info.get("last_price") or info.get("previous_close")
        currency = str(info.get("currency", "USD"))
        return {"price": round(price, 2), "currency": currency} if price else None
    except Exception as e:
        print(f"yfinance fetch error for {symbol}: {e}")
    return None

# ============ GitHub 中国数据获取 ============
def fetch_china_data() -> dict:
    """从 GitHub Raw 获取中国宏观数据"""
    url = f"{GITHUB_RAW_BASE}/all_indicators.json"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"GitHub fetch error: {e}")
    return {}

# ============ 信号合成 ============
def get_trend(current: float, history: list, threshold_pct: float = 2.0) -> str:
    """计算趋势（基于近30日数据）"""
    if not history or len(history) < 5:
        return "持平"
    values = [h["value"] for h in history if h.get("value") is not None]
    if len(values) < 5:
        return "持平"
    avg_past = sum(values[:10]) / min(10, len(values))
    if not avg_past:
        return "持平"
    change_pct = (current - avg_past) / abs(avg_past) * 100
    if change_pct > threshold_pct:
        return "收窄" if threshold_pct > 0 else "走阔"
    elif change_pct < -threshold_pct:
        return "走阔" if threshold_pct > 0 else "收窄"
    return "持平"

# ============ API 端点 ============

@app.get("/api/v1/dashboard")
def get_dashboard():
    """
    统一全景接口
    返回完整仪表盘数据：overview + 各模块数据
    """
    now = datetime.now()

    # 获取中国数据
    china_data = fetch_china_data()

    # 获取 FRED 数据
    fred_data = {}
    for key, series_id in FRED_SERIES.items():
        fred_data[key] = fetch_fred(series_id)

    # 获取 yfinance 数据（失败则用 akshare 备援）
    assets_data = {}
    for key, symbol in YF_SYMBOLS.items():
        yf_data = fetch_yfinance(symbol)
        if yf_data is not None:
            assets_data[key] = yf_data
        else:
            akshare_data = fetch_akshare(key)
            if akshare_data is not None:
                assets_data[key] = akshare_data
            else:
                assets_data[key] = None

    # ===== 信号合成 =====
    # 中美利差计算
    cn_10y = china_data.get("china", {}).get("cn_10y_yield")  # 需要从中国数据获取
    us_10y = fred_data.get("us_10y_yield")
    cn_us_spread = None
    if cn_10y and us_10y:
        cn_us_spread = (cn_10y - us_10y) * 100  # 转为 bp

    # 获取利差历史用于计算趋势
    spread_history = fetch_fred_series("DGS10", 30)  # 简化：只用美债历史

    # 各因子值
    vix = fred_data.get("vix")
    credit_spread = fred_data.get("hy_spread_oas")
    north_money_3d = china_data.get("china", {}).get("north_money_3d")

    # 计算风险评分
    score_result = calculate_risk_score(
        cn_us_spread=cn_us_spread,
        cn_us_spread_trend=get_trend(us_10y or 0, spread_history) if us_10y else "持平",
        m1_m2_spread=china_data.get("china", {}).get("m1_m2_spread", {}).get("spread"),
        m1_m2_spread_trend=china_data.get("china", {}).get("m1_m2_spread", {}).get("trend", "持平"),
        vix=vix,
        north_money_3d=north_money_3d,
        credit_spread=credit_spread,
    )

    # 组装 factor_details（用于展示）
    factor_details_out = {}
    for f in score_result.factor_details:
        factor_details_out[f.name] = {
            "signal": f.signal,
            "weight": f.weight,
            "contribution": round(f.contribution, 3),
            "view": f.view,
            "narrative": f.narrative,
            "trend": f.trend,
        }

    # ===== 构建响应 =====
    return {
        "meta": {
            "updated_at": now.isoformat(),
            "data_date": (now.date()).isoformat(),
            "status": "success" if score_result.confidence > 30 else "degraded",
        },
        "overview": {
            "bias": score_result.bias,
            "confidence": score_result.confidence,
            "score": score_result.score,
            "label": score_result.label,
            "primary_driver": score_result.primary_driver,
            "suggestions": score_result.suggestions,
            "narrative": score_result.narrative,
            "factor_details": factor_details_out,
        },
        "china_core": china_data.get("china", {}),
        "global_macro": {
            "us_ism_pmi": {"value": fred_data.get("us_ism_pmi"), "unit": "", "name": "美国ISM制造业PMI"},
            "us_core_pce_yy": {"value": fred_data.get("us_core_pce_yy"), "unit": "%", "name": "美国核心PCE同比"},
            "fed_balance_sheet": {"value": fred_data.get("fed_balance_sheet"), "unit": "万亿USD", "name": "美联储资产负债表"},
            "on_rrp_balance": {"value": fred_data.get("on_rrp_balance"), "unit": "万亿USD", "name": "ON RRP隔夜逆回购"},
        },
        "fx_liquidity": {
            "dxy_idx": {"value": fred_data.get("dxy_idx"), "unit": "", "name": "DXY美元指数"},
            "cn_us_10y_spread": {"value": cn_us_spread, "unit": "bp", "name": "中美利差(10Y)"},
            "usd_cnh": {"value": assets_data.get("usd_cnh", {}).get("price") if assets_data.get("usd_cnh") else None, "unit": "", "name": "USD/CNH"},
            "usd_jpy": {"value": assets_data.get("usd_jpy", {}).get("price") if assets_data.get("usd_jpy") else None, "unit": "", "name": "USD/JPY"},
        },
        "assets": {
            "spx": {"value": assets_data.get("spx", {}).get("price") if assets_data.get("spx") else None, "unit": "", "name": "标普500"},
            "hs300": {"value": assets_data.get("hs300", {}).get("price") if assets_data.get("hs300") else None, "unit": "", "name": "沪深300"},
            "gold_spot": {"value": assets_data.get("gold_spot", {}).get("price") if assets_data.get("gold_spot") else None, "unit": "USD", "name": "黄金现货"},
            "wti_oil": {"value": assets_data.get("wti_oil", {}).get("price") if assets_data.get("wti_oil") else None, "unit": "USD", "name": "WTI原油"},
            "us_10y_yield": {"value": fred_data.get("us_10y_yield"), "unit": "%", "name": "10Y美债收益率"},
        },
        "risk_monitor": {
            "vix": {"value": vix, "unit": "", "name": "VIX恐慌指数"},
            "move_idx": {"value": fred_data.get("move_idx"), "unit": "", "name": "MOVE债券波动率"},
            "hy_spread_oas": {"value": credit_spread, "unit": "bp", "name": "高收益债利差(OAS)"},
            "cn_vix": {"value": china_data.get("china", {}).get("cn_vix"), "unit": "", "name": "A股隐含波动率"},
        },
    }


@app.get("/api/v1/overview")
def get_overview():
    """顶层概览：RISK ON/OFF + 核心信号"""
    dashboard = get_dashboard()
    return dashboard["overview"]


@app.get("/api/v1/china-core")
def get_china_core():
    """中国内核数据"""
    china_data = fetch_china_data()
    return china_data.get("china", {})


@app.get("/api/v1/global-macro")
def get_global_macro():
    """全球宏观数据"""
    return {
        "us_ism_pmi": {"value": fetch_fred("ISMINDUS"), "unit": "", "name": "美国ISM制造业PMI"},
        "us_core_pce_yy": {"value": fetch_fred("PCEPILFE"), "unit": "%", "name": "美国核心PCE同比"},
        "fed_balance_sheet": {"value": fetch_fred("WALCL"), "unit": "万亿USD", "name": "美联储资产负债表"},
        "on_rrp_balance": {"value": fetch_fred("RRPONTSYD"), "unit": "万亿USD", "name": "ON RRP隔夜逆回购"},
        "us_10y_yield": {"value": fetch_fred("DGS10"), "unit": "%", "name": "10Y美债收益率"},
        "us_2y_yield": {"value": fetch_fred("DGS2"), "unit": "%", "name": "2Y美债收益率"},
    }


@app.get("/api/v1/fx-liquidity")
def get_fx_liquidity():
    """汇率与流动性"""
    china_data = fetch_china_data()
    cn_10y = china_data.get("china", {}).get("cn_10y_yield")
    us_10y = fetch_fred("DGS10")
    cn_us_spread = (cn_10y - us_10y) * 100 if cn_10y and us_10y else None

    return {
        "dxy_idx": {"value": fetch_fred("DTWEXBGS"), "unit": "", "name": "DXY美元指数"},
        "cn_us_10y_spread": {"value": cn_us_spread, "unit": "bp", "name": "中美利差(10Y)"},
        "usd_cnh": {"value": fetch_yfinance("CNHF=X", {}).get("price") if fetch_yfinance("CNHF=X") else None, "unit": "", "name": "USD/CNH"},
        "usd_jpy": {"value": fetch_yfinance("JPY=X", {}).get("price") if fetch_yfinance("JPY=X") else None, "unit": "", "name": "USD/JPY"},
    }


@app.get("/api/v1/assets")
def get_assets():
    """全球核心资产行情"""
    assets = {}
    for key, symbol in YF_SYMBOLS.items():
        yf_data = fetch_yfinance(symbol)
        if yf_data:
            assets[key] = {"value": yf_data["price"], "currency": yf_data["currency"]}
        else:
            akshare_data = fetch_akshare(key)
            if akshare_data:
                assets[key] = {"value": akshare_data["price"], "currency": akshare_data["currency"]}

    # 美债收益率单独从 FRED 获取
    assets["us_10y_yield"] = {"value": fetch_fred("DGS10"), "unit": "%"}

    return assets


@app.get("/api/v1/risk")
def get_risk():
    """波动率与风险指标"""
    return {
        "vix": {"value": fetch_fred("VIXCLS"), "unit": "", "name": "VIX恐慌指数"},
        "move_idx": {"value": fetch_fred("MOVE"), "unit": "", "name": "MOVE债券波动率"},
        "hy_spread_oas": {"value": fetch_fred("BAMLH0A0HYM2"), "unit": "bp", "name": "高收益债利差(OAS)"},
        "ted_spread": {"value": fetch_fred("TEDRATE"), "unit": "bp", "name": "TED利差"},
    }


@app.get("/api/v1/vix-history")
def get_vix_history(days: int = 30):
    """VIX 历史数据"""
    history = fetch_fred_series("VIXCLS", days)
    return {"data": history}


@app.get("/api/v1/health")
def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "fred_connected": bool(FRED_API_KEY),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
