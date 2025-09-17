from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

import pandas as pd
import requests


class DataSourceError(RuntimeError):
    """Raised when the remote data source fails."""


@dataclass
class BinanceClient:
    """Minimal client for retrieving market data from Binance."""

    base_url: str
    timeout: int = 10

    def _request(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        response = requests.get(
            f"{self.base_url}{path}", params=params, timeout=self.timeout
        )
        if response.status_code != 200:
            raise DataSourceError(
                f"Binance API request failed ({response.status_code}): {response.text}"
            )
        return response.json()

    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
    ) -> pd.DataFrame:
        """Fetch historical candle data for a given symbol and timeframe."""

        raw: Iterable[Iterable[Any]] = self._request(
            "/api/v3/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit},
        )

        if not raw:
            raise DataSourceError("Received empty kline payload")

        frame = pd.DataFrame(
            raw,
            columns=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base",
                "taker_buy_quote",
                "ignore",
            ],
        )
        numeric_cols = ["open", "high", "low", "close", "volume"]
        frame[numeric_cols] = frame[numeric_cols].astype(float)
        time_cols = ["open_time", "close_time"]
        frame[time_cols] = frame[time_cols].astype("int64")
        frame["open_time"] = pd.to_datetime(frame["open_time"], unit="ms", utc=True)
        frame["close_time"] = pd.to_datetime(frame["close_time"], unit="ms", utc=True)
        return frame

    def fetch_last_price(self, symbol: str) -> float:
        payload: Dict[str, Any] = self._request(
            "/api/v3/ticker/price", params={"symbol": symbol}
        )
        price_str = payload.get("price")
        if price_str is None:
            raise DataSourceError("Price not present in response")
        return float(price_str)
