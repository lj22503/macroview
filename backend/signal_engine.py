"""
信号合成引擎
- 各因子打分（-2 到 +2）
- 加权合成 RISK ON/OFF
- 仓位映射
"""

from dataclasses import dataclass
from typing import List, Dict, Optional

# ============ 权重配置 ============
WEIGHTS = {
    "cn_us_spread": 0.20,   # 中美利差
    "m1_m2_spread": 0.25,   # M1-M2剪刀差
    "vix": 0.15,            # VIX
    "north_money": 0.15,     # 北向资金
    "credit_spread": 0.25,   # 信用利差
}

# ============ 打分规则 ============
def score_cn_us_spread(value: Optional[float], trend: str = "持平") -> int:
    """中美利差打分"""
    if value is None:
        return 0
    if value > -150 and trend == "收窄":
        return 2
    elif -200 <= value <= -150 and trend == "收窄":
        return 1
    elif -250 <= value <= -200 and trend == "持平":
        return 0
    elif value < -250 and trend == "走阔":
        return -1
    elif value < -300 and trend == "加速走阔":
        return -2
    return 0

def score_m1_m2_spread(value: Optional[float], trend: str = "持平") -> int:
    """M1-M2剪刀差打分"""
    if value is None:
        return 0
    if value > -3 and trend == "收窄":
        return 2
    elif -8 <= value <= -3 and trend == "收窄":
        return 1
    elif trend == "持平":
        return 0
    elif -8 < value <= -5 and trend == "走阔":
        return -1
    elif value <= -8 and trend == "走阔":
        return -2
    return 0

def score_vix(value: Optional[float]) -> int:
    """VIX打分"""
    if value is None:
        return 0
    if value < 14:
        return 2
    elif 14 <= value < 18:
        return 1
    elif 18 <= value <= 22:
        return 0
    elif 22 < value <= 28:
        return -1
    else:  # > 28
        return -2

def score_north_money_3d(value: Optional[float]) -> int:
    """北向资金3日累计打分"""
    if value is None:
        return 0
    if value > 100:
        return 2
    elif 50 < value <= 100:
        return 1
    elif -50 <= value <= 50:
        return 0
    elif -100 <= value < -50:
        return -1
    else:  # < -100
        return -2

def score_credit_spread(value: Optional[float]) -> int:
    """高收益债利差打分"""
    if value is None:
        return 0
    if value < 350:
        return 2
    elif 350 <= value < 450:
        return 1
    elif 450 <= value <= 550:
        return 0
    elif 550 < value <= 700:
        return -1
    else:  # > 700
        return -2

# ============ 仓位映射 ============
def map_score_to_allocation(score: float) -> Dict[str, int]:
    """总分映射到仓位"""
    if score >= 1.5:
        return {"equity": 85, "bond": 10, "gold": 5, "cash": 0}
    elif score >= 0.5:
        return {"equity": 65, "bond": 25, "gold": 10, "cash": 0}
    elif score >= -0.5:
        return {"equity": 45, "bond": 35, "gold": 10, "cash": 10}
    elif score >= -1.5:
        return {"equity": 25, "bond": 40, "gold": 15, "cash": 20}
    else:
        return {"equity": 10, "bond": 40, "gold": 20, "cash": 30}

def map_score_to_label(score: float) -> str:
    """总分映射到叙事标签"""
    if score >= 1.5:
        return "全面扩张"
    elif score >= 0.5:
        return "温和复苏"
    elif score >= -0.5:
        return "结构分化"
    elif score >= -1.5:
        return "收缩压力"
    else:
        return "系统性风险"

def map_score_to_bias(score: float) -> str:
    """总分映射到 RISK ON/OFF"""
    if score > 0.3:
        return "RISK_ON"
    elif score < -0.3:
        return "RISK_OFF"
    else:
        return "NEUTRAL"

# ============ 观点话术映射 ============
def get_view_comment(factor: str, value: Optional[float], signal: int) -> Dict[str, str]:
    """获取观点话术"""
    views = {
        "cn_us_spread": {
            2: ("资本回流中国", "人民币资产吸引力上升，外资加速配置中国"),
            1: ("利差收窄", "资本外流压力边际减弱"),
            0: ("利差稳定", "中美利差维持现状，外资观望"),
            -1: ("资本外逃风险", "美元资产回报率相对更高，外资面临汇兑损失"),
            -2: ("资本外逃加剧", "利差深度倒挂，外资加速撤离人民币资产"),
        },
        "m1_m2_spread": {
            2: ("资金活化", "企业投资意愿强，牛市流动性基础坚实"),
            1: ("资金活化迹象", "M1增速回升，资金活化度提高"),
            0: ("结构分化", "实体需求疲软，资金在金融体系空转"),
            -1: ("资金沉淀", "企业躺平，经济活力不足"),
            -2: ("通缩风险", "资金严重沉淀，需求极度萎靡"),
        },
        "vix": {
            2: ("过度自满", "市场对风险毫无防备，往往是大跌前兆"),
            1: ("风险偏好正常", "市场情绪健康，专注选股"),
            0: ("波动正常区间", "VIX处于历史正常区间"),
            -1: ("风险偏好下降", "恐慌情绪升温，防御为主"),
            -2: ("恐慌性抛售", "踩踏式出逃，但恐慌峰值往往对应中期底部"),
        },
        "north_money": {
            2: ("外资大幅流入", "聪明钱系统性回补中国头寸"),
            1: ("外资温和流入", "北向资金持续净买入"),
            0: ("外资观望", "北向资金小幅波动，等待信号明确"),
            -1: ("外资小幅流出", "外资谨慎减仓"),
            -2: ("外资战略撤离", "通常对应人民币贬值或地缘政治恶化"),
        },
        "credit_spread": {
            2: ("信用畅通", "企业融资毫无压力，垃圾债市场歌舞升平"),
            1: ("信用宽松", "银行放贷意愿强，高风险企业融资顺畅"),
            0: ("信用正常", "信用环境健康，企业再融资压力可控"),
            -1: ("信用收紧", "银行惜贷，高风险企业借新还旧出现困难"),
            -2: ("信用冻结", "流动性危机正在传导，企业违约潮担忧加剧"),
        },
    }

    if factor in views and signal in views[factor]:
        signal_text, narrative = views[factor][signal]
    else:
        signal_text, narrative = "未知", "数据不足"

    return {
        "view": signal_text,
        "narrative": narrative,
    }

# ============ 信号合成主函数 ============
@dataclass
class FactorResult:
    name: str
    name_cn: str
    value: Optional[float]
    signal: int
    weight: float
    contribution: float
    trend: str
    view: str
    narrative: str

@dataclass
class ScoreResult:
    bias: str
    confidence: int
    score: float
    label: str
    primary_driver: List[str]
    suggestions: Dict[str, int]
    narrative: str
    factor_details: List[FactorResult]

def calculate_risk_score(
    cn_us_spread: Optional[float] = None,
    cn_us_spread_trend: str = "持平",
    m1_m2_spread: Optional[float] = None,
    m1_m2_spread_trend: str = "持平",
    vix: Optional[float] = None,
    north_money_3d: Optional[float] = None,
    credit_spread: Optional[float] = None,
) -> ScoreResult:
    """计算 RISK ON/OFF 评分"""

    # 各因子打分
    signals = {
        "cn_us_spread": score_cn_us_spread(cn_us_spread, cn_us_spread_trend),
        "m1_m2_spread": score_m1_m2_spread(m1_m2_spread, m1_m2_spread_trend),
        "vix": score_vix(vix),
        "north_money": score_north_money_3d(north_money_3d),
        "credit_spread": score_credit_spread(credit_spread),
    }

    # 计算加权总分
    total_score = sum(
        signals[f] * WEIGHTS[f]
        for f in WEIGHTS.keys()
    )

    # 各因子详情
    factor_details = []
    primary_drivers = []

    factor_names = {
        "cn_us_spread": ("中美利差", "bp"),
        "m1_m2_spread": ("M1-M2剪刀差", "%"),
        "vix": ("VIX恐慌指数", ""),
        "north_money": ("北向资金3日累计", "亿"),
        "credit_spread": ("高收益债利差", "bp"),
    }

    factor_values = {
        "cn_us_spread": cn_us_spread,
        "m1_m2_spread": m1_m2_spread,
        "vix": vix,
        "north_money": north_money_3d,
        "credit_spread": credit_spread,
    }

    trends = {
        "cn_us_spread": cn_us_spread_trend,
        "m1_m2_spread": m1_m2_spread_trend,
        "vix": "平稳" if vix and 14 <= vix <= 22 else ("偏高" if vix and vix > 22 else "偏低"),
        "north_money": "流入" if north_money_3d and north_money_3d > 50 else ("流出" if north_money_3d and north_money_3d < -50 else "观望"),
        "credit_spread": "平稳" if credit_spread and 350 <= credit_spread <= 550 else ("走扩" if credit_spread and credit_spread > 550 else "收窄"),
    }

    for factor, weight in WEIGHTS.items():
        signal = signals[factor]
        value = factor_values.get(factor)
        trend = trends.get(factor, "持平")
        name_cn, unit = factor_names.get(factor, (factor, ""))

        contribution = signal * weight
        view_info = get_view_comment(factor, value, signal)

        if signal > 0 and factor in ["cn_us_spread", "m1_m2_spread", "vix", "north_money", "credit_spread"]:
            primary_drivers.append(name_cn)

        factor_details.append(FactorResult(
            name=factor,
            name_cn=name_cn,
            value=value,
            signal=signal,
            weight=weight,
            contribution=contribution,
            trend=trend,
            view=view_info["view"],
            narrative=view_info["narrative"],
        ))

    # 置信度：基于有多少有效数据
    valid_count = sum(1 for v in factor_values.values() if v is not None)
    confidence = min(95, max(30, valid_count * 19))  # 每有一个有效数据 +19%，全有 = 95%

    # 映射到输出
    bias = map_score_to_bias(total_score)
    label = map_score_to_label(total_score)
    suggestions = map_score_to_allocation(total_score)

    # 生成叙事文本
    if primary_drivers:
        narrative = f"{'、'.join(primary_drivers[:3])}，{label}。"
    else:
        narrative = f"多空信号交织，市场 {label}。"

    return ScoreResult(
        bias=bias,
        confidence=confidence,
        score=round(total_score, 2),
        label=label,
        primary_driver=primary_drivers[:3],
        suggestions=suggestions,
        narrative=narrative,
        factor_details=factor_details,
    )
