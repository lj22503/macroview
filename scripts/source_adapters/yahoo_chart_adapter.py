"""Yahoo Chart API 直连适配器（yfinance 库被 429 后的裸 HTTP 兜底）

yfinance 库直连 Yahoo Finance 已被限流（HTTP 429），本适配器直接调用
Yahoo Chart JSON API（query1.finance.yahoo.com），用于补充：
- nk225 (^N225)
- move_idx (^MOVE)
这两个指标在 FRED/AKShare 均无数据源。
"""

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from . import SourceResult

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

SYMBOLS = {
    "nk225": "^N225",
    "move_idx": "^MOVE",
}


def _fetch_chart(symbol: str, timeout: float = 12.0):
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{urllib.parse.quote(symbol)}?range=5d&interval=1d"
    )
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8", "replace"))
    result = data.get("chart", {}).get("result") or []
    if not result:
        return None
    r = result[0]
    meta = r.get("meta", {})
    price = meta.get("regularMarketPrice")
    if price is None:
        closes = [
            c
            for c in (r.get("indicators", {}).get("quote", [{}])[0].get("close") or [])
            if c is not None
        ]
        price = closes[-1] if closes else None
    return float(price) if price is not None else None


def fetch_yahoo_assets() -> dict[str, SourceResult]:
    out = {}
    for key, symbol in SYMBOLS.items():
        try:
            price = _fetch_chart(symbol)
            out[key] = SourceResult(
                value=price,
                source="YahooChart",
                date=datetime.now(timezone.utc).date().isoformat(),
                quality="live" if price is not None else "fallback",
                error=None if price is not None else "chart api empty",
            )
        except Exception as e:  # noqa: BLE001
            out[key] = SourceResult(
                value=None,
                source="YahooChart",
                date=None,
                quality="fallback",
                error=f"chart api error: {e}",
            )
        time.sleep(0.3)
    return out
