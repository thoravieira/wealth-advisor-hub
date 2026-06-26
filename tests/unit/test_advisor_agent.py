# Tests for SPEC-001: Investment Advisor Agent
# AC-001: no duplicate creation
# AC-002: Portuguese language
# AC-004: greets client by name
from unittest.mock import MagicMock, patch
import pytest
from elevenlabs_fsi.agent.advisor_agent import AdvisorAgent, AgentAlreadyExistsError


MOCK_AGENT_ID = "agent_test123"


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.conversational_ai.agents.get_all.return_value = MagicMock(agents=[])
    client.conversational_ai.agents.create.return_value = MagicMock(
        agent_id=MOCK_AGENT_ID
    )
    return client


@pytest.fixture
def advisor(mock_client):
    return AdvisorAgent(client=mock_client)


class TestAdvisorAgentCreation:
    def test_create_returns_agent_id(self, advisor, mock_client):
        agent_id = advisor.get_or_create()
        assert agent_id == MOCK_AGENT_ID

    def test_create_calls_api_once(self, advisor, mock_client):
        advisor.get_or_create()
        mock_client.conversational_ai.agents.create.assert_called_once()

    def test_get_or_create_returns_existing_agent_without_creating(
        self, mock_client
    ):
        # MagicMock reserves `name` as a constructor kwarg — set it post-init
        existing = MagicMock(agent_id=MOCK_AGENT_ID)
        existing.name = "Assessor Virtual XP"
        mock_client.conversational_ai.agents.get_all.return_value = MagicMock(
            agents=[existing]
        )
        advisor = AdvisorAgent(client=mock_client)
        agent_id = advisor.get_or_create()
        mock_client.conversational_ai.agents.create.assert_not_called()
        assert agent_id == MOCK_AGENT_ID

    def test_agent_name_is_fixed(self, advisor, mock_client):
        advisor.get_or_create()
        call_kwargs = mock_client.conversational_ai.agents.create.call_args
        assert "Assessor Virtual XP" in str(call_kwargs)

    def test_agent_language_is_portuguese(self, advisor, mock_client):
        advisor.get_or_create()
        call_kwargs = str(mock_client.conversational_ai.agents.create.call_args)
        assert "pt" in call_kwargs

    def test_first_message_greets_in_portuguese(self, advisor, mock_client):
        advisor.get_or_create()
        call_kwargs = str(mock_client.conversational_ai.agents.create.call_args)
        assert "Olá" in call_kwargs or "olá" in call_kwargs


class TestAdvisorAgentSystemPrompt:
    def test_system_prompt_references_compliance_disclaimer(self, advisor):
        prompt = advisor.build_system_prompt()
        assert "rentabilidade" in prompt.lower() or "garantida" in prompt.lower()

    def test_system_prompt_includes_product_routing_rules(self, advisor):
        prompt = advisor.build_system_prompt()
        assert "liquidez" in prompt.lower() or "CDB" in prompt

    def test_system_prompt_ends_with_human_escalation_offer(self, advisor):
        prompt = advisor.build_system_prompt()
        assert "assessor" in prompt.lower() or "especialista" in prompt.lower()
