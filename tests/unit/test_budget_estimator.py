# Tests for SPEC-001 AC-006: credit pre-flight check
# Written before implementation (TDD red phase)
import pytest
from elevenlabs_fsi.budget.estimator import CreditEstimator, InsufficientCreditsError

SAFETY_RESERVE = 2_000


class TestCreditEstimator:
    def test_tts_cost_equals_character_count(self):
        estimator = CreditEstimator(available=9_813)
        assert estimator.estimate_tts("Hello world") == 11

    def test_tts_cost_empty_string_is_zero(self):
        estimator = CreditEstimator(available=9_813)
        assert estimator.estimate_tts("") == 0

    def test_check_passes_when_sufficient_budget(self):
        estimator = CreditEstimator(available=5_000)
        estimator.check(required=1_000)  # should not raise

    def test_check_raises_when_required_exceeds_available_minus_reserve(self):
        estimator = CreditEstimator(available=2_500)
        with pytest.raises(InsufficientCreditsError):
            estimator.check(required=600)  # 2500 - 600 = 1900 < 2000 reserve

    def test_check_raises_when_available_below_safety_reserve(self):
        estimator = CreditEstimator(available=1_999)
        with pytest.raises(InsufficientCreditsError):
            estimator.check(required=1)

    def test_check_passes_exactly_at_reserve_boundary(self):
        # available=2700, required=700 → remaining after = 2000 = exactly reserve → ok
        estimator = CreditEstimator(available=2_700)
        estimator.check(required=700)

    def test_error_message_includes_context(self):
        estimator = CreditEstimator(available=2_100)
        with pytest.raises(InsufficientCreditsError) as exc_info:
            estimator.check(required=200)
        assert "available" in str(exc_info.value).lower()
        assert "reserve" in str(exc_info.value).lower()

    def test_agent_turn_upper_bound_is_700(self):
        estimator = CreditEstimator(available=9_813)
        assert estimator.estimate_agent_turn() == 700
