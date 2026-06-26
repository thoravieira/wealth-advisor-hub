# Tests for SPEC-001 AC-003: knowledge base setup
from unittest.mock import MagicMock
import pytest
from elevenlabs_fsi.agent.knowledge_base import KnowledgeBaseManager


MOCK_KB_ID = "kb_test456"


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.conversational_ai.knowledge_base.create.return_value = MagicMock(
        id=MOCK_KB_ID
    )
    return client


@pytest.fixture
def kb_manager(mock_client):
    return KnowledgeBaseManager(client=mock_client)


class TestKnowledgeBaseManager:
    def test_create_returns_kb_id(self, kb_manager, mock_client):
        kb_id = kb_manager.create(name="FSI Products", content="CDB, LCI, LCA...")
        assert kb_id == MOCK_KB_ID

    def test_create_calls_api_with_name(self, kb_manager, mock_client):
        kb_manager.create(name="FSI Products", content="CDB, LCI...")
        call_kwargs = str(mock_client.conversational_ai.knowledge_base.create.call_args)
        assert "FSI Products" in call_kwargs

    def test_default_documents_are_defined(self, kb_manager):
        docs = kb_manager.get_default_documents()
        names = [d["name"] for d in docs]
        assert "products" in names
        assert "faq" in names
        assert "compliance" in names

    def test_default_documents_have_content(self, kb_manager):
        docs = kb_manager.get_default_documents()
        for doc in docs:
            assert len(doc["content"]) > 50, f"Document '{doc['name']}' content too short"

    def test_total_default_content_under_budget(self, kb_manager):
        docs = kb_manager.get_default_documents()
        total = sum(len(d["content"]) for d in docs)
        # KB upload doesn't cost TTS chars, but good to document size
        assert total < 10_000, "Default KB content unexpectedly large"
