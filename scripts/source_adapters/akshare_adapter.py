"""
AKShare 适配器 — 在岸中国数据（本地专用，CI 不可用）
"""

import warnings
warnings.filterwarnings('ignore')

from datetime import date
from . import SourceAdapter, SourceResult


def _try_get(df, index=0, col=None):
    if df is None or df.empty:
        return None
    try:
        if col:
            val = df.iloc[index][col]
        else:
            val = df.iloc[index]
        if hasattr(val, 'iloc'):
            val = val.iloc[0]
        return float(val) if val is not None else None
    except:
        return None


class AkshareAdapter(SourceAdapter):
    name = "AKShare"

    def fetch(self, symbol: str) -> SourceResult:
        method_name = f"_fetch_{symbol}"
        method = getattr(self, method_name, None)
        if method is None:
            return SourceResult(value=None, source="AKShare", date=None, quality="fallback", error=f"no handler for {symbol}")
        return method()

    def _fetch_hs300(self) -> SourceResult:
        try:
            import akshare as ak
            df = ak.stock_zh_index_daily(symbol='sh000300')
            if df is None or df.empty:
                return SourceResult(value=None, source="AKShare", date=None, quality="fallback", error="no data")
            close = _try_get(df, -1, 'close')
            latest = str(df.iloc[-1]['date']) if 'date' in df.columns else str(date.today())
            return SourceResult(value=close, source="AKShare", date=latest, quality="live")
        except Exception as e:
            return SourceResult(value=None, source="AKShare", date=None, quality="fallback", error=str(e))

    def _fetch_hsi(self) -> SourceResult:
        try:
            import akshare as ak
            df = ak.stock_hk_daily(symbol='HSI', adjust='qfq')
            if df is None or df.empty:
                return SourceResult(value=None, source="AKShare", date=None, quality="fallback", error="no data")
            close = _try_get(df, -1, 'close')
            latest = str(df.iloc[-1]['date']) if 'date' in df.columns else str(date.today())
            return SourceResult(value=close, source="AKShare", date=latest, quality="live")
        except Exception as e:
            return SourceResult(value=None, source="AKShare", date=None, quality="fallback", error=str(e))

    def _fetch_usd_cnh_ak(self) -> SourceResult:
        try:
            import akshare as ak
            df = ak.currency_zh_forex_sina(symbol='USDCNH', adjust='qfq')
            if df is None or df.empty:
                return SourceResult(value=None, source="AKShare", date=None, quality="fallback", error="no data")
            close = _try_get(df, -1, 'close')
            latest = str(df.iloc[-1]['date']) if 'date' in df.columns else str(date.today())
            return SourceResult(value=close, source="AKShare", date=latest, quality="live")
        except Exception as e:
            return SourceResult(value=None, source="AKShare", date=None, quality="fallback", error=str(e))

    def _fetch_nk225(self) -> SourceResult:
        try:
            import akshare as ak
            df = ak.stock_jp_daily(symbol='nikkei')
            if df is None or df.empty:
                return SourceResult(value=None, source="AKShare", date=None, quality="fallback", error="no data")
            close = _try_get(df, -1, 'close')
            latest = str(df.iloc[-1]['date']) if 'date' in df.columns else str(date.today())
            return SourceResult(value=close, source="AKShare", date=latest, quality="live")
        except Exception as e:
            return SourceResult(value=None, source="AKShare", date=None, quality="fallback", error=str(e))

    def fetch_all(self) -> dict[str, SourceResult]:
        symbols = {"hs300": "hs300", "hsi": "hsi", "usd_cnh_ak": "usd_cnh_ak", "nk225_ak": "nk225"}
        results = {}
        for key, symbol in symbols.items():
            results[key] = self.fetch(symbol)
        return results


def fetch_all_akshare() -> dict[str, SourceResult]:
    return AkshareAdapter().fetch_all()
