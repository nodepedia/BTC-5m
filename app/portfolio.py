from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.config import Settings
from app.models import MarketSnapshot, PositionSide, SignalAction


@dataclass
class PositionState:
    side: str = PositionSide.FLAT.value
    quantity: float = 0.0
    entry_price: float = 0.0
    entry_timestamp: int = 0


@dataclass
class AccountState:
    account_name: str
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    total_fees: float = 0.0
    trade_count: int = 0
    win_count: int = 0
    loss_count: int = 0
    position: PositionState | None = None

    def __post_init__(self) -> None:
        if self.position is None:
            self.position = PositionState()


class PortfolioTracker:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_dir = Path(settings.data_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.base_dir / "portfolio_state.json"
        self.trade_log_path = self.base_dir / "trade_history.jsonl"
        self.snapshot_log_path = self.base_dir / "pnl_history.jsonl"
        self.state = self._load_state()

    def process_signal(self, signal: SignalAction, snapshot: MarketSnapshot) -> list[str]:
        messages: list[str] = []
        for account in self._account_names():
            account_state = self.state.setdefault(account, AccountState(account_name=account))
            messages.extend(self._apply_signal(account_state, signal, snapshot))
            self._mark_to_market(account_state, snapshot.mark_price)

        self._append_snapshot(snapshot)
        self._save_state()
        return messages

    def summary_lines(self) -> list[str]:
        lines: list[str] = []
        for account in self._account_names():
            account_state = self.state.setdefault(account, AccountState(account_name=account))
            position = account_state.position or PositionState()
            lines.append(
                f"[PNL] account={account} side={position.side} "
                f"realized={account_state.realized_pnl:.2f} "
                f"unrealized={account_state.unrealized_pnl:.2f} "
                f"fees={account_state.total_fees:.2f} trades={account_state.trade_count}"
            )
        return lines

    def current_position_action(self) -> SignalAction:
        account_names = self._account_names()
        if not account_names:
            return SignalAction.HOLD

        account_state = self.state.get(account_names[0])
        if account_state is None or account_state.position is None:
            return SignalAction.HOLD

        if account_state.position.side == PositionSide.LONG.value:
            return SignalAction.ENTER_LONG
        if account_state.position.side == PositionSide.SHORT.value:
            return SignalAction.ENTER_SHORT
        return SignalAction.HOLD

    def _apply_signal(
        self,
        account_state: AccountState,
        signal: SignalAction,
        snapshot: MarketSnapshot,
    ) -> list[str]:
        messages: list[str] = []
        position = account_state.position or PositionState()
        entry_fee = self._fee_amount(self.settings.paper_trade_size_usdc)

        if signal == SignalAction.ENTER_LONG and position.side == PositionSide.FLAT.value:
            quantity = self.settings.paper_trade_size_usdc / snapshot.mark_price
            account_state.position = PositionState(
                side=PositionSide.LONG.value,
                quantity=quantity,
                entry_price=snapshot.mark_price,
                entry_timestamp=snapshot.candle_timestamp,
            )
            account_state.total_fees += entry_fee
            self._append_trade_event(
                {
                    "event": "enter_long",
                    "account_name": account_state.account_name,
                    "price": snapshot.mark_price,
                    "quantity": quantity,
                    "fee": entry_fee,
                    "timestamp": snapshot.candle_timestamp,
                    "symbol": snapshot.source_symbol,
                }
            )
            messages.append(
                f"[TRADE] account={account_state.account_name} enter_long "
                f"price={snapshot.mark_price:.2f} qty={quantity:.6f}"
            )
            return messages

        if signal == SignalAction.ENTER_SHORT and position.side == PositionSide.FLAT.value:
            quantity = self.settings.paper_trade_size_usdc / snapshot.mark_price
            account_state.position = PositionState(
                side=PositionSide.SHORT.value,
                quantity=quantity,
                entry_price=snapshot.mark_price,
                entry_timestamp=snapshot.candle_timestamp,
            )
            account_state.total_fees += entry_fee
            self._append_trade_event(
                {
                    "event": "enter_short",
                    "account_name": account_state.account_name,
                    "price": snapshot.mark_price,
                    "quantity": quantity,
                    "fee": entry_fee,
                    "timestamp": snapshot.candle_timestamp,
                    "symbol": snapshot.source_symbol,
                }
            )
            messages.append(
                f"[TRADE] account={account_state.account_name} enter_short "
                f"price={snapshot.mark_price:.2f} qty={quantity:.6f}"
            )
            return messages

        if signal == SignalAction.EXIT_LONG and position.side == PositionSide.LONG.value:
            pnl = (snapshot.mark_price - position.entry_price) * position.quantity
            exit_fee = self._fee_amount(snapshot.mark_price * position.quantity)
            realized = pnl - exit_fee
            account_state.realized_pnl += realized
            account_state.total_fees += exit_fee
            account_state.trade_count += 1
            if realized >= 0:
                account_state.win_count += 1
            else:
                account_state.loss_count += 1
            self._append_trade_event(
                {
                    "event": "exit_long",
                    "account_name": account_state.account_name,
                    "entry_price": position.entry_price,
                    "exit_price": snapshot.mark_price,
                    "quantity": position.quantity,
                    "gross_pnl": pnl,
                    "net_pnl": realized,
                    "fee": exit_fee,
                    "timestamp": snapshot.candle_timestamp,
                    "symbol": snapshot.source_symbol,
                }
            )
            account_state.position = PositionState()
            account_state.unrealized_pnl = 0.0
            messages.append(
                f"[TRADE] account={account_state.account_name} exit_long "
                f"price={snapshot.mark_price:.2f} pnl={realized:.2f}"
            )
            return messages

        if signal == SignalAction.EXIT_SHORT and position.side == PositionSide.SHORT.value:
            pnl = (position.entry_price - snapshot.mark_price) * position.quantity
            exit_fee = self._fee_amount(snapshot.mark_price * position.quantity)
            realized = pnl - exit_fee
            account_state.realized_pnl += realized
            account_state.total_fees += exit_fee
            account_state.trade_count += 1
            if realized >= 0:
                account_state.win_count += 1
            else:
                account_state.loss_count += 1
            self._append_trade_event(
                {
                    "event": "exit_short",
                    "account_name": account_state.account_name,
                    "entry_price": position.entry_price,
                    "exit_price": snapshot.mark_price,
                    "quantity": position.quantity,
                    "gross_pnl": pnl,
                    "net_pnl": realized,
                    "fee": exit_fee,
                    "timestamp": snapshot.candle_timestamp,
                    "symbol": snapshot.source_symbol,
                }
            )
            account_state.position = PositionState()
            account_state.unrealized_pnl = 0.0
            messages.append(
                f"[TRADE] account={account_state.account_name} exit_short "
                f"price={snapshot.mark_price:.2f} pnl={realized:.2f}"
            )
            return messages

        return messages

    def _mark_to_market(self, account_state: AccountState, mark_price: float) -> None:
        position = account_state.position or PositionState()
        if position.side == PositionSide.LONG.value:
            account_state.unrealized_pnl = (mark_price - position.entry_price) * position.quantity
            return
        if position.side == PositionSide.SHORT.value:
            account_state.unrealized_pnl = (position.entry_price - mark_price) * position.quantity
            return
        account_state.unrealized_pnl = 0.0

    def _account_names(self) -> list[str]:
        if self.settings.bot_mode == "demo":
            return [account.name for account in self.settings.demo_accounts]
        return ["dry_run_main"]

    def _load_state(self) -> dict[str, AccountState]:
        if not self.state_path.exists():
            return {}

        payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        state: dict[str, AccountState] = {}
        for account_name, data in payload.items():
            position_data = data.get("position", {}) or {}
            state[account_name] = AccountState(
                account_name=account_name,
                realized_pnl=float(data.get("realized_pnl", 0.0)),
                unrealized_pnl=float(data.get("unrealized_pnl", 0.0)),
                total_fees=float(data.get("total_fees", 0.0)),
                trade_count=int(data.get("trade_count", 0)),
                win_count=int(data.get("win_count", 0)),
                loss_count=int(data.get("loss_count", 0)),
                position=PositionState(
                    side=str(position_data.get("side", PositionSide.FLAT.value)),
                    quantity=float(position_data.get("quantity", 0.0)),
                    entry_price=float(position_data.get("entry_price", 0.0)),
                    entry_timestamp=int(position_data.get("entry_timestamp", 0)),
                ),
            )
        return state

    def _save_state(self) -> None:
        payload = {
            account_name: asdict(account_state)
            for account_name, account_state in self.state.items()
        }
        self.state_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _append_trade_event(self, payload: dict[str, object]) -> None:
        self._append_jsonl(self.trade_log_path, payload)

    def _append_snapshot(self, snapshot: MarketSnapshot) -> None:
        timestamp_iso = datetime.fromtimestamp(snapshot.candle_timestamp, UTC).isoformat()
        for account_name, account_state in self.state.items():
            position = account_state.position or PositionState()
            self._append_jsonl(
                self.snapshot_log_path,
                {
                    "timestamp": snapshot.candle_timestamp,
                    "timestamp_iso": timestamp_iso,
                    "account_name": account_name,
                    "symbol": snapshot.source_symbol,
                    "mark_price": snapshot.mark_price,
                    "position_side": position.side,
                    "realized_pnl": account_state.realized_pnl,
                    "unrealized_pnl": account_state.unrealized_pnl,
                    "total_fees": account_state.total_fees,
                    "trade_count": account_state.trade_count,
                },
            )

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True))
            handle.write("\n")

    def _fee_amount(self, notional: float) -> float:
        return notional * (self.settings.fee_bps / 10000.0)
