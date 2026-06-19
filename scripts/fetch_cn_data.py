"""
本地中国宏观数据拉取脚本
使用 AKShare 获取中国数据，生成 JSON 并 push 到 GitHub

使用方法：
  python fetch_cn_data.py
"""

import os
import json
import subprocess
from datetime import datetime

try:
    import akshare as ak
    print("AKShare 版本:", ak.__version__)
except ImportError:
    print("错误：请先安装 AKShare: pip install akshare")
    exit(1)


def fetch_china_data():
    """拉取中国宏观数据"""
    data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "AKShare",
        "pmi": None,
        "cpi": None,
        "ppi": None,
        "m1m2": None,
        "social": None,
        "lpr": None,
        "north_bound": None,
    }

    try:
        df = ak.realthime_china_pmi()
        if not df.empty:
            data["pmi"] = {
                "value": float(df.iloc[0]["value"]) if "value" in df.columns else None,
                "name": "中国 PMI",
                "date": str(df.iloc[0]["date"]) if "date" in df.columns else None,
            }
        print("PMI 获取成功")
    except Exception as e:
        print(f"PMI 获取失败: {e}")

    try:
        df = ak.economic_figure(indicator="cpi")
        if not df.empty:
            data["cpi"] = {
                "value": float(df.iloc[0]["cpi"]),
                "name": "中国 CPI",
                "date": str(df.iloc[0]["date"]),
            }
        print("CPI 获取成功")
    except Exception as e:
        print(f"CPI 获取失败: {e}")

    try:
        df = ak.economic_figure(indicator="ppi")
        if not df.empty:
            data["ppi"] = {
                "value": float(df.iloc[0]["ppi"]),
                "name": "中国 PPI",
                "date": str(df.iloc[0]["date"]),
            }
        print("PPI 获取成功")
    except Exception as e:
        print(f"PPI 获取失败: {e}")

    try:
        df = ak.money_supply()
        if not df.empty:
            m1_rate = df.iloc[0]["m1_yoy"] if "m1_yoy" in df.columns else None
            m2_rate = df.iloc[0]["m2_yoy"] if "m2_yoy" in df.columns else None
            data["m1m2"] = {
                "m1_yoy": float(m1_rate) if m1_rate else None,
                "m2_yoy": float(m2_rate) if m2_rate else None,
                "spread": float(m2_rate - m1_rate) if m1_rate and m2_rate else None,
                "name": "M1-M2 剪刀差",
                "date": str(df.iloc[0]["date"]) if "date" in df.columns else None,
            }
        print("M1/M2 获取成功")
    except Exception as e:
        print(f"M1/M2 获取失败: {e}")

    try:
        df = ak.social_financing()
        if not df.empty:
            data["social"] = {
                "value": float(df.iloc[0]["增量"]) if "增量" in df.columns else None,
                "name": "社融增量",
                "date": str(df.iloc[0]["date"]) if "date" in df.columns else None,
            }
        print("社融获取成功")
    except Exception as e:
        print(f"社融获取失败: {e}")

    try:
        df = ak.loan_lpr()
        if not df.empty:
            lpr_1y = df.iloc[0]["lpr_1y"] if "lpr_1y" in df.columns else None
            data["lpr"] = {
                "value": float(lpr_1y) if lpr_1y else None,
                "name": "LPR (1年期)",
                "date": str(df.iloc[0]["date"]) if "date" in df.columns else None,
            }
        print("LPR 获取成功")
    except Exception as e:
        print(f"LPR 获取失败: {e}")

    return data


def save_and_push(data: dict):
    """保存 JSON 文件并 push 到 GitHub"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)

    file_path = os.path.join(data_dir, "cn_indicators.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"数据已保存到 {file_path}")

    try:
        subprocess.run(["git", "add", "data/cn_indicators.json"], cwd=project_root, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"更新宏观数据 {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
            cwd=project_root,
            check=True,
        )
        subprocess.run(["git", "push"], cwd=project_root, check=True)
        print("已推送到 GitHub")
    except subprocess.CalledProcessError as e:
        print(f"Git 操作失败: {e}")
        print("提示：请确保已配置 git remote 和 SSH key")


def main():
    print("=" * 50)
    print("开始拉取中国宏观数据...")
    print("=" * 50)

    data = fetch_china_data()
    save_and_push(data)

    print("=" * 50)
    print("数据拉取完成!")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print("=" * 50)


if __name__ == "__main__":
    main()
