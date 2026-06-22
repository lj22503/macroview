"""
分层存储：归档 + meta + 最新数据
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
ARCHIVE_DIR = DATA_DIR / "archives"
ARCHIVE_KEEP_DAYS = 30


def ensure_dirs():
    DATA_DIR.mkdir(exist_ok=True)
    ARCHIVE_DIR.mkdir(exist_ok=True)


def save_archive(data: dict) -> str:
    today = date.today().isoformat()
    archive_file = ARCHIVE_DIR / f"{today}.json"
    with open(archive_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    _cleanup_old_archives()
    return str(archive_file)


def update_meta(data_date, freshness, source_status, total_fields, valid_fields) -> dict:
    ensure_dirs()
    meta_file = DATA_DIR / "meta.json"
    meta = {
        "data_date": data_date,
        "updated_at": datetime.now().isoformat(),
        "data_freshness": freshness,
        "source_status": source_status,
        "coverage": f"{valid_fields}/{total_fields}",
        "version": "2",
    }
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return meta


def assess_freshness(data_updated_at: str) -> str:
    try:
        dt = datetime.fromisoformat(data_updated_at.replace("Z", "+00:00"))
        age_hours = (datetime.now() - dt).total_seconds() / 3600
        if age_hours < 6:
            return "fresh"
        elif age_hours < 24:
            return "stale"
        else:
            return "partial"
    except:
        return "partial"


def save_latest(data: dict, freshness: str = "fresh") -> str:
    ensure_dirs()
    latest_file = DATA_DIR / "all_indicators.json"
    data["meta"]["data_freshness"] = freshness
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return str(latest_file)


def _cleanup_old_archives():
    cutoff = (datetime.now() - timedelta(days=ARCHIVE_KEEP_DAYS)).date().isoformat()
    for f in ARCHIVE_DIR.glob("*.json"):
        if f.stem < cutoff:
            try:
                f.unlink()
            except Exception:
                pass
