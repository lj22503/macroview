"""
yfinance 适配器 — 全球资产数据
"""

import time
from . import SourceAdapter, SourceResult


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


def fetch_yfinance(symbol: str, retries: int = 3) -> SourceResult:
    try:
        import yfinance as yf
    except ImportError:
        return SourceResult(value=None, source="yfinance", date=None, quality="fallback", error="yfinance not installed")

    for attempt in range(retries):
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if hist.empty:
                if attempt < retries - 1:
                    time.sleep(3)
                    continue
                return SourceResult(value=None, source="yfinance", date=None, quality="fallback", error="history empty")

            price = float(hist["Close"].dropna().iloc[-1])
            dates = hist["Close"].dropna().index
            latest_date = dates[-1].strftime("%Y-%m-%d") if len(dates) > 0 else None
            return SourceResult(value=price, source="yfinance", date=latest_date, quality="live")
        except Exception as e:
            err_str = str(e)
            if "YFRateLimitError" in err_str or "rate limit" in err_str.lower():
                if attempt < retries - 1:
                    time.sleep(5)
                    continue
                return SourceResult(value=None, source="yfinance", date=None, quality="fallback", error=f"rate limited: {err_str}")
            if attempt < retries - 1:
                time.sleep(3)
                continue
            return SourceResult(value=None, source="yfinance", date=None, quality="fallback", error=err_str)

    return SourceResult(value=None, source="yfinance", date=None, quality="fallback", error="max retries")


class YfinanceAdapter(SourceAdapter):
    name = "yfinance"

    def fetch(self, symbol: str) -> SourceResult:
        return fetch_yfinance(symbol)

    def fetch_all(self) -> dict[str, SourceResult]:
        return super().fetch_all(YF_SYMBOLS)


def fetch_all_yfinance() -> dict[str, SourceResult]:
    return YfinanceAdapter().fetch_all()
