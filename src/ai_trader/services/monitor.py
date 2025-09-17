from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence

import pandas as pd

from ai_trader.alerting.alerts import LevelAlert, VolatilityAlert, utcnow
from ai_trader.analysis.support_resistance import PriceLevel, SupportResistanceAnalyzer
from ai_trader.analysis.volatility import VolatilityAnalyzer
from ai_trader.config import BotConfig, SymbolSettings, TimeframeSettings
from ai_trader.data.binance import BinanceClient, DataSourceError
from ai_trader.telegram.messenger import TelegramMessenger

logger = logging.getLogger(__name__)


@dataclass
class MarketMonitor:
    config: BotConfig
    data_client: BinanceClient
    messenger: TelegramMessenger
    sr_analyzer: SupportResistanceAnalyzer = field(default_factory=SupportResistanceAnalyzer)
    vol_analyzer: Optional[VolatilityAnalyzer] = None

    def __post_init__(self) -> None:
        if self.vol_analyzer is None:
            self.vol_analyzer = VolatilityAnalyzer(
                self.config.volatility_window_minutes, self.config.volatility_threshold
            )
        self.previous_prices: Dict[str, float] = {}
        self.active_level_alerts: Dict[str, str] = {}
        self.last_volatility_alert: Dict[str, pd.Timestamp] = {}

    def run_once(self) -> List[str]:
        alerts_to_send: List[str] = []
        for symbol in self.config.symbols:
            pair = symbol.pair
            try:
                current_price = self.data_client.fetch_last_price(pair)
            except DataSourceError as exc:
                logger.warning("Failed to fetch price for %s: %s", pair, exc)
                continue

            for timeframe in self.config.timeframes:
                try:
                    candles = self.data_client.fetch_klines(
                        pair,
                        interval=timeframe.interval,
                        limit=timeframe.lookback,
                    )
                except DataSourceError as exc:
                    logger.warning(
                        "Failed to fetch klines for %s (%s): %s",
                        pair,
                        timeframe.name,
                        exc,
                    )
                    continue

                levels = self.sr_analyzer.detect_levels(candles, timeframe.name)
                level_alerts = self._evaluate_levels(
                    symbol=symbol,
                    timeframe=timeframe,
                    levels=levels,
                    price=current_price,
                )
                alerts_to_send.extend(level_alerts)

            volatility_alert = self._evaluate_volatility(symbol)
            if volatility_alert:
                alerts_to_send.append(volatility_alert)

            self.previous_prices[pair] = current_price

        return alerts_to_send

    def dispatch_alerts(self, alerts: Iterable[str]) -> None:
        for message in alerts:
            try:
                self.messenger.send_message(message)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("Failed to dispatch alert: %s", exc)

    def _evaluate_levels(
        self,
        symbol: SymbolSettings,
        timeframe: TimeframeSettings,
        levels: Sequence[PriceLevel],
        price: float,
    ) -> List[str]:
        previous_price = self.previous_prices.get(symbol.pair)
        tolerance = self.config.price_alert_tolerance
        messages: List[str] = []

        for level in levels:
            direction = self._level_trigger(level, price, previous_price, tolerance)
            key = self._level_key(symbol.pair, timeframe.name, level)
            if direction:
                if self.active_level_alerts.get(key) == direction:
                    continue
                alert = LevelAlert(
                    symbol=symbol.name,
                    timeframe=timeframe.name,
                    level=level,
                    price=price,
                    direction=direction,
                    triggered_at=utcnow(),
                )
                messages.append(alert.format_message())
                self.active_level_alerts[key] = direction
            else:
                self.active_level_alerts.pop(key, None)
        return messages

    def _evaluate_volatility(self, symbol: SymbolSettings) -> Optional[str]:
        if self.vol_analyzer is None:
            return None

        pair = symbol.pair
        try:
            candles = self.data_client.fetch_klines(
                pair,
                interval=self.config.volatility_interval,
                limit=self.config.volatility_lookback,
            )
        except DataSourceError as exc:
            logger.warning("Failed to fetch volatility data for %s: %s", pair, exc)
            return None

        event = self.vol_analyzer.detect(
            symbol.name, self.config.volatility_interval, candles
        )
        if not event:
            return None

        last_time = self.last_volatility_alert.get(pair)
        if last_time and event.end_time <= last_time:
            return None

        alert = VolatilityAlert(event=event, triggered_at=utcnow())
        self.last_volatility_alert[pair] = event.end_time
        return alert.format_message()

    def _level_trigger(
        self,
        level: PriceLevel,
        price: float,
        previous_price: Optional[float],
        tolerance: float,
    ) -> Optional[str]:
        threshold = level.price * tolerance
        if level.kind == "support":
            if price <= level.price - threshold:
                if not previous_price or previous_price > level.price - threshold:
                    return "跌破"
            elif abs(price - level.price) <= threshold:
                return "触及"
        else:
            if price >= level.price + threshold:
                if not previous_price or previous_price < level.price + threshold:
                    return "突破"
            elif abs(price - level.price) <= threshold:
                return "触及"
        return None

    def _level_key(
        self, symbol: str, timeframe: str, level: PriceLevel
    ) -> str:
        rounded = round(level.price, 2)
        return f"{symbol}:{timeframe}:{level.kind}:{rounded}"
