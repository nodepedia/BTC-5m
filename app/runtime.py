from __future__ import annotations

import time

from app.config import Settings
from app.data import MeteoraClient
from app.executor import DemoExecutor, DryRunExecutor
from app.indicators import build_indicator_snapshot
from app.models import MarketSnapshot, SignalAction
from app.portfolio import PortfolioTracker
from app.strategy import StrategyEngine


def build_market_snapshot(settings: Settings) -> MarketSnapshot:
    if settings.data_source != "meteora":
        raise ValueError(f"Unsupported data source: {settings.data_source}")

    client = MeteoraClient(pool_address=settings.meteora_pool_address)
    signal_candles = client.fetch_ohlcv(settings.signal_timeframe, settings.history_limit)
    trend_candles = client.fetch_ohlcv(settings.trend_timeframe, settings.history_limit)

    signal_snapshot = build_indicator_snapshot(signal_candles)
    trend_snapshot = build_indicator_snapshot(trend_candles)

    last_candle = signal_snapshot.last_candle
    touch_lower_bb = last_candle.low <= signal_snapshot.bollinger.lower
    touch_upper_bb = last_candle.high >= signal_snapshot.bollinger.upper
    macd_first_green = (
        signal_snapshot.macd_previous.histogram <= 0
        and signal_snapshot.macd_current.histogram > 0
    )
    macd_first_red = (
        signal_snapshot.macd_previous.histogram >= 0
        and signal_snapshot.macd_current.histogram < 0
    )

    print(
        f"Fetched source={settings.data_source} pool={settings.meteora_pool_name} "
        f"signal_candles={len(signal_candles)} trend_candles={len(trend_candles)}"
    )
    print(
        f"Latest {settings.signal_timeframe} candle "
        f"open={last_candle.open:.2f} high={last_candle.high:.2f} "
        f"low={last_candle.low:.2f} close={last_candle.close:.2f}"
    )
    print(
        f"Indicators RSI={signal_snapshot.rsi:.2f} "
        f"BB.lower={signal_snapshot.bollinger.lower:.2f} "
        f"BB.upper={signal_snapshot.bollinger.upper:.2f} "
        f"MACD.hist.prev={signal_snapshot.macd_previous.histogram:.6f} "
        f"MACD.hist.curr={signal_snapshot.macd_current.histogram:.6f}"
    )

    return MarketSnapshot(
        supertrend_5m=signal_snapshot.supertrend,
        supertrend_30m=trend_snapshot.supertrend,
        touch_lower_bb=touch_lower_bb,
        touch_upper_bb=touch_upper_bb,
        rsi_value=signal_snapshot.rsi,
        macd_first_green=macd_first_green,
        macd_first_red=macd_first_red,
        source_symbol=settings.symbol,
        source_name=settings.meteora_pool_name,
        mark_price=last_candle.close,
        candle_timestamp=last_candle.timestamp,
    )


def run_bot(settings: Settings) -> None:
    print(
        f"Starting bot mode={settings.bot_mode} symbol={settings.symbol} "
        f"label='{settings.strategy_label}' "
        f"live_loop={settings.local_live_loop} "
        f"poll_interval={settings.poll_interval_seconds}s "
        f"demo_accounts={settings.demo_account_count}"
    )

    iteration = 0
    tracker = PortfolioTracker(settings)
    while True:
        iteration += 1
        print(f"\n--- iteration={iteration} ---")
        _run_single_cycle(settings, tracker)

        if not settings.local_live_loop:
            break

        if settings.max_loop_iterations > 0 and iteration >= settings.max_loop_iterations:
            print(f"Stopping loop after {iteration} iteration(s) due to MAX_LOOP_ITERATIONS")
            break

        print(f"Sleeping for {settings.poll_interval_seconds} seconds before next cycle")
        time.sleep(settings.poll_interval_seconds)


def _run_single_cycle(settings: Settings, tracker: PortfolioTracker) -> None:
    strategy = StrategyEngine()
    snapshot = build_market_snapshot(settings)
    current_position = tracker.current_position_action()

    if current_position in {SignalAction.ENTER_LONG, SignalAction.ENTER_SHORT}:
        primary_signal = strategy.evaluate_exit(snapshot, current_position=current_position)
        print(f"Evaluated exit signal: {primary_signal.action.value} ({primary_signal.reason})")
    else:
        primary_signal = strategy.evaluate_entry(snapshot)
        print(f"Evaluated entry signal: {primary_signal.action.value} ({primary_signal.reason})")

    if settings.bot_mode == "demo":
        executor = DemoExecutor(settings)
        executor.execute(primary_signal)
        signal_to_apply = primary_signal.action
    else:
        executor = DryRunExecutor()
        executor.execute(primary_signal)
        signal_to_apply = primary_signal.action

    trade_messages = tracker.process_signal(signal_to_apply, snapshot)
    for message in trade_messages:
        print(message)
    for line in tracker.summary_lines():
        print(line)
