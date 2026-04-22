from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import sqrt

from app.data import Candle
from app.models import TrendDirection


@dataclass(frozen=True)
class BollingerBandState:
    middle: float
    upper: float
    lower: float


@dataclass(frozen=True)
class MacdState:
    macd: float
    signal: float
    histogram: float


@dataclass(frozen=True)
class IndicatorSnapshot:
    supertrend: TrendDirection
    rsi: float
    bollinger: BollingerBandState
    macd_current: MacdState
    macd_previous: MacdState
    last_candle: Candle


def build_indicator_snapshot(candles: list[Candle]) -> IndicatorSnapshot:
    if len(candles) < 50:
        raise ValueError("At least 50 candles are required to build indicators reliably")

    supertrend_direction = compute_supertrend_direction(candles)
    rsi_value = compute_rsi(candles)
    bollinger = compute_bollinger_bands(candles)
    macd_previous, macd_current = compute_macd_states(candles)

    return IndicatorSnapshot(
        supertrend=supertrend_direction,
        rsi=rsi_value,
        bollinger=bollinger,
        macd_current=macd_current,
        macd_previous=macd_previous,
        last_candle=candles[-1],
    )


def compute_rsi(candles: list[Candle], period: int = 14) -> float:
    closes = [candle.close for candle in candles]
    if len(closes) < period + 1:
        raise ValueError("Not enough candles for RSI")

    gains: list[float] = []
    losses: list[float] = []
    for index in range(1, period + 1):
        delta = closes[index] - closes[index - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))

    average_gain = sum(gains) / period
    average_loss = sum(losses) / period

    for index in range(period + 1, len(closes)):
        delta = closes[index] - closes[index - 1]
        gain = max(delta, 0.0)
        loss = max(-delta, 0.0)
        average_gain = ((average_gain * (period - 1)) + gain) / period
        average_loss = ((average_loss * (period - 1)) + loss) / period

    if average_loss == 0:
        return 100.0

    rs = average_gain / average_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_bollinger_bands(
    candles: list[Candle],
    period: int = 20,
    std_multiplier: float = 2.0,
) -> BollingerBandState:
    closes = [candle.close for candle in candles]
    if len(closes) < period:
        raise ValueError("Not enough candles for Bollinger Bands")

    window = closes[-period:]
    middle = sum(window) / period
    variance = sum((value - middle) ** 2 for value in window) / period
    std_dev = sqrt(variance)

    return BollingerBandState(
        middle=middle,
        upper=middle + (std_multiplier * std_dev),
        lower=middle - (std_multiplier * std_dev),
    )


def compute_macd_states(candles: list[Candle]) -> tuple[MacdState, MacdState]:
    closes = [candle.close for candle in candles]
    if len(closes) < 35:
        raise ValueError("Not enough candles for MACD")

    ema12 = _ema_series(closes, 12)
    ema26 = _ema_series(closes, 26)
    macd_line = [fast - slow for fast, slow in zip(ema12, ema26, strict=True)]
    signal_line = _ema_series(macd_line, 9)
    histogram = [macd - signal for macd, signal in zip(macd_line, signal_line, strict=True)]

    previous = MacdState(
        macd=macd_line[-2],
        signal=signal_line[-2],
        histogram=histogram[-2],
    )
    current = MacdState(
        macd=macd_line[-1],
        signal=signal_line[-1],
        histogram=histogram[-1],
    )
    return previous, current


def compute_supertrend_direction(
    candles: list[Candle],
    period: int = 10,
    multiplier: float = 3.0,
) -> TrendDirection:
    if len(candles) < period + 2:
        raise ValueError("Not enough candles for Supertrend")

    atr_values = _atr_series(candles, period)
    final_upper: list[float] = []
    final_lower: list[float] = []
    direction = TrendDirection.NEUTRAL

    for index, candle in enumerate(candles):
        hl2 = (candle.high + candle.low) / 2.0
        atr = atr_values[index]
        basic_upper = hl2 + (multiplier * atr)
        basic_lower = hl2 - (multiplier * atr)

        if index == 0:
            final_upper.append(basic_upper)
            final_lower.append(basic_lower)
            continue

        prev_upper = final_upper[-1]
        prev_lower = final_lower[-1]
        prev_close = candles[index - 1].close

        current_upper = (
            basic_upper
            if basic_upper < prev_upper or prev_close > prev_upper
            else prev_upper
        )
        current_lower = (
            basic_lower
            if basic_lower > prev_lower or prev_close < prev_lower
            else prev_lower
        )

        final_upper.append(current_upper)
        final_lower.append(current_lower)

        if candle.close > current_upper:
            direction = TrendDirection.BULLISH
        elif candle.close < current_lower:
            direction = TrendDirection.BEARISH
        elif direction == TrendDirection.NEUTRAL:
            direction = (
                TrendDirection.BULLISH
                if candle.close >= hl2
                else TrendDirection.BEARISH
            )

    return direction


def _ema_series(values: list[float], period: int) -> list[float]:
    if len(values) < period:
        raise ValueError("Not enough values for EMA")

    multiplier = 2.0 / (period + 1)
    ema_values: list[float] = []
    ema = values[0]

    for value in values:
        ema = (value - ema) * multiplier + ema
        ema_values.append(ema)

    return ema_values


def _atr_series(candles: list[Candle], period: int) -> list[float]:
    true_ranges: list[float] = []
    for index, candle in enumerate(candles):
        if index == 0:
            tr = candle.high - candle.low
        else:
            prev_close = candles[index - 1].close
            tr = max(
                candle.high - candle.low,
                abs(candle.high - prev_close),
                abs(candle.low - prev_close),
            )
        true_ranges.append(tr)

    atr_values: list[float] = []
    rolling: deque[float] = deque(maxlen=period)
    atr = 0.0

    for tr in true_ranges:
        rolling.append(tr)
        if len(rolling) < period:
            atr_values.append(sum(rolling) / len(rolling))
            continue
        if atr == 0.0:
            atr = sum(rolling) / period
        else:
            atr = ((atr * (period - 1)) + tr) / period
        atr_values.append(atr)

    return atr_values
