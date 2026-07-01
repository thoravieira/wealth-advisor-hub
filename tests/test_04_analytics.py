"""
Phase 3 tests — DuckDB analytics service (port 8001).

ALL of these will FAIL until the analytics container is running.

Run:  pytest tests/test_04_analytics.py -v
"""
import httpx
import pytest

from conftest import ANALYTICS_URL

DEMO_CLIENT_IDS = [
    "ricardo", "fernando", "beatriz", "carlos", "ana", "pedro",
    "lucia", "roberto", "mariana", "paulo", "camila", "andre",
]


# ─── Connectivity ─────────────────────────────────────────────────────────────

class TestAnalyticsConnectivity:
    def test_analytics_health_returns_200(self, analytics):
        r = analytics.get("/health")
        assert r.status_code == 200, f"Analytics service not running. Got {r.status_code}"

    def test_analytics_health_has_status_ok(self, analytics):
        r = analytics.get("/health")
        assert r.json().get("status") == "ok"

    def test_analytics_health_reports_duckdb(self, analytics):
        r = analytics.get("/health")
        body = r.json()
        assert "duckdb" in body, f"Expected duckdb field in health response: {body}"


# ─── Clients ──────────────────────────────────────────────────────────────────

class TestClientsEndpoint:
    def test_returns_200(self, analytics):
        r = analytics.get("/clients")
        assert r.status_code == 200, f"Got {r.status_code}: {r.text}"

    def test_returns_list(self, analytics):
        r = analytics.get("/clients")
        body = r.json()
        assert isinstance(body, list), f"Expected list, got {type(body)}"

    def test_returns_12_demo_clients(self, analytics):
        r = analytics.get("/clients")
        assert len(r.json()) == 12, (
            f"Expected 12 clients (demo seed), got {len(r.json())}"
        )

    def test_client_has_required_fields(self, analytics):
        r = analytics.get("/clients")
        client = r.json()[0]
        required = {"client_id", "name", "aum", "risk_profile", "equity_pct",
                    "fixed_income_pct", "funds_pct", "cash_pct", "status"}
        missing = required - set(client.keys())
        assert not missing, f"Client record missing fields: {missing}"

    def test_get_client_by_id(self, analytics):
        r = analytics.get("/clients/ricardo")
        assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
        body = r.json()
        assert body["client_id"] == "ricardo"
        assert body["name"] == "Ricardo Tanaka"

    def test_unknown_client_returns_404(self, analytics):
        r = analytics.get("/clients/does_not_exist")
        assert r.status_code == 404

    @pytest.mark.parametrize("client_id", DEMO_CLIENT_IDS)
    def test_each_demo_client_exists(self, analytics, client_id):
        r = analytics.get(f"/clients/{client_id}")
        assert r.status_code == 200, (
            f"Demo client '{client_id}' not found in analytics service"
        )


# ─── Portfolio snapshots ───────────────────────────────────────────────────────

class TestPortfolioSnapshots:
    def test_get_snapshots_for_client(self, analytics):
        r = analytics.get("/clients/ricardo/snapshots")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)

    def test_snapshot_has_date_and_aum(self, analytics):
        r = analytics.get("/clients/ricardo/snapshots")
        if not r.json():
            pytest.skip("No snapshots seeded yet")
        snap = r.json()[0]
        assert "snapshot_date" in snap
        assert "aum" in snap


# ─── Recommendations ─────────────────────────────────────────────────────────

class TestRecommendations:
    def test_get_recommendations_returns_200(self, analytics):
        r = analytics.get("/recommendations")
        assert r.status_code == 200

    def test_get_recommendations_returns_list(self, analytics):
        r = analytics.get("/recommendations")
        assert isinstance(r.json(), list)

    def test_post_recommendation_persists(self, analytics):
        payload = {
            "client_id": "ricardo",
            "text": "Ricardo, considering your high equity exposure...",
            "status": "draft",
            "channel": "whatsapp",
        }
        r = analytics.post("/recommendations", json=payload)
        assert r.status_code in (200, 201), f"Got {r.status_code}: {r.text}"
        body = r.json()
        assert "recommendation_id" in body

    def test_recommendation_status_update(self, analytics):
        # Create a recommendation
        payload = {
            "client_id": "beatriz",
            "text": "Beatriz, your suitability document expires in 7 days.",
            "status": "draft",
            "channel": "whatsapp",
        }
        r = analytics.post("/recommendations", json=payload)
        rec_id = r.json()["recommendation_id"]

        # Update status to sent
        r2 = analytics.patch(f"/recommendations/{rec_id}", json={"status": "sent"})
        assert r2.status_code == 200

        # Verify
        r3 = analytics.get(f"/recommendations/{rec_id}")
        assert r3.json()["status"] == "sent"


# ─── Voice messages ──────────────────────────────────────────────────────────

class TestVoiceMessages:
    def test_get_voice_messages_returns_200(self, analytics):
        r = analytics.get("/voice-messages")
        assert r.status_code == 200

    def test_post_voice_message_persists(self, analytics):
        payload = {
            "client_id": "ricardo",
            "text": "Ricardo, we need to talk about your portfolio.",
            "status": "generated",
            "channel": "whatsapp",
        }
        r = analytics.post("/voice-messages", json=payload)
        assert r.status_code in (200, 201), f"Got {r.status_code}: {r.text}"
        assert "message_id" in r.json()


# ─── Alerts ──────────────────────────────────────────────────────────────────

class TestAlerts:
    def test_get_alerts_returns_200(self, analytics):
        r = analytics.get("/alerts")
        assert r.status_code == 200

    def test_alerts_is_list(self, analytics):
        assert isinstance(analytics.get("/alerts").json(), list)

    def test_active_alerts_filter(self, analytics):
        r = analytics.get("/alerts?status=active")
        assert r.status_code == 200
        for alert in r.json():
            assert alert["status"] == "active"
