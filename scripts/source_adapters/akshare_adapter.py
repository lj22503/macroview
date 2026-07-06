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
            df = ak.fx_spot_quote()
            if df is None or df.empty:
                return SourceResult(value=None, source="AKShare", date=None, quality="fallback", error="no data")
            row = df[df['货币对'] == 'USD/CNY']
            if row.empty:
                return SourceResult(value=None, source="AKShare", date=None, quality="fallback", error="USD/CNY not found")
            # Use mid price
            bid = float(row.iloc[0]['买报价'])
            ask = float(row.iloc[0]['卖报价'])
            mid = round((bid + ask) / 2, 4)
            return SourceResult(value=mid, source="AKShare", date=str(date.today()), quality="live")
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

    def _fetch_gold_spot_ak(self) -> SourceResult:
        try:
            import akshare as ak
            df = ak.spot_golden_benchmark_sge()
            if df is None or df.empty:
                return SourceResult(value=None, source="AKShare", date=None, quality="fallback", error="no data")
            latest = df.iloc[-1]
            # Price in CNY/g, convert to USD/oz: CNY/g * (31.1035 g/oz) / (USDCNY rate)
            price_cny_per_g = float(latest['早盘价']) if latest['早盘价'] > 0 else float(latest['晚盘价'])
            return SourceResult(value=price_cny_per_g, source="AKShare", date=str(latest.get('交易时间', date.today())), quality="live")
        except Exception as e:
            return SourceResult(value=None, source="AKShare", date=None, quality="fallback", error=str(e))

    def _fetch_us_ism_pmi_ak(self) -> SourceResult:
        try:
            import akshare as ak
            import pandas as pd
            df = ak.macro_usa_ism_pmi()
            if df is None or df.empty:
                return SourceResult(value=None, source="AKShare", date=None, quality="fallback", error="no data")
            latest = df.iloc[-1]
            val = float(latest['今值'])
            dt = str(latest['日期'])
            return SourceResult(value=val, source="AKShare", date=dt, quality="live")
        except Exception as e:
            return SourceResult(value=None, source="AKShare", date=None, quality="fallback", error=str(e))

    def fetch_all(self) -> dict[str, SourceResult]:
        symbols = {
            "hs300": "hs300", "hsi": "hsi",
            "usd_cnh_ak": "usd_cnh_ak", "nk225_ak": "nk225",
            "gold_spot_ak": "gold_spot_ak",
            "us_ism_pmi_ak": "us_ism_pmi_ak",
        }
        results = {}
        for key, symbol in symbols.items():
            results[key] = self.fetch(symbol)
        return results


def fetch_all_akshare() -> dict[str, SourceResult]:
    return AkshareAdapter().fetch_all()
