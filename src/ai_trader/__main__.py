from __future__ import annotations

import logging
import time

from ai_trader.config import BotConfig
from ai_trader.data.binance import BinanceClient
from ai_trader.services.monitor import MarketMonitor
from ai_trader.telegram.messenger import TelegramMessenger


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)

    config = BotConfig.from_env()
    data_client = BinanceClient(config.data_source_url, timeout=config.request_timeout)
    messenger = TelegramMessenger(
        token=config.telegram_token,
        chat_ids=config.chat_ids,
        timeout=config.request_timeout,
    )
    monitor = MarketMonitor(
        config=config,
        data_client=data_client,
        messenger=messenger,
    )

    logger.info(
        "Starting market monitor for symbols: %s",
        ", ".join(symbol.name for symbol in config.symbols),
    )

    try:
        while True:
            alerts = monitor.run_once()
            if alerts:
                monitor.dispatch_alerts(alerts)
            time.sleep(config.poll_interval_seconds)
    except KeyboardInterrupt:
        logger.info("Stopping monitor")


if __name__ == "__main__":
    main()
