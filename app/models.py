from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TrendDirection(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class SignalAction(str, Enum):
    ENTER_LONG = "enter_long"
    EXIT_LONG = "exit_long"
    ENTER_SHORT = "enter_short"
    EXIT_SHORT = "exit_short"
    HOLD = "hold"


class PositionSide(str, Enum):
    FLAT = "flat"
    LONG = "long"
    SHORT = "short"


@dataclass(frozen=True)
class MarketSnapshot:
    supertrend_5m: TrendDirection
    supertrend_30m: TrendDirection
    touch_lower_bb: bool
    touch_upper_bb: bool
    rsi_value: float
    macd_first_green: bool
    macd_first_red: bool
    source_symbol: str
    source_name: str
    mark_price: float
    candle_timestamp: int


@dataclass(frozen=True)
class SignalDecision:
    action: SignalAction
    reason: str
