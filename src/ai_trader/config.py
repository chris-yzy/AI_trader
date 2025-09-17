from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Sequence


@dataclass
class TimeframeSettings:
    """Configuration values for analysing a single timeframe."""

    name: str
    interval: str
    lookback: int = 500
    pivot_lookback: int = 5
    level_tolerance: float = 0.003
    min_touches: int = 2


@dataclass
class SymbolSettings:
    """Symbols that should be monitored by the bot."""

    name: str
    quote: str = "USDT"

    @property
    def pair(self) -> str:
        return f"{self.name}{self.quote}"


@dataclass
class BotConfig:
    """Top level configuration for the Telegram alert bot."""

    telegram_token: str
    chat_ids: Sequence[int]
    symbols: Sequence[SymbolSettings] = field(
        default_factory=lambda: [
            SymbolSettings("BTC"),
            SymbolSettings("ETH"),
        ]
    )
    timeframes: Sequence[TimeframeSettings] = field(
        default_factory=lambda: [
            TimeframeSettings("1d", "1d"),
            TimeframeSettings("4h", "4h"),
            TimeframeSettings("1h", "1h"),
        ]
    )
    price_alert_tolerance: float = 0.002
    volatility_window_minutes: int = 15
    volatility_threshold: float = 0.01
    volatility_interval: str = "1m"
    volatility_lookback: int = 120
    data_source_url: str = "https://api.binance.com"
    request_timeout: int = 10
    poll_interval_seconds: int = 300

    @classmethod
    def from_env(cls) -> "BotConfig":
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")

        chat_id_env = os.getenv("TELEGRAM_CHAT_IDS", "")
        chat_ids: List[int] = []
        for raw_id in chat_id_env.split(","):
            raw_id = raw_id.strip()
            if not raw_id:
                continue
            try:
                chat_ids.append(int(raw_id))
            except ValueError as exc:
                raise ValueError(
                    "TELEGRAM_CHAT_IDS must contain integers separated by commas"
                ) from exc

        if not chat_ids:
            raise ValueError("At least one chat id must be provided")

        price_alert_tolerance = float(
            os.getenv("PRICE_ALERT_TOLERANCE", cls.price_alert_tolerance)
        )
        volatility_window_minutes = int(
            os.getenv("VOLATILITY_WINDOW_MINUTES", cls.volatility_window_minutes)
        )
        volatility_threshold = float(
            os.getenv("VOLATILITY_THRESHOLD", cls.volatility_threshold)
        )
        volatility_interval = os.getenv("VOLATILITY_INTERVAL", cls.volatility_interval)
        volatility_lookback = int(
            os.getenv("VOLATILITY_LOOKBACK", cls.volatility_lookback)
        )
        data_source_url = os.getenv("DATA_SOURCE_URL", cls.data_source_url)
        request_timeout = int(os.getenv("REQUEST_TIMEOUT", cls.request_timeout))
        poll_interval_seconds = int(
            os.getenv("POLL_INTERVAL_SECONDS", cls.poll_interval_seconds)
        )

        return cls(
            telegram_token=token,
            chat_ids=chat_ids,
            price_alert_tolerance=price_alert_tolerance,
            volatility_window_minutes=volatility_window_minutes,
            volatility_threshold=volatility_threshold,
            volatility_interval=volatility_interval,
            volatility_lookback=volatility_lookback,
            data_source_url=data_source_url,
            request_timeout=request_timeout,
            poll_interval_seconds=poll_interval_seconds,
        )
