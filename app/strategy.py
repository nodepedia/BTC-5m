from __future__ import annotations

from app.models import MarketSnapshot, SignalAction, SignalDecision, TrendDirection


class StrategyEngine:
    """Evaluate trading signals from a prepared market snapshot."""

    def evaluate_entry(self, snapshot: MarketSnapshot) -> SignalDecision:
        if self._is_bullish_trend(snapshot):
            if snapshot.touch_lower_bb and (snapshot.rsi_value <= 10 or snapshot.macd_first_green):
                return SignalDecision(
                    action=SignalAction.ENTER_LONG,
                    reason="Bullish trend + touch lower BB + RSI<=10 or MACD first green",
                )

        if self._is_bearish_trend(snapshot):
            if snapshot.touch_upper_bb and (snapshot.rsi_value >= 90 or snapshot.macd_first_red):
                return SignalDecision(
                    action=SignalAction.ENTER_SHORT,
                    reason="Bearish trend + touch upper BB + RSI>=90 or MACD first red",
                )

        return SignalDecision(action=SignalAction.HOLD, reason="No valid entry signal")

    def evaluate_exit(
        self,
        snapshot: MarketSnapshot,
        current_position: SignalAction,
    ) -> SignalDecision:
        if current_position == SignalAction.ENTER_LONG:
            if snapshot.touch_upper_bb and (snapshot.rsi_value >= 90 or snapshot.macd_first_red):
                return SignalDecision(
                    action=SignalAction.EXIT_LONG,
                    reason="Touch upper BB + RSI>=90 or MACD first red",
                )

        if current_position == SignalAction.ENTER_SHORT:
            if snapshot.touch_lower_bb and (snapshot.rsi_value <= 10 or snapshot.macd_first_green):
                return SignalDecision(
                    action=SignalAction.EXIT_SHORT,
                    reason="Touch lower BB + RSI<=10 or MACD first green",
                )

        return SignalDecision(action=SignalAction.HOLD, reason="No valid exit signal")

    @staticmethod
    def _is_bullish_trend(snapshot: MarketSnapshot) -> bool:
        return (
            snapshot.supertrend_5m == TrendDirection.BULLISH
            and snapshot.supertrend_30m == TrendDirection.BULLISH
        )

    @staticmethod
    def _is_bearish_trend(snapshot: MarketSnapshot) -> bool:
        return (
            snapshot.supertrend_5m == TrendDirection.BEARISH
            and snapshot.supertrend_30m == TrendDirection.BEARISH
        )
