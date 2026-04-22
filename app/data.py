from __future__ import annotations

import json
import time
from dataclasses import dataclass
from urllib.error import HTTPError
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


METEORA_BASE_URL = "https://dlmm.datapi.meteora.ag"


@dataclass(frozen=True)
class Candle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class MeteoraClient:
    def __init__(self, pool_address: str, timeout_seconds: float = 10.0) -> None:
        self.pool_address = pool_address
        self.timeout_seconds = timeout_seconds

    def fetch_ohlcv(self, timeframe: str, limit: int) -> list[Candle]:
        seconds_per_candle = _seconds_per_timeframe(timeframe)
        chunk_candles = 48
        cursor_end = int(time.time())
        all_candles: dict[int, Candle] = {}

        while len(all_candles) < limit:
            start_time = cursor_end - (chunk_candles * seconds_per_candle)
            query = urlencode(
                {
                    "timeframe": timeframe,
                    "start_time": start_time,
                    "end_time": cursor_end,
                }
            )
            url = f"{METEORA_BASE_URL}/pools/{self.pool_address}/ohlcv?{query}"
            payload = self._fetch_json(url)
            raw_candles = payload.get("data", [])
            candles = [
                Candle(
                    timestamp=int(item["timestamp"]),
                    open=float(item["open"]),
                    high=float(item["high"]),
                    low=float(item["low"]),
                    close=float(item["close"]),
                    volume=float(item["volume"]),
                )
                for item in raw_candles
            ]
            if not candles:
                break

            for candle in candles:
                all_candles[candle.timestamp] = candle

            oldest_timestamp = min(candle.timestamp for candle in candles)
            next_cursor_end = oldest_timestamp - seconds_per_candle
            if next_cursor_end >= cursor_end:
                break
            cursor_end = next_cursor_end

        candles = list(all_candles.values())
        candles.sort(key=lambda candle: candle.timestamp)
        return candles[-limit:]

    def _fetch_json(self, url: str) -> dict[str, Any]:
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Meridian-OG-BTC-demo-bot/0.1",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Meteora API request failed: {exc.code} {body}") from exc


def _seconds_per_timeframe(timeframe: str) -> int:
    mapping = {
        "5m": 5 * 60,
        "30m": 30 * 60,
        "1h": 60 * 60,
        "2h": 2 * 60 * 60,
        "4h": 4 * 60 * 60,
        "12h": 12 * 60 * 60,
        "24h": 24 * 60 * 60,
    }
    try:
        return mapping[timeframe]
    except KeyError as exc:
        raise ValueError(f"Unsupported timeframe: {timeframe}") from exc
