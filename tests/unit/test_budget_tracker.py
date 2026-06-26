# Tests for SPEC-001 AC-007: credit usage logging
import json
import pytest
from pathlib import Path
from elevenlabs_fsi.budget.tracker import CreditTracker


@pytest.fixture
def tracker(tmp_path):
    ledger = tmp_path / ".budget.json"
    return CreditTracker(ledger_path=ledger, initial_available=9_813)


class TestCreditTracker:
    def test_initial_remaining_equals_configured_value(self, tracker):
        assert tracker.remaining == 9_813

    def test_log_usage_reduces_remaining(self, tracker):
        tracker.log(feature="SPEC-001", operation="agent_turn", chars=700)
        assert tracker.remaining == 9_113

    def test_log_usage_multiple_times_accumulates(self, tracker):
        tracker.log(feature="SPEC-001", operation="agent_turn", chars=700)
        tracker.log(feature="SPEC-001", operation="agent_turn", chars=650)
        assert tracker.remaining == 8_463

    def test_log_persists_to_ledger_file(self, tracker, tmp_path):
        tracker.log(feature="SPEC-001", operation="tts", chars=200)
        ledger = tmp_path / ".budget.json"
        data = json.loads(ledger.read_text())
        assert data["remaining"] == 9_613
        assert len(data["log"]) == 1

    def test_log_entry_contains_required_fields(self, tracker):
        tracker.log(feature="SPEC-001", operation="tts", chars=200)
        entry = tracker.get_log()[0]
        assert "timestamp" in entry
        assert entry["feature"] == "SPEC-001"
        assert entry["operation"] == "tts"
        assert entry["chars"] == 200

    def test_tracker_loads_existing_ledger(self, tmp_path):
        ledger = tmp_path / ".budget.json"
        ledger.write_text(json.dumps({"remaining": 5_000, "log": []}))
        tracker = CreditTracker(ledger_path=ledger, initial_available=9_813)
        assert tracker.remaining == 5_000

    def test_warn_threshold_at_3000_chars(self, tracker):
        tracker.log(feature="SPEC-001", operation="agent_turn", chars=6_900)
        assert tracker.should_warn is True

    def test_no_warn_above_3000_chars(self, tracker):
        tracker.log(feature="SPEC-001", operation="agent_turn", chars=100)
        assert tracker.should_warn is False
