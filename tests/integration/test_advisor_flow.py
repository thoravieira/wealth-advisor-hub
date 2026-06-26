# Integration tests — require real ELEVENLABS_API_KEY
# Run with: pytest tests/integration/ -v
# WARNING: These tests consume real API characters. Each run costs ~700 chars.
import os
import pytest
from elevenlabs_fsi.agent.advisor_agent import AdvisorAgent
from elevenlabs_fsi.agent.knowledge_base import KnowledgeBaseManager
from elevenlabs_fsi.budget.tracker import CreditTracker
from elevenlabs_fsi.budget.estimator import CreditEstimator
from elevenlabs import ElevenLabs


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def api_key():
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        pytest.skip("ELEVENLABS_API_KEY not set")
    return key


@pytest.fixture(scope="module")
def client(api_key):
    return ElevenLabs(api_key=api_key)


@pytest.fixture(scope="module")
def tracker():
    return CreditTracker(initial_available=9_813)


@pytest.fixture(scope="module")
def estimator(tracker):
    return CreditEstimator(available=tracker.remaining)


class TestAdvisorAgentIntegration:
    def test_get_or_create_returns_agent_id(self, client, tracker, estimator):
        advisor = AdvisorAgent(client=client)
        agent_id = advisor.get_or_create()
        assert agent_id is not None
        assert agent_id.startswith("agent_")

    def test_get_or_create_is_idempotent(self, client, tracker, estimator):
        advisor = AdvisorAgent(client=client)
        id_1 = advisor.get_or_create()
        id_2 = advisor.get_or_create()
        assert id_1 == id_2

    def test_knowledge_base_creation(self, client, tracker):
        kb_manager = KnowledgeBaseManager(client=client)
        docs = kb_manager.get_default_documents()
        kb_id = kb_manager.create(name="FSI Products Test", content=docs[0]["content"])
        assert kb_id is not None
