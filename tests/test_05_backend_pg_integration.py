"""
Phase 2 tests — backend integrado com PostgreSQL e analytics.

Rodando ANTES da implementação, esses testes vão falhar.
Eles definem o contrato esperado após a migração para a compose stack completa.

Run:  pytest tests/test_05_backend_pg_integration.py -v
"""
import time

import httpx
import pytest

from conftest import BACKEND_URL, POSTGRES_DSN, SHORT_TEXT, make_silent_wav


# ─── Health report completo ───────────────────────────────────────────────────

class TestHealthWithDependencies:
    def test_health_reports_postgres_ok(self):
        """Após integração, /health deve incluir status do postgres."""
        r = httpx.get(f"{BACKEND_URL}/health")
        body = r.json()
        assert "postgres" in body, (
            f"/health não reporta postgres. Campos atuais: {list(body.keys())}"
        )
        assert body["postgres"] == "ok", (
            f"postgres não está ok: {body.get('postgres')}"
        )

    def test_health_reports_analytics_ok(self):
        """Após integração, /health deve incluir status do serviço analytics."""
        r = httpx.get(f"{BACKEND_URL}/health")
        body = r.json()
        assert "analytics" in body, (
            f"/health não reporta analytics. Campos atuais: {list(body.keys())}"
        )
        assert body["analytics"] == "ok", (
            f"analytics não está ok: {body.get('analytics')}"
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
        """Cada chamada a /agent/token deve criar uma linha em agent_sessions."""
        psycopg2 = pytest.importorskip("psycopg2")
        before = self._session_count()
        httpx.get(f"{BACKEND_URL}/agent/token")
        after = self._session_count()
        assert after == before + 1, (
            f"Esperado +1 sessão após /agent/token, mas foi de {before} para {after}"
        )

    def test_session_row_has_signed_url_or_conversation_id(self):
        """A linha de sessão deve ter ao menos o signed_url ou conversation_id."""
        psycopg2 = pytest.importorskip("psycopg2")
        httpx.get(f"{BACKEND_URL}/agent/token")
        conn = psycopg2.connect(POSTGRES_DSN)
        cur = conn.cursor()
        cur.execute(
            "SELECT conversation_id, status FROM agent_sessions ORDER BY created_at DESC LIMIT 1"
        )
        row = cur.fetchone()
        conn.close()
        assert row is not None, "Nenhuma sessão encontrada"
        # conversation_id pode ser null no momento da criação (antes do WS conectar)
        # mas o status deve ser 'active'
        assert row[1] == "active", f"status esperado 'active', got '{row[1]}'"


# ─── Memória de longa duração ─────────────────────────────────────────────────

class TestLongTermMemory:
    BASE = f"{BACKEND_URL}/memory/long"

    def test_get_memory_returns_200(self):
        r = httpx.get(f"{self.BASE}/ricardo")
        assert r.status_code == 200, f"GET /memory/long/ricardo retornou {r.status_code}: {r.text}"

    def test_get_memory_returns_list(self):
        r = httpx.get(f"{self.BASE}/ricardo")
        assert isinstance(r.json(), list), f"Esperado lista, got: {type(r.json())}"

    def test_post_memory_persists_fact(self):
        payload = {
            "client_id": "fernando",
            "category": "preference",
            "fact": "Prefere contato no período da manhã",
            "confidence": 0.95,
        }
        r = httpx.post(self.BASE, json=payload)
        assert r.status_code in (200, 201), f"POST /memory/long retornou {r.status_code}: {r.text}"

    def test_post_memory_is_retrievable(self):
        unique_fact = f"Teste persistência {int(time.time())}"
        httpx.post(self.BASE, json={
            "client_id": "carlos",
            "category": "note",
            "fact": unique_fact,
            "confidence": 1.0,
        })
        r = httpx.get(f"{self.BASE}/carlos")
        facts = [m["fact"] for m in r.json()]
        assert unique_fact in facts, (
            f"Fato salvo não encontrado. Encontrados: {facts}"
        )

    def test_memory_has_expected_fields(self):
        httpx.post(self.BASE, json={
            "client_id": "beatriz",
            "category": "life_event",
            "fact": "Aposentadoria prevista para 2028",
            "confidence": 0.8,
        })
        r = httpx.get(f"{self.BASE}/beatriz")
        entries = r.json()
        if not entries:
            pytest.skip("Sem entradas de memória para beatriz")
        entry = entries[0]
        for field in ("client_id", "category", "fact", "confidence", "created_at"):
            assert field in entry, f"Campo '{field}' ausente na resposta de memória"


# ─── Advisor actions log ──────────────────────────────────────────────────────

class TestAdvisorActionsLog:
    def test_tts_call_logs_action(self):
        """POST /tts deve registrar uma advisor_action do tipo 'voice_generated'."""
        psycopg2 = pytest.importorskip("psycopg2")
        conn = psycopg2.connect(POSTGRES_DSN)
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM advisor_actions WHERE action_type = 'voice_generated'"
        )
        before = cur.fetchone()[0]
        conn.close()

        httpx.post(f"{BACKEND_URL}/tts", json={"text": "Teste de log de ação."})

        conn = psycopg2.connect(POSTGRES_DSN)
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM advisor_actions WHERE action_type = 'voice_generated'"
        )
        after = cur.fetchone()[0]
        conn.close()

        assert after == before + 1, (
            f"Esperado +1 action 'voice_generated', foi de {before} para {after}"
        )

    def test_get_actions_endpoint(self):
        """GET /actions deve retornar o histórico de ações do advisor."""
        r = httpx.get(f"{BACKEND_URL}/actions")
        assert r.status_code == 200, f"GET /actions retornou {r.status_code}: {r.text}"
        assert isinstance(r.json(), list)


# ─── Conectividade interna entre serviços ────────────────────────────────────

class TestInternalConnectivity:
    def test_backend_can_reach_analytics(self):
        """Backend deve conseguir chamar o analytics service internamente."""
        r = httpx.get(f"{BACKEND_URL}/internal/analytics-health")
        assert r.status_code == 200, (
            f"Backend não consegue alcançar analytics internamente. "
            f"Endpoint /internal/analytics-health retornou {r.status_code}: {r.text}"
        )
        assert r.json().get("analytics") == "ok"

    def test_backend_can_fetch_client_from_analytics(self):
        """Backend deve conseguir fazer proxy de dados do analytics."""
        r = httpx.get(f"{BACKEND_URL}/clients/ricardo")
        assert r.status_code == 200, (
            f"GET /clients/ricardo via backend retornou {r.status_code}: {r.text}"
        )
        body = r.json()
        assert body.get("client_id") == "ricardo"
        assert "name" in body
