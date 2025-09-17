from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal

import pandas as pd

LevelKind = Literal["support", "resistance"]


@dataclass
class PriceLevel:
    """Represents a price level detected in the market."""

    price: float
    kind: LevelKind
    touches: int
    timeframe: str
    last_touched: pd.Timestamp


class SupportResistanceAnalyzer:
    """Detects support and resistance levels from OHLC data."""

    def __init__(
        self,
        pivot_lookback: int = 5,
        level_tolerance: float = 0.003,
        min_touches: int = 2,
    ) -> None:
        self.pivot_lookback = pivot_lookback
        self.level_tolerance = level_tolerance
        self.min_touches = min_touches

    def detect_levels(self, candles: pd.DataFrame, timeframe: str) -> List[PriceLevel]:
        if candles.empty:
            return []

        candidates: List[PriceLevel] = []
        highs = candles["high"].reset_index(drop=True)
        lows = candles["low"].reset_index(drop=True)
        close_times = candles["close_time"].reset_index(drop=True)

        for idx in range(self.pivot_lookback, len(candles) - self.pivot_lookback):
            window_slice = slice(idx - self.pivot_lookback, idx + self.pivot_lookback + 1)
            is_resistance = highs.iloc[idx] == highs.iloc[window_slice].max()
            is_support = lows.iloc[idx] == lows.iloc[window_slice].min()

            if is_resistance:
                self._add_level(
                    candidates,
                    price=highs.iloc[idx],
                    kind="resistance",
                    timeframe=timeframe,
                    timestamp=close_times.iloc[idx],
                )
            if is_support:
                self._add_level(
                    candidates,
                    price=lows.iloc[idx],
                    kind="support",
                    timeframe=timeframe,
                    timestamp=close_times.iloc[idx],
                )

        for level in candidates:
            touches = self._count_touches(
                candles,
                level.price,
                level.kind,
                tolerance=self.level_tolerance,
            )
            level.touches = touches

        filtered = [
            level for level in candidates if level.touches >= self.min_touches
        ]
        return filtered

    def _add_level(
        self,
        levels: List[PriceLevel],
        price: float,
        kind: LevelKind,
        timeframe: str,
        timestamp: pd.Timestamp,
    ) -> None:
        for existing in levels:
            if existing.kind != kind or existing.timeframe != timeframe:
                continue
            if self._is_close(existing.price, price):
                merged_price = (existing.price * existing.touches + price) / (
                    existing.touches + 1
                )
                existing.price = merged_price
                existing.touches += 1
                if timestamp > existing.last_touched:
                    existing.last_touched = timestamp
                return

        levels.append(
            PriceLevel(
                price=price,
                kind=kind,
                touches=1,
                timeframe=timeframe,
                last_touched=timestamp,
            )
        )

    def _count_touches(
        self,
        candles: pd.DataFrame,
        price: float,
        kind: LevelKind,
        tolerance: float,
    ) -> int:
        if kind == "support":
            values = candles["low"]
        else:
            values = candles["high"]
        within = (values - price).abs() <= price * tolerance
        return int(within.sum())

    def _is_close(self, reference: float, candidate: float) -> bool:
        return abs(reference - candidate) <= reference * self.level_tolerance
