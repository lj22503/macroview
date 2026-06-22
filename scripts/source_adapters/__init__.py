"""
数据源适配器基类
所有适配器返回统一格式: { "value": float|None, "source": str, "date": str|None, "quality": str }
quality: "live" | "stale" | "fallback"
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SourceResult:
    value: Optional[float]
    source: str        # e.g. "FRED", "yfinance", "AKShare"
    date: Optional[str]  # ISO date string
    quality: str       # "live" | "stale" | "fallback"
    error: Optional[str] = None

    def is_valid(self) -> bool:
        return self.value is not None and self.error is None


class SourceAdapter(ABC):
    """数据源适配器基类"""

    name: str = "base"  # 子类覆盖

    @abstractmethod
    def fetch(self, symbol: str) -> SourceResult:
        """拉取单个指标"""
        pass

    def fetch_all(self, symbols: dict[str, str]) -> dict[str, SourceResult]:
        """拉取多个指标，symbols = {字段名: 符号}"""
        results = {}
        for key, symbol in symbols.items():
            results[key] = self.fetch(symbol)
        return results
