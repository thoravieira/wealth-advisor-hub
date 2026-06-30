"""
Phase 2 tests — PostgreSQL memory layer.

ALL of these will FAIL until Phase 1 (docker-compose infra) and
Phase 2 (backend integration) are implemented.

Run:  pytest tests/test_03_postgres.py -v
"""
import httpx
import pytest

from conftest import BACKEND_URL, POSTGRES_DSN


# ─── Connectivity ─────────────────────────────────────────────────────────────

class TestPostgresConnectivity:
    def test_postgres_is_reachable(self):
        """PostgreSQL must be reachable at localhost:5432."""
        import socket
        try:
            s = socket.create_connection(("localhost", 5432), timeout=3)
            s.close()
        except OSError as e:
            pytest.fail(f"PostgreSQL not reachable on port 5432: {e}")

    def test_backend_health_includes_postgres_status(self):
        """After Phase 2, /health should report postgres connectivity."""
        r = httpx.get(f"{BACKEND_URL}/health")
        body = r.json()
        assert "postgres" in body, (
            f"/health doesn't include postgres status yet. Got: {body}"
        )
        assert body["postgres"] == "ok", (
            f"postgres status is not 'ok': {body.get('postgres')}"
        )


# ─── Schema ───────────────────────────────────────────────────────────────────

class TestPostgresSchema:
    """Verify the expected tables exist after init.sql runs."""

    @pytest.fixture(scope="class")
    def conn(self):
        psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2 not installed")
        try:
            conn = psycopg2.connect(POSTGRES_DSN)
            yield conn
            conn.close()
        except Exception as e:
            pytest.fail(f"Cannot connect to PostgreSQL: {e}")

    def _tables(self, conn):
        cur = conn.cursor()
        cur.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        )
        return {row[0] for row in cur.fetchall()}

    def test_agent_sessions_table_exists(self, conn):
        assert "agent_sessions" in self._tables(conn)

    def test_agent_memory_short_table_exists(self, conn):
        assert "agent_memory_short" in self._tables(conn)

    def test_agent_memory_long_table_exists(self, conn):
        assert "agent_memory_long" in self._tables(conn)

    def test_advisor_actions_table_exists(self, conn):
        assert "advisor_actions" in self._tables(conn)


# ─── Session lifecycle via API ────────────────────────────────────────────────

class TestSessionLifecycle:
    def test_get_token_creates_session(self):
        """Calling /agent/token must write a row to agent_sessions."""
        psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2 not installed")
        conn = psycopg2.connect(POSTGRES_DSN)

        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM agent_sessions")
        before = cur.fetchone()[0]

        httpx.get(f"{BACKEND_URL}/agent/token")

        cur.execute("SELECT COUNT(*) FROM agent_sessions")
        after = cur.fetchone()[0]
        conn.close()

        assert after == before + 1, (
            f"Expected 1 new session row after /agent/token, "
            f"count went from {before} to {after}"
        )

    def test_session_row_has_conversation_id(self):
        """The session row must store the ElevenLabs conversation_id."""
        psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2 not installed")
        conn = psycopg2.connect(POSTGRES_DSN)
        cur = conn.cursor()
        cur.execute(
            "SELECT conversation_id FROM agent_sessions ORDER BY created_at DESC LIMIT 1"
        )
        row = cur.fetchone()
        conn.close()
        assert row is not None, "No session row found"
        assert row[0] is not None, "conversation_id is NULL"


# ─── Memory endpoints ─────────────────────────────────────────────────────────

class TestMemoryAPI:
    def test_get_memory_long_returns_200(self):
        r = httpx.get(f"{BACKEND_URL}/memory/long/ricardo")
        assert r.status_code == 200, f"Got {r.status_code}: {r.text}"

    def test_get_memory_long_returns_list(self):
        r = httpx.get(f"{BACKEND_URL}/memory/long/ricardo")
        body = r.json()
        assert isinstance(body, list), f"Expected list, got: {type(body)}"

    def test_post_memory_long_persists(self):
        payload = {
            "client_id": "ricardo",
            "category": "preference",
            "fact": "Prefers morning calls",
            "confidence": 0.9,
        }
        r = httpx.post(f"{BACKEND_URL}/memory/long", json=payload)
        assert r.status_code in (200, 201), f"Got {r.status_code}: {r.text}"

        # Verify it was stored
        r2 = httpx.get(f"{BACKEND_URL}/memory/long/ricardo")
        facts = [m["fact"] for m in r2.json()]
        assert "Prefers morning calls" in facts, (
            f"Saved fact not found in memory. Got: {facts}"
        )
