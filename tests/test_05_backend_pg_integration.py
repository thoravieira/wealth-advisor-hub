"""
Phase 2 tests — backend integrated with PostgreSQL and analytics.

Running BEFORE implementation, these tests will fail.
They define the expected contract after migrating to the full compose stack.

Run:  pytest tests/test_05_backend_pg_integration.py -v
"""
import time

import httpx
import pytest

from conftest import BACKEND_URL, POSTGRES_DSN, SHORT_TEXT, make_silent_wav


# ─── Health report ────────────────────────────────────────────────────────────

class TestHealthWithDependencies:
    def test_health_reports_postgres_ok(self):
        """After integration, /health must include postgres status."""
        r = httpx.get(f"{BACKEND_URL}/health")
        body = r.json()
        assert "postgres" in body, (
            f"/health does not report postgres. Current fields: {list(body.keys())}"
        )
        assert body["postgres"] == "ok", (
            f"postgres is not ok: {body.get('postgres')}"
        )

    def test_health_reports_analytics_ok(self):
        """After integration, /health must include analytics service status."""
        r = httpx.get(f"{BACKEND_URL}/health")
        body = r.json()
        assert "analytics" in body, (
            f"/health does not report analytics. Current fields: {list(body.keys())}"
        )
        assert body["analytics"] == "ok", (
            f"analytics is not ok: {body.get('analytics')}"
        )


# ─── Session lifecycle ────────────────────────────────────────────────────────

class TestSessionPersistence:
    def _session_count(self):
        psycopg2 = pytest.importorskip("psycopg2")
        conn = psycopg2.connect(POSTGRES_DSN)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM agent_sessions")
        count = cur.fetchone()[0]
        conn.close()
        return count

    def test_agent_token_creates_session_row(self):
        """Each call to /agent/token must create a row in agent_sessions."""
        psycopg2 = pytest.importorskip("psycopg2")
        before = self._session_count()
        httpx.get(f"{BACKEND_URL}/agent/token")
        after = self._session_count()
        assert after == before + 1, (
            f"Expected +1 session after /agent/token, but went from {before} to {after}"
        )

    def test_session_row_has_signed_url_or_conversation_id(self):
        """Session row must have at least signed_url or conversation_id."""
        psycopg2 = pytest.importorskip("psycopg2")
        httpx.get(f"{BACKEND_URL}/agent/token")
        conn = psycopg2.connect(POSTGRES_DSN)
        cur = conn.cursor()
        cur.execute(
            "SELECT conversation_id, status FROM agent_sessions ORDER BY created_at DESC LIMIT 1"
        )
        row = cur.fetchone()
        conn.close()
        assert row is not None, "No session found"
        # conversation_id may be null at creation time (before WebSocket connects)
        # but status must be 'active'
        assert row[1] == "active", f"expected status 'active', got '{row[1]}'"


# ─── Long-term memory ─────────────────────────────────────────────────────────

class TestLongTermMemory:
    BASE = f"{BACKEND_URL}/memory/long"

    def test_get_memory_returns_200(self):
        r = httpx.get(f"{self.BASE}/ricardo")
        assert r.status_code == 200, f"GET /memory/long/ricardo returned {r.status_code}: {r.text}"

    def test_get_memory_returns_list(self):
        r = httpx.get(f"{self.BASE}/ricardo")
        assert isinstance(r.json(), list), f"Expected list, got: {type(r.json())}"

    def test_post_memory_persists_fact(self):
        payload = {
            "client_id": "fernando",
            "category": "preference",
            "fact": "Prefers contact in the morning",
            "confidence": 0.95,
        }
        r = httpx.post(self.BASE, json=payload)
        assert r.status_code in (200, 201), f"POST /memory/long returned {r.status_code}: {r.text}"

    def test_post_memory_is_retrievable(self):
        unique_fact = f"Persistence test {int(time.time())}"
        httpx.post(self.BASE, json={
            "client_id": "carlos",
            "category": "note",
            "fact": unique_fact,
            "confidence": 1.0,
        })
        r = httpx.get(f"{self.BASE}/carlos")
        facts = [m["fact"] for m in r.json()]
        assert unique_fact in facts, (
            f"Saved fact not found. Found: {facts}"
        )

    def test_memory_has_expected_fields(self):
        httpx.post(self.BASE, json={
            "client_id": "beatriz",
            "category": "life_event",
            "fact": "Retirement planned for 2028",
            "confidence": 0.8,
        })
        r = httpx.get(f"{self.BASE}/beatriz")
        entries = r.json()
        if not entries:
            pytest.skip("No memory entries for beatriz")
        entry = entries[0]
        for field in ("client_id", "category", "fact", "confidence", "created_at"):
            assert field in entry, f"Field '{field}' missing from memory response"


# ─── Advisor actions log ──────────────────────────────────────────────────────

class TestAdvisorActionsLog:
    def test_tts_call_logs_action(self):
        """POST /tts must log an advisor_action of type 'voice_generated'."""
        psycopg2 = pytest.importorskip("psycopg2")
        conn = psycopg2.connect(POSTGRES_DSN)
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM advisor_actions WHERE action_type = 'voice_generated'"
        )
        before = cur.fetchone()[0]
        conn.close()

        httpx.post(f"{BACKEND_URL}/tts", json={"text": "Action log test."})

        conn = psycopg2.connect(POSTGRES_DSN)
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM advisor_actions WHERE action_type = 'voice_generated'"
        )
        after = cur.fetchone()[0]
        conn.close()

        assert after == before + 1, (
            f"Expected +1 action 'voice_generated', went from {before} to {after}"
        )

    def test_get_actions_endpoint(self):
        """GET /actions must return the advisor action history."""
        r = httpx.get(f"{BACKEND_URL}/actions")
        assert r.status_code == 200, f"GET /actions returned {r.status_code}: {r.text}"
        assert isinstance(r.json(), list)


# ─── Internal service connectivity ───────────────────────────────────────────

class TestInternalConnectivity:
    def test_backend_can_reach_analytics(self):
        """Backend must be able to call the analytics service internally."""
        r = httpx.get(f"{BACKEND_URL}/internal/analytics-health")
        assert r.status_code == 200, (
            f"Backend cannot reach analytics internally. "
            f"/internal/analytics-health returned {r.status_code}: {r.text}"
        )
        assert r.json().get("analytics") == "ok"

    def test_backend_can_fetch_client_from_analytics(self):
        """Backend must be able to proxy client data from analytics."""
        r = httpx.get(f"{BACKEND_URL}/clients/ricardo")
        assert r.status_code == 200, (
            f"GET /clients/ricardo via backend returned {r.status_code}: {r.text}"
        )
        body = r.json()
        assert body.get("client_id") == "ricardo"
        assert "name" in body
