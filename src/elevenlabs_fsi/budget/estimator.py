SAFETY_RESERVE = 2_000
AGENT_TURN_UPPER_BOUND = 700


class InsufficientCreditsError(Exception):
    pass


class CreditEstimator:
    def __init__(self, available: int):
        self._available = available

    def estimate_tts(self, text: str) -> int:
        return len(text)

    def estimate_agent_turn(self) -> int:
        return AGENT_TURN_UPPER_BOUND

    def check(self, required: int) -> None:
        spendable = self._available - SAFETY_RESERVE
        if required > spendable:
            raise InsufficientCreditsError(
                f"Cannot spend {required} chars: only {spendable} available above "
                f"safety reserve of {SAFETY_RESERVE} "
                f"(total available: {self._available})"
            )
