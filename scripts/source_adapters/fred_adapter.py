"""
FRED 适配器 — 美联储经济数据
"""

import os
import requests

from . import SourceAdapter, SourceResult


FRED_MULTIPLIERS = {
    "PCEPILFE": 0.01,
    "CPIAUCSL": 0.01,
    "BAMLH0A0HYM2": 100,
}

FRED_SERIES = {
    "spx": "SP500",
    "vix": "VIXCLS",
    "move_idx": "MOVE",
    "us_10y_yield": "DGS10",
    "us_2y_yield": "DGS2",
    "us_core_pce_yy": "PCEPILFE",
    "us_cpi_yy": "CPIAUCSL",
    "us_ism_pmi": "NAPMPMI",
    "fed_balance_sheet": "WALCL",
    "on_rrp_balance": "RRPONTSYD",
    "fed_funds_rate": "FEDFUNDS",
    "dxy_idx": "DTWEXBGS",
    "hy_spread_oas": "BAMLH0A0HYM2",
    "ted_spread": "TEDRATE",
    "btc_usd": "CBBTCUSD",
    "gold_spot_fred": "GOLDAMGBD228NLBM",
    "wti_oil_fred": "DCOILWTICO",
    "usd_cnh_fred": "DEXCHUS",
}


def fetch_fred_series(series_id: str, api_key: str = "") -> SourceResult:
    if not api_key:
        api_key = os.getenv("FRED_API_KEY", "")

    if not api_key:
        return SourceResult(value=None, source="FRED", date=None, quality="fallback", error="FRED_API_KEY not set")

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if "error" in data:
            return SourceResult(value=None, source="FRED", date=None, quality="fallback", error=data.get("error", "unknown"))
        if "observations" not in data or not data["observations"]:
            return SourceResult(value=None, source="FRED", date=None, quality="fallback", error="no observations")

        obs = data["observations"][0]
        val_str = obs["value"]
        if val_str == "." or val_str is None:
            return SourceResult(value=None, source="FRED", date=obs["date"], quality="fallback", error="null value")

        val = float(val_str)
        if series_id in FRED_MULTIPLIERS:
            val = val * FRED_MULTIPLIERS[series_id]

        return SourceResult(value=val, source="FRED", date=obs["date"], quality="live")
    except Exception as e:
        return SourceResult(value=None, source="FRED", date=None, quality="fallback", error=str(e))


class FredAdapter(SourceAdapter):
    name = "FRED"

    def fetch(self, symbol: str) -> SourceResult:
        return fetch_fred_series(symbol, os.getenv("FRED_API_KEY", ""))

    def fetch_all(self) -> dict[str, SourceResult]:
        return super().fetch_all(FRED_SERIES)


def fetch_all_fred() -> dict[str, SourceResult]:
    return FredAdapter().fetch_all()
