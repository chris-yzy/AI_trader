from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ai_trader.analysis.support_resistance import PriceLevel
from ai_trader.analysis.volatility import VolatilityEvent


@dataclass
class LevelAlert:
    symbol: str
    timeframe: str
    level: PriceLevel
    price: float
    direction: str
    triggered_at: datetime

    def format_message(self) -> str:
        emoji = "🛑" if self.level.kind == "resistance" else "🛡️"
        return (
            f"{emoji} {self.symbol} {self.timeframe} {self.level.kind.upper()} {self.direction}\n"
            f"价格: {self.price:.2f} (关键位 {self.level.price:.2f})\n"
            f"触碰次数: {self.level.touches}"
        )


@dataclass
class VolatilityAlert:
    event: VolatilityEvent
    triggered_at: datetime

    def format_message(self) -> str:
        direction = "上涨" if self.event.percent_change > 0 else "下跌"
        percent = self.event.percent_change * 100
        return (
            "⚡ 市场波动提醒\n"
            f"{self.event.symbol} {direction} {percent:.2f}%\n"
            f"区间: {self.event.start_time.strftime('%Y-%m-%d %H:%M')} - {self.event.end_time.strftime('%Y-%m-%d %H:%M')} UTC\n"
            f"价格: {self.event.start_price:.2f} -> {self.event.end_price:.2f}"
        )


def utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)
