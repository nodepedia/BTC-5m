from __future__ import annotations

from app.config import Settings
from app.models import SignalDecision


class DryRunExecutor:
    def execute(self, signal: SignalDecision) -> None:
        print(f"[DRY RUN] action={signal.action.value} reason={signal.reason}")


class DemoExecutor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def execute(self, signal: SignalDecision) -> None:
        for account in self.settings.demo_accounts:
            print(
                "[DEMO] "
                f"account={account.name} "
                f"action={signal.action.value} "
                f"reason={signal.reason}"
            )
