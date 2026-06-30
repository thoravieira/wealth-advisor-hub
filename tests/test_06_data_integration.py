"""
TDD — Data Layer Integration

Documents what should be true when the full 4-container stack is running
with seeded data. Tests are grouped into:

  - Baseline (must pass before implementation)
  - Target (fail before implementation, pass after)

Run after `docker compose up --build` with a fresh postgres volume.
"""

import re
import psycopg2
import pytest
from pathlib import Path

from conftest import BACKEND_URL, ANALYTICS_URL, POSTGRES_DSN


# ─── Baseline: endpoints already work ────────────────────────────────────────

class TestAnalyticsClientsBaseline:
    """Analytics service already returns all 12 clients — no changes needed."""

    def test_clients_returns_list(self, analytics):
        r = analytics.get("/clients")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_clients_count_is_12(self, analytics):
        r = analytics.get("/clients")
        assert len(r.json()) == 12

    def test_client_has_required_fields(self, analytics):
        r = analytics.get("/clients/ricardo")
        assert r.status_code == 200
        c = r.json()
        for field in ("client_id", "name", "vip", "aum", "equity_pct",
                      "fixed_income_pct", "funds_pct", "cash_pct", "status"):
            assert field in c, f"Missing field: {field}"

    def test_ricardo_allocation_matches_demo(self, analytics):
        c = analytics.get("/clients/ricardo").json()
        assert c["equity_pct"] == 71
        assert c["fixed_income_pct"] == 14

    def test_beatriz_client_exists(self, analytics):
        r = analytics.get("/clients/beatriz")
        assert r.status_code == 200

    def test_backend_proxies_clients(self, backend):
        r = backend.get("/clients")
        assert r.status_code == 200
        assert len(r.json()) == 12

    def test_backend_proxies_single_client(self, backend):
        r = backend.get("/clients/ricardo")
        assert r.status_code == 200
        c = r.json()
        assert c["client_id"] == "ricardo"

    def test_memory_endpoint_exists(self, backend):
        r = backend.get("/memory/long/nonexistent")
        assert r.status_code == 200
        assert r.json() == []


# ─── Target: postgres seed data ───────────────────────────────────────────────

class TestPostgresSeedData:
    """
    agent_memory_long must be pre-seeded by db/init.sql.
    These tests FAIL before the seed INSERT statements are added.
    They PASS after `docker compose down -v && docker compose up --build`.
    """

    def _pg(self):
        return psycopg2.connect(POSTGRES_DSN)

    def test_seed_has_rows(self):
        conn = self._pg()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM agent_memory_long WHERE is_active = TRUE")
        count = cur.fetchone()[0]
        conn.close()
        assert count >= 5, f"Expected at least 5 seed facts, got {count}"

    def test_ricardo_has_risk_signal(self):
        conn = self._pg()
        cur = conn.cursor()
        cur.execute(
            "SELECT fact FROM agent_memory_long WHERE client_id = %s AND category = %s AND is_active = TRUE",
            ("ricardo", "risk_signal")
        )
        rows = cur.fetchall()
        conn.close()
        assert rows, "No risk_signal fact seeded for Ricardo"
        assert any("71" in row[0] or "withdrawal" in row[0].lower() or "resgate" in row[0].lower() for row in rows)

    def test_beatriz_has_suitability_fact(self):
        conn = self._pg()
        cur = conn.cursor()
        cur.execute(
            "SELECT fact FROM agent_memory_long WHERE client_id = %s AND is_active = TRUE",
            ("beatriz",)
        )
        rows = cur.fetchall()
        conn.close()
        assert rows, "No seed facts for Beatriz"
        combined = " ".join(r[0] for r in rows).lower()
        assert "suitability" in combined or "suit" in combined

    def test_memory_endpoint_returns_seed_for_ricardo(self, backend):
        r = backend.get("/memory/long/ricardo")
        assert r.status_code == 200
        facts = r.json()
        assert len(facts) >= 1, "Expected at least 1 seed fact for Ricardo"
        categories = {f["category"] for f in facts}
        assert categories & {"risk_signal", "life_event", "preference", "objective"}

    def test_memory_fact_has_correct_schema(self, backend):
        r = backend.get("/memory/long/ricardo")
        f = r.json()[0]
        for field in ("id", "client_id", "category", "fact", "confidence", "created_at"):
            assert field in f, f"Missing field: {field}"

    def test_seed_covers_multiple_clients(self):
        conn = self._pg()
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT client_id FROM agent_memory_long WHERE is_active = TRUE"
        )
        clients = {row[0] for row in cur.fetchall()}
        conn.close()
        assert len(clients) >= 4, f"Expected seed facts for at least 4 clients, got {clients}"


# ─── Target: cockpit uses analytics data ─────────────────────────────────────

class TestCockpitUsesAnalyticsData:
    """
    cockpit.html must call the backend /clients endpoint on load and
    store results in analyticsClients state. These tests inspect the
    HTML source and JS for the integration code.

    FAIL before cockpit.html is updated.
    PASS after the _initData() method is added.
    """

    COCKPIT = Path(__file__).parent.parent / "front" / "cockpit.html"

    def _src(self):
        return self.COCKPIT.read_text()

    def test_cockpit_has_analytics_clients_state(self):
        src = self._src()
        assert "analyticsClients" in src, \
            "cockpit.html missing analyticsClients in state"

    def test_cockpit_has_memory_facts_state(self):
        src = self._src()
        assert "memoryFacts" in src, \
            "cockpit.html missing memoryFacts in state"

    def test_cockpit_has_init_data_method(self):
        src = self._src()
        assert "_initData" in src, \
            "cockpit.html missing _initData() method"

    def test_cockpit_has_fetch_memory_method(self):
        src = self._src()
        assert "_fetchMemory" in src, \
            "cockpit.html missing _fetchMemory() method"

    def test_cockpit_fetches_clients_endpoint(self):
        src = self._src()
        assert re.search(r"fetch\(['\"].*?/clients['\"]", src) or "/clients'" in src or '/clients"' in src, \
            "cockpit.html does not fetch /clients endpoint"

    def test_cockpit_fetches_memory_long_endpoint(self):
        src = self._src()
        assert "memory/long" in src, \
            "cockpit.html does not call /memory/long endpoint"

    def test_cockpit_memory_section_in_client_detail(self):
        src = self._src()
        assert "memoryList" in src, \
            "cockpit.html missing memoryList in client detail view"

    def test_sofia_banner_removed_from_conversations(self):
        src = self._src()
        assert "Sofia live call panel" not in src, \
            "Sofia live call panel banner was not removed from Conversations view"


# ─── Target: analytics data visible in cockpit response ──────────────────────

class TestLiveDataFlow:
    """
    End-to-end: analytics data flows through backend proxy and
    is verifiable via standard HTTP calls. These PASS before cockpit
    changes (they test the backend+analytics stack, not the frontend JS).
    Listed here to document the full data path.
    """

    def test_analytics_and_backend_agree_on_ricardo_equity(self, analytics, backend):
        an = analytics.get("/clients/ricardo").json()
        bk = backend.get("/clients/ricardo").json()
        assert an["equity_pct"] == bk["equity_pct"]

    def test_analytics_client_ids_match_demo_clients(self, analytics):
        """All demo client IDs in analytics must match the cockpit's hardcoded list."""
        demo_ids = {
            "ricardo", "fernando", "beatriz", "carlos", "ana", "pedro",
            "lucia", "roberto", "mariana", "paulo", "camila", "andre"
        }
        an_ids = {c["client_id"] for c in analytics.get("/clients").json()}
        assert demo_ids == an_ids, f"ID mismatch: {demo_ids.symmetric_difference(an_ids)}"
