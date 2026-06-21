"""
每日数据拉取脚本
- 拉取 FRED + AKShare + yfinance 数据
- 计算信号合成
- 生成 JSON 推送到 GitHub
"""

import os
import json
from datetime import datetime, date
from pathlib import Path

# 需要的依赖：pip install requests yfinance akshare pandas
import requests
import yfinance as yf
import pandas as pd

# ============ 配置 ============
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")  # GitHub Personal Access Token
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "lj22503")
GITHUB_REPO = os.getenv("GITHUB_REPO", "macroview")
GITHUB_BRANCH = "main"

# 拉取脚本目录
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
OUTPUT_FILE = DATA_DIR / "all_indicators.json"

# ============ FRED 数据 ============
FRED_SERIES = {
    "vix": "VIXCLS",
    "move_idx": "MOVE",
    "us_10y_yield": "DGS10",
    "us_2y_yield": "DGS2",
    "us_core_pce_yy": "PCEPILFE",
    "us_cpi_yy": "CPIAUCSL",
    "us_ism_pmi": "ISMINDUS",
    "fed_balance_sheet": "WALCL",
    "on_rrp_balance": "RRPONTSYD",
    "fed_funds_rate": "FEDFUNDS",
    "dxy_idx": "DTWEXBGS",
    "hy_spread_oas": "BAMLH0A0HYM2",
    "ted_spread": "TEDRATE",
    "spx": "SP500",
    "btc_usd": "CBBTCUSD",
}

def fetch_fred(series_id: str) -> tuple:
    """从 FRED 获取最新值和日期"""
    if not FRED_API_KEY:
        print(f"  [WARN] FRED_API_KEY 未设置，跳过 {series_id}")
        return None, None

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
            obs = data["observations"][0]
            val = float(obs["value"]) if obs["value"] != "." else None
            return val, obs["date"]
    except Exception as e:
        print(f"  [ERROR] FRED {series_id}: {e}")
    return None, None

def fetch_fred_all() -> dict:
    """拉取所有 FRED 数据"""
    print("\n[1/4] 拉取 FRED 数据...")
    result = {}
    for key, series_id in FRED_SERIES.items():
        val, obs_date = fetch_fred(series_id)
        result[key] = {
            "value": val,
            "date": obs_date,
            "name": key,
            "source": "FRED"
        }
        print(f"  {key}: {val} ({obs_date})")
    return result

# ============ yfinance 数据 ============
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

def fetch_yfinance(symbol: str) -> tuple:
    """获取 yfinance 数据"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        price = info.get("last_price") or info.get("previous_close")
        currency = str(info.get("currency", "USD"))
        return round(price, 2) if price else None, currency
    except Exception as e:
        print(f"  [ERROR] yfinance {symbol}: {e}")
        return None, "USD"

def fetch_yfinance_all() -> dict:
    """拉取所有 yfinance 数据"""
    print("\n[2/4] 拉取 yfinance 数据...")
    result = {}
    for key, symbol in YF_SYMBOLS.items():
        price, currency = fetch_yfinance(symbol)
        result[key] = {
            "value": price,
            "currency": currency,
            "source": "yfinance"
        }
        print(f"  {key}: {price} ({currency})")
    return result

# ============ AKShare 中国数据 ============
def fetch_china_akshare() -> dict:
    """拉取 AKShare 中国数据"""
    print("\n[3/4] 拉取 AKShare 中国数据...")

    # 检查 akshare 是否安装
    try:
        import akshare as ak
    except ImportError:
        print("  [WARN] akshare 未安装，跳过中国数据")
        return {
            "cn_pmi_official": {"value": None, "name": "官方制造业PMI", "source": "AKShare"},
            "cn_pmi_caixin": {"value": None, "name": "财新制造业PMI", "source": "AKShare"},
            "cn_cpi_yy": {"value": None, "name": "CPI同比", "source": "AKShare"},
            "cn_ppi_yy": {"value": None, "name": "PPI同比", "source": "AKShare"},
            "cn_social_financing": {"value": None, "name": "社融存量同比", "source": "AKShare"},
            "cn_m1_m2_spread": {"value": None, "name": "M1-M2剪刀差", "source": "AKShare"},
            "cn_lpr_1y": {"value": None, "name": "1年期LPR", "source": "AKShare"},
            "cn_10y_yield": {"value": None, "name": "10Y中债收益率", "source": "AKShare"},
            "north_money_3d": {"value": None, "name": "北向资金3日累计", "source": "AKShare"},
            "north_money": {"value": None, "name": "北向资金当日", "source": "AKShare"},
        }

    result = {}

    # PMI
    try:
        df = ak.macro_china_pmi()
        if df is not None and len(df) > 0:
            result["cn_pmi_official"] = {"value": float(df.iloc[0]["official"]), "name": "官方制造业PMI", "source": "AKShare"}
            result["cn_pmi_caixin"] = {"value": float(df.iloc[0]["caixin"]), "name": "财新制造业PMI", "source": "AKShare"}
            print(f"  cn_pmi_official: {result['cn_pmi_official']['value']}")
            print(f"  cn_pmi_caixin: {result['cn_pmi_caixin']['value']}")
    except Exception as e:
        print(f"  [ERROR] PMI: {e}")
        result["cn_pmi_official"] = {"value": None, "name": "官方制造业PMI", "source": "AKShare"}
        result["cn_pmi_caixin"] = {"value": None, "name": "财新制造业PMI", "source": "AKShare"}

    # CPI/PPI
    try:
        df = ak.macro_china_cpi()
        if df is not None and len(df) > 0:
            result["cn_cpi_yy"] = {"value": float(df.iloc[0]["cpi_yoy"]), "name": "CPI同比", "source": "AKShare"}
            print(f"  cn_cpi_yy: {result['cn_cpi_yy']['value']}")
    except Exception as e:
        print(f"  [ERROR] CPI: {e}")
        result["cn_cpi_yy"] = {"value": None, "name": "CPI同比", "source": "AKShare"}

    try:
        df = ak.macro_china_ppi()
        if df is not None and len(df) > 0:
            result["cn_ppi_yy"] = {"value": float(df.iloc[0]["ppi_yoy"]), "name": "PPI同比", "source": "AKShare"}
            print(f"  cn_ppi_yy: {result['cn_ppi_yy']['value']}")
    except Exception as e:
        print(f"  [ERROR] PPI: {e}")
        result["cn_ppi_yy"] = {"value": None, "name": "PPI同比", "source": "AKShare"}

    # M1/M2
    try:
        df = ak.macro_china_money_supply()
        if df is not None and len(df) > 0:
            m1 = float(df.iloc[0]["m1_yoy"])
            m2 = float(df.iloc[0]["m2_yoy"])
            spread = m1 - m2
            result["cn_m1_m2_spread"] = {
                "value": spread,
                "m1_yoy": m1,
                "m2_yoy": m2,
                "spread": spread,
                "trend": "收窄" if spread > 0 or spread > -3 else "持平",
                "name": "M1-M2剪刀差",
                "source": "AKShare"
            }
            print(f"  cn_m1_m2_spread: {spread}% (M1={m1}%, M2={m2}%)")
    except Exception as e:
        print(f"  [ERROR] M1/M2: {e}")
        result["cn_m1_m2_spread"] = {"value": None, "name": "M1-M2剪刀差", "source": "AKShare"}

    # LPR
    try:
        df = ak.macro_china_lpr()
        if df is not None and len(df) > 0:
            result["cn_lpr_1y"] = {"value": float(df.iloc[0]["lpr_1y"]), "name": "1年期LPR", "source": "AKShare"}
            print(f"  cn_lpr_1y: {result['cn_lpr_1y']['value']}")
    except Exception as e:
        print(f"  [ERROR] LPR: {e}")
        result["cn_lpr_1y"] = {"value": None, "name": "1年期LPR", "source": "AKShare"}

    # 社融
    try:
        df = ak.macro_china_shrzgm()
        if df is not None and len(df) > 0:
            result["cn_social_financing"] = {"value": float(df.iloc[0]["social_financing"]), "name": "社融存量同比", "source": "AKShare"}
            print(f"  cn_social_financing: {result['cn_social_financing']['value']}")
    except Exception as e:
        print(f"  [ERROR] 社融: {e}")
        result["cn_social_financing"] = {"value": None, "name": "社融存量同比", "source": "AKShare"}

    # 北向资金
    try:
        df = ak.stock_hsgt_north_net_flow_in()
        if df is not None and len(df) >= 3:
            north_3d = sum([float(df.iloc[i]["北向净流入"]) for i in range(min(3, len(df)))])
            north_today = float(df.iloc[0]["北向净流入"])
            result["north_money_3d"] = {"value": round(north_3d, 2), "name": "北向资金3日累计", "source": "AKShare"}
            result["north_money"] = {"value": round(north_today, 2), "name": "北向资金当日", "source": "AKShare"}
            print(f"  north_money_3d: {north_3d}亿")
            print(f"  north_money: {north_today}亿")
    except Exception as e:
        print(f"  [ERROR] 北向资金: {e}")
        result["north_money_3d"] = {"value": None, "name": "北向资金3日累计", "source": "AKShare"}
        result["north_money"] = {"value": None, "name": "北向资金当日", "source": "AKShare"}

    # 中债收益率
    try:
        df = ak.bond_china_yield()
        if df is not None and len(df) > 0:
            for _, row in df.iterrows():
                if "10年" in str(row.get("年限", "")):
                    result["cn_10y_yield"] = {"value": float(row["收益率"]) / 100, "name": "10Y中债收益率", "source": "AKShare"}
                    print(f"  cn_10y_yield: {result['cn_10y_yield']['value']}")
                    break
    except Exception as e:
        print(f"  [ERROR] 中债收益率: {e}")
        result["cn_10y_yield"] = {"value": None, "name": "10Y中债收益率", "source": "AKShare"}

    return result

# ============ 信号计算 ============
def calculate_signals(fred_data: dict, china_data: dict) -> dict:
    """计算信号合成"""
    print("\n[计算信号]")

    # 权重
    WEIGHTS = {
        "cn_us_spread": 0.20,
        "m1_m2_spread": 0.25,
        "vix": 0.15,
        "north_money": 0.15,
        "credit_spread": 0.25,
    }

    # 中美利差
    cn_10y = china_data.get("cn_10y_yield", {}).get("value")
    us_10y = fred_data.get("us_10y_yield", {}).get("value")
    cn_us_spread = None
    if cn_10y and us_10y:
        cn_us_spread = (cn_10y - us_10y) * 100  # bp

    # 打分函数
    def score_cn_us_spread(v):
        if v is None: return 0
        if v > -150: return 2
        if v > -200: return 1
        if v > -250: return 0
        return -1

    def score_m1_m2(v):
        if v is None: return 0
        if v > -3: return 2
        if v > -5: return 1
        if v > -8: return 0
        return -1

    def score_vix(v):
        if v is None: return 0
        if v < 14: return 2
        if v < 18: return 1
        if v < 22: return 0
        if v < 28: return -1
        return -2

    def score_north(v):
        if v is None: return 0
        if v > 100: return 2
        if v > 50: return 1
        if v > -50: return 0
        if v > -100: return -1
        return -2

    def score_credit(v):
        if v is None: return 0
        if v < 350: return 2
        if v < 450: return 1
        if v < 550: return 0
        if v < 700: return -1
        return -2

    # 各因子得分
    signals = {
        "cn_us_spread": score_cn_us_spread(cn_us_spread),
        "m1_m2_spread": score_m1_m2(china_data.get("cn_m1_m2_spread", {}).get("spread")),
        "vix": score_vix(fred_data.get("vix", {}).get("value")),
        "north_money": score_north(china_data.get("north_money_3d", {}).get("value")),
        "credit_spread": score_credit(fred_data.get("hy_spread_oas", {}).get("value")),
    }

    # 加权总分
    total_score = sum(signals[f] * WEIGHTS[f] for f in WEIGHTS)

    # 观点
    view_map = {
        "cn_us_spread": {
            2: ("资本回流中国", "人民币资产吸引力上升，外资加速配置中国"),
            1: ("利差收窄", "资本外流压力边际减弱"),
            0: ("利差稳定", "中美利差维持现状，外资观望"),
            -1: ("资本外逃风险", "美元资产回报率相对更高，外资面临汇兑损失"),
            -2: ("资本外逃加剧", "利差深度倒挂，外资加速撤离人民币资产"),
        },
        "vix": {
            2: ("过度自满", "市场对风险毫无防备，往往是大跌前兆"),
            1: ("风险偏好正常", "市场情绪健康，专注选股"),
            0: ("波动正常区间", "VIX处于历史正常区间"),
            -1: ("风险偏好下降", "恐慌情绪升温，防御为主"),
            -2: ("恐慌性抛售", "踩踏式出逃，但恐慌峰值往往对应中期底部"),
        },
    }

    factor_details = {}
    for f, w in WEIGHTS.items():
        sig = signals[f]
        view_info = view_map.get(f, {}).get(sig, ("--", "--"))
        factor_details[f] = {
            "signal": sig,
            "weight": w,
            "view": view_info[0],
            "narrative": view_info[1],
        }

    # 仓位映射
    if total_score >= 1.5:
        allocation = {"equity": 85, "bond": 10, "gold": 5, "cash": 0}
        label = "全面扩张"
    elif total_score >= 0.5:
        allocation = {"equity": 65, "bond": 25, "gold": 10, "cash": 0}
        label = "温和复苏"
    elif total_score >= -0.5:
        allocation = {"equity": 45, "bond": 35, "gold": 10, "cash": 10}
        label = "结构分化"
    elif total_score >= -1.5:
        allocation = {"equity": 25, "bond": 40, "gold": 15, "cash": 20}
        label = "收缩压力"
    else:
        allocation = {"equity": 10, "bond": 40, "gold": 20, "cash": 30}
        label = "系统性风险"

    # Bias
    if total_score > 0.3:
        bias = "RISK_ON"
    elif total_score < -0.3:
        bias = "RISK_OFF"
    else:
        bias = "NEUTRAL"

    # 主要驱动
    drivers = []
    for f in ["cn_us_spread", "m1_m2_spread", "vix", "north_money", "credit_spread"]:
        if signals[f] > 0:
            driver_names = {
                "cn_us_spread": "中美利差收窄",
                "m1_m2_spread": "M1-M2改善",
                "vix": "VIX稳定",
                "north_money": "北向资金流入",
                "credit_spread": "信用利差正常"
            }
            drivers.append(driver_names.get(f, f))
            if len(drivers) >= 3:
                break

    # 置信度
    valid_count = sum(1 for f in ["cn_us_spread", "m1_m2_spread", "vix", "north_money", "credit_spread"]
                      if (f == "cn_us_spread" and cn_us_spread is not None) or
                         (f == "m1_m2_spread" and china_data.get("cn_m1_m2_spread", {}).get("value") is not None) or
                         (f == "vix" and fred_data.get("vix", {}).get("value") is not None) or
                         (f == "north_money" and china_data.get("north_money_3d", {}).get("value") is not None) or
                         (f == "credit_spread" and fred_data.get("hy_spread_oas", {}).get("value") is not None))
    confidence = min(95, max(30, valid_count * 19))

    print(f"  总分: {total_score:.2f}")
    print(f"  状态: {bias} ({label})")
    print(f"  置信度: {confidence}%")
    print(f"  权益仓位建议: {allocation['equity']}%")

    return {
        "bias": bias,
        "confidence": confidence,
        "score": round(total_score, 2),
        "label": label,
        "primary_driver": drivers,
        "suggestions": allocation,
        "narrative": f"{'、'.join(drivers)}，{label}。",
        "factor_details": factor_details,
    }

# ============ GitHub 推送 ============
def push_to_github(data: dict):
    """推送数据到 GitHub"""
    print("\n[4/4] 推送到 GitHub...")

    if not GITHUB_TOKEN:
        print("  [WARN] GITHUB_TOKEN 未设置，保存到本地文件")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  已保存到: {OUTPUT_FILE}")
        return

    import base64

    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/data/all_indicators.json"

    # 获取当前 SHA
    try:
        get_resp = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None
    except:
        sha = None

    # 编码内容
    content = json.dumps(data, ensure_ascii=False, indent=2)
    encoded_content = base64.b64encode(content.encode()).decode()

    # 推送
    payload = {
        "message": f"chore: 更新宏观数据 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": encoded_content,
        "branch": GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    try:
        resp = requests.put(url, headers={"Authorization": f"token {GITHUB_TOKEN}"}, json=payload)
        if resp.status_code in [200, 201]:
            print("  [SUCCESS] 已推送到 GitHub")
        else:
            print(f"  [ERROR] GitHub push failed: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"  [ERROR] GitHub push: {e}")

# ============ 主函数 ============
def main():
    print("=" * 50)
    print("宏观仪表盘 - 每日数据更新")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 拉取数据
    fred_data = fetch_fred_all()
    yf_data = fetch_yfinance_all()
    china_data = fetch_china_akshare()

    # 计算信号
    overview = calculate_signals(fred_data, china_data)

    # 组装输出
    output = {
        "meta": {
            "updated_at": datetime.now().isoformat(),
            "data_date": date.today().isoformat(),
            "status": "success",
        },
        "overview": overview,
        "china": china_data,
        "fred": fred_data,
        "assets": yf_data,
    }

    # 推送到 GitHub
    push_to_github(output)

    print("\n" + "=" * 50)
    print("完成!")
    print("=" * 50)

if __name__ == "__main__":
    main()
