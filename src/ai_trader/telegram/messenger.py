from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import requests


class TelegramError(RuntimeError):
    pass


@dataclass
class TelegramMessenger:
    token: str
    chat_ids: Iterable[int]
    timeout: int = 10

    def __post_init__(self) -> None:
        self._base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, text: str) -> None:
        for chat_id in self.chat_ids:
            response = requests.post(
                f"{self._base_url}/sendMessage",
                json={"chat_id": chat_id, "text": text},
                timeout=self.timeout,
            )
            if response.status_code != 200:
                raise TelegramError(
                    f"Failed to send message to {chat_id}: {response.text}"
                )
