"""
多源数据合并器
"""

from source_adapters import SourceResult

FALLBACK_CHAIN = {
    "spx": ["fred:spx", "yfinance:spx"],
    "hs300": ["yfinance:hs300", "akshare:hs300"],
    "hsi": ["yfinance:hsi", "akshare:hsi"],
    "nk225": ["yfinance:nk225", "akshare:nk225"],
    "gold_spot": ["yfinance:gold_spot", "fred:gold_spot_fred", "akshare:gold_spot_ak"],
    "wti_oil": ["yfinance:wti_oil", "fred:wti_oil_fred"],
    "usd_cnh": ["yfinance:usd_cnh", "akshare:usd_cnh_ak", "fred:usd_cnh_fred"],
    "usd_jpy": ["yfinance:usd_jpy"],
    "btc_usd": ["fred:btc_usd"],
    "vix": ["fred:vix"],
    "move_idx": ["fred:move_idx"],
    "us_10y_yield": ["fred:us_10y_yield"],
    "us_2y_yield": ["fred:us_2y_yield"],
    "us_core_pce_yy": ["fred:us_core_pce_yy"],
    "us_cpi_yy": ["fred:us_cpi_yy"],
    "us_ism_pmi": ["fred:us_ism_pmi", "akshare:us_ism_pmi_ak"],
    "fed_balance_sheet": ["fred:fed_balance_sheet"],
    "on_rrp_balance": ["fred:on_rrp_balance"],
    "fed_funds_rate": ["fred:fed_funds_rate"],
    "dxy_idx": ["fred:dxy_idx"],
    "hy_spread_oas": ["fred:hy_spread_oas"],
    "ted_spread": ["fred:ted_spread"],
}


def merge_results(
    fred_results, yf_results, ak_results
) -> dict:
    output = {}
    for field, chain in FALLBACK_CHAIN.items():
        result = _resolve_field(chain, fred_results, yf_results, ak_results)
        output[field] = {
            "value": result.value,
            "source": result.source,
            "date": result.date,
            "quality": result.quality,
        }
    return output


def _resolve_field(chain, fred, yf, ak) -> SourceResult:
    sources = {"fred": fred, "yfinance": yf, "akshare": ak}
    for source_ref in chain:
        src, key = source_ref.split(":", 1)
        result = sources.get(src, {}).get(key)
        if result and result.is_valid():
            return result
    return SourceResult(value=None, source="unavailable", date=None, quality="fallback", error="all sources failed")


def build_assets(merged) -> dict:
    assets_keys = ["spx", "hs300", "hsi", "nk225", "gold_spot", "wti_oil", "usd_cnh", "usd_jpy", "btc_usd"]
    return {k: merged[k] for k in assets_keys if k in merged}


def build_fred(merged) -> dict:
    fred_keys = [
        "vix", "move_idx", "us_10y_yield", "us_2y_yield",
        "us_core_pce_yy", "us_cpi_yy", "us_ism_pmi",
        "fed_balance_sheet", "on_rrp_balance", "fed_funds_rate",
        "dxy_idx", "hy_spread_oas", "ted_spread", "spx", "btc_usd",
    ]
    return {k: merged[k] for k in fred_keys if k in merged}
