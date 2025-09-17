from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class VolatilityEvent:
    symbol: str
    timeframe: str
    percent_change: float
    start_time: pd.Timestamp
    end_time: pd.Timestamp
    start_price: float
    end_price: float


class VolatilityAnalyzer:
    def __init__(self, window_minutes: int, threshold: float) -> None:
        self.window = pd.Timedelta(minutes=window_minutes)
        self.threshold = threshold

    def detect(
        self, symbol: str, timeframe: str, candles: pd.DataFrame
    ) -> Optional[VolatilityEvent]:
        if candles.empty:
            return None

        last_time = candles["close_time"].iloc[-1]
        window_start = last_time - self.window
        window_df = candles[candles["close_time"] >= window_start]

        if len(window_df) < 2:
            return None

        start_price = float(window_df["close"].iloc[0])
        end_price = float(window_df["close"].iloc[-1])
        if start_price == 0:
            return None

        percent_change = (end_price - start_price) / start_price
        if abs(percent_change) < self.threshold:
            return None

        return VolatilityEvent(
            symbol=symbol,
            timeframe=timeframe,
            percent_change=percent_change,
            start_time=window_df["close_time"].iloc[0],
            end_time=last_time,
            start_price=start_price,
            end_price=end_price,
        )
