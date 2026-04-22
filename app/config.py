from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


VALID_BOT_MODES = {"dry_run", "demo"}


@dataclass(frozen=True)
class DemoAccountConfig:
    index: int
    name: str
    api_key: str
    api_secret: str


@dataclass(frozen=True)
class Settings:
    bot_mode: str
    symbol: str
    strategy_label: str
    data_source: str
    meteora_pool_address: str
    meteora_pool_name: str
    signal_timeframe: str
    trend_timeframe: str
    history_limit: int
    local_live_loop: bool
    poll_interval_seconds: int
    max_loop_iterations: int
    data_dir: str
    paper_trade_size_usdc: float
    fee_bps: float
    demo_account_count: int
    demo_accounts: tuple[DemoAccountConfig, ...]


def load_settings(env_path: str | Path = ".env") -> Settings:
    env_file = Path(env_path)
    if env_file.exists():
        _load_env_file(env_file)

    bot_mode = os.getenv("BOT_MODE", "dry_run").strip().lower()
    if bot_mode not in VALID_BOT_MODES:
        valid = ", ".join(sorted(VALID_BOT_MODES))
        raise ValueError(f"BOT_MODE must be one of: {valid}")

    symbol = os.getenv("SYMBOL", "cbBTC/USDC").strip() or "cbBTC/USDC"
    strategy_label = os.getenv("STRATEGY_LABEL", "cbBTC BTC proxy demo").strip() or "cbBTC BTC proxy demo"
    data_source = os.getenv("DATA_SOURCE", "meteora").strip().lower() or "meteora"
    meteora_pool_address = os.getenv(
        "METEORA_POOL_ADDRESS",
        "7ubS3GccjhQY99AYNKXjNJqnXjaokEdfdV915xnCb96r",
    ).strip()
    meteora_pool_name = os.getenv("METEORA_POOL_NAME", "cbBTC-USDC").strip() or "cbBTC-USDC"
    signal_timeframe = os.getenv("SIGNAL_TIMEFRAME", "5m").strip() or "5m"
    trend_timeframe = os.getenv("TREND_TIMEFRAME", "30m").strip() or "30m"
    history_limit = _parse_int("HISTORY_LIMIT", default=250)
    local_live_loop = _parse_bool("LOCAL_LIVE_LOOP", default=False)
    poll_interval_seconds = _parse_int("POLL_INTERVAL_SECONDS", default=30)
    max_loop_iterations = _parse_int("MAX_LOOP_ITERATIONS", default=0)
    data_dir = os.getenv("DATA_DIR", "data").strip() or "data"
    paper_trade_size_usdc = _parse_float("PAPER_TRADE_SIZE_USDC", default=1000.0)
    fee_bps = _parse_float("FEE_BPS", default=0.0)
    demo_account_count = _parse_int("DEMO_ACCOUNT_COUNT", default=0)

    demo_accounts = _load_demo_accounts(demo_account_count)

    if bot_mode == "demo":
        if demo_account_count <= 0:
            raise ValueError("DEMO_ACCOUNT_COUNT must be greater than 0 when BOT_MODE=demo")
        if len(demo_accounts) != demo_account_count:
            raise ValueError("Loaded demo account count does not match DEMO_ACCOUNT_COUNT")

    return Settings(
        bot_mode=bot_mode,
        symbol=symbol,
        strategy_label=strategy_label,
        data_source=data_source,
        meteora_pool_address=meteora_pool_address,
        meteora_pool_name=meteora_pool_name,
        signal_timeframe=signal_timeframe,
        trend_timeframe=trend_timeframe,
        history_limit=history_limit,
        local_live_loop=local_live_loop,
        poll_interval_seconds=poll_interval_seconds,
        max_loop_iterations=max_loop_iterations,
        data_dir=data_dir,
        paper_trade_size_usdc=paper_trade_size_usdc,
        fee_bps=fee_bps,
        demo_account_count=demo_account_count,
        demo_accounts=tuple(demo_accounts),
    )


def _load_demo_accounts(count: int) -> list[DemoAccountConfig]:
    accounts: list[DemoAccountConfig] = []
    for index in range(1, count + 1):
        name = os.getenv(f"DEMO_{index}_NAME", "").strip()
        api_key = os.getenv(f"DEMO_{index}_API_KEY", "").strip()
        api_secret = os.getenv(f"DEMO_{index}_API_SECRET", "").strip()

        missing: list[str] = []
        if not name:
            missing.append(f"DEMO_{index}_NAME")
        if not api_key:
            missing.append(f"DEMO_{index}_API_KEY")
        if not api_secret:
            missing.append(f"DEMO_{index}_API_SECRET")

        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Demo account #{index} is incomplete. Missing: {joined}")

        accounts.append(
            DemoAccountConfig(
                index=index,
                name=name,
                api_key=api_key,
                api_secret=api_secret,
            )
        )
    return accounts


def _parse_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _parse_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default

    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean-like value")


def _parse_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc


def _load_env_file(env_path: Path) -> None:
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        os.environ.setdefault(key, value)
