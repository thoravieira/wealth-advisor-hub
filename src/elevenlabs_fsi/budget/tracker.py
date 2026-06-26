import json
from datetime import datetime, timezone
from pathlib import Path

WARN_THRESHOLD = 3_000
DEFAULT_LEDGER = Path(".budget.json")


class CreditTracker:
    def __init__(self, ledger_path: Path = DEFAULT_LEDGER, initial_available: int = 9_813):
        self._ledger_path = ledger_path
        self._state = self._load(initial_available)

    def _load(self, initial_available: int) -> dict:
        if self._ledger_path.exists():
            return json.loads(self._ledger_path.read_text())
        return {"remaining": initial_available, "log": []}

    def _save(self) -> None:
        self._ledger_path.write_text(json.dumps(self._state, indent=2))

    @property
    def remaining(self) -> int:
        return self._state["remaining"]

    @property
    def should_warn(self) -> bool:
        return self.remaining < WARN_THRESHOLD

    def log(self, feature: str, operation: str, chars: int) -> None:
        self._state["remaining"] -= chars
        self._state["log"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "feature": feature,
            "operation": operation,
            "chars": chars,
        })
        self._save()

    def get_log(self) -> list[dict]:
        return self._state["log"]
