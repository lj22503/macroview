"""
宏观仪表盘 FastAPI 后端
- FRED API 拉取美国宏观数据
- yfinance 拉取全球资产价格
- 从 GitHub Raw 读取中国宏观数据 JSON
"""

import os
import json
import sqlite3
from datetime import datetime, date
from typing import Optional

import requests
import yfinance as yf
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="宏观仪表盘 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ 配置 ============
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
GITHUB_RAW_URL = "https://raw.githubusercontent.com/{owner}/{repo}/main/data/cn_indicators.json"
GITHUB_INFO = {
    "owner": os.getenv("GITHUB_OWNER", "YOUR_GITHUB_USERNAME"),
    "repo": os.getenv("GITHUB_REPO", "macro-dashboard"),
}

DB_PATH = "data/macro.db"

# ============ 数据库初始化 ============
def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS indicators (
            id TEXT PRIMARY KEY,
            name TEXT,
            value REAL,
            unit TEXT,
            updated_at TEXT,
            source TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            symbol TEXT PRIMARY KEY,
            name TEXT,
            price REAL,
            change_pct REAL,
            updated_at TEXT,
            source TEXT
        )
    """)
    conn.commit()
    conn.close()

# ============ 辅助函数 ============
def fetch_fred(series_id: str) -> Optional[float]:
    """从 FRED 获取单个指标最新值"""
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
            return float(data["observations"][0]["value"])
    except Exception as e:
        print(f"FRED fetch error for {series_id}: {e}")
    return None

def fetch_yfinance(symbol: str) -> Optional[dict]:
    """从 yfinance 获取资产价格"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        price = info.get("last_price") or info.get("previous_close")
        if price:
            return {
                "price": round(price, 2),
                "currency": str(info.get("currency", "USD")),
            }
    except Exception as e:
        print(f"yfinance fetch error for {symbol}: {e}")
    return None

def fetch_cn_data_from_github() -> dict:
    """从 GitHub Raw 获取中国宏观数据"""
    url = GITHUB_RAW_URL.format(**GITHUB_INFO)
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"GitHub fetch error: {e}")
    return {}

def save_to_db(indicator_id: str, name: str, value: float, unit: str, source: str):
    """保存指标到数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO indicators (id, name, value, unit, updated_at, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (indicator_id, name, value, unit, datetime.now().isoformat(), source))
    conn.commit()
    conn.close()

# ============ API 端点 ============

@app.get("/api/v1/overview")
def get_overview():
    """顶层概览：RISK ON/OFF + 核心指标"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    indicators = {}
    for row in c.execute("SELECT id, value FROM indicators"):
        indicators[row[0]] = row[1]
    conn.close()

    vix = indicators.get("VIXCLS")
    cn_us_spread = indicators.get("CN_US_SPREAD", 0)
    risk_score = 50
    if vix and vix < 20:
        risk_score += 20
    if cn_us_spread and cn_us_spread > -200:
        risk_score += 15

    if risk_score >= 70:
        risk_status = "RISK ON"
    elif risk_score <= 40:
        risk_status = "RISK OFF"
    else:
        risk_status = "NEUTRAL"

    return {
        "risk_status": risk_status,
        "confidence": min(95, max(30, risk_score)),
        "primary_drivers": "VIX + 中美利差",
        "updated_at": datetime.now().isoformat(),
        "indicators": indicators,
    }

@app.get("/api/v1/china")
def get_china():
    """中国宏观数据（从 GitHub 读取）"""
    data = fetch_cn_data_from_github()
    return data

@app.get("/api/v1/global")
def get_global():
    """全球宏观数据（从 FRED 读取）"""
    global_data = {
        "vix": {"value": fetch_fred("VIXCLS"), "name": "VIX恐慌指数", "unit": "", "source": "FRED"},
        "dgs10": {"value": fetch_fred("DGS10"), "name": "10Y美债收益率", "unit": "%", "source": "FRED"},
        "dgs2": {"value": fetch_fred("DGS2"), "name": "2Y美债收益率", "unit": "%", "source": "FRED"},
        "pce": {"value": fetch_fred("PCEPILFE"), "name": "核心PCE", "unit": "%", "source": "FRED"},
        "ism": {"value": fetch_fred("ISMINDUS"), "name": "ISM制造业PMI", "unit": "", "source": "FRED"},
        "dxy": {"value": fetch_fred("DTWEXBGS"), "name": "DXY美元指数", "unit": "", "source": "FRED"},
        "walcl": {"value": fetch_fred("WALCL"), "name": "美联储资产负债表", "unit": "万亿USD", "source": "FRED"},
        "baml": {"value": fetch_fred("BAMLM0A0CM"), "name": "高收益债利差", "unit": "bp", "source": "FRED"},
    }
    return {"data": global_data, "updated_at": datetime.now().isoformat()}

@app.get("/api/v1/assets")
def get_assets():
    """全球资产价格（从 yfinance 读取）"""
    assets = {
        "sp500": {"symbol": "SPY", "name": "标普500"},
        "hs300": {"symbol": "000300.SS", "name": "沪深300"},
        "gold": {"symbol": "GC=F", "name": "黄金"},
        "crude": {"symbol": "CL=F", "name": "原油"},
        "usd_cnh": {"symbol": "CNHF=X", "name": "USD/CNH"},
    }

    result = {}
    for key, asset in assets.items():
        data = fetch_yfinance(asset["symbol"])
        if data:
            result[key] = {
                **asset,
                "price": data["price"],
                "currency": data["currency"],
                "updated_at": datetime.now().isoformat(),
            }

    return {"data": result, "updated_at": datetime.now().isoformat()}

@app.get("/api/v1/risk")
def get_risk():
    """波动率与风险指标"""
    return {
        "vix": fetch_fred("VIXCLS"),
        "baml": fetch_fred("BAMLM0A0CM"),
        "updated_at": datetime.now().isoformat(),
    }

@app.get("/api/v1/health")
def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.on_event("startup")
def startup():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
