AGENT_NAME = "Assessor Virtual XP"
MODEL_ID = "eleven_flash_v2_5"
LANGUAGE = "pt"
FIRST_MESSAGE = "Olá! Sou seu assessor virtual. Como posso ajudá-lo com seus investimentos hoje?"


class AgentAlreadyExistsError(Exception):
    pass


class AdvisorAgent:
    def __init__(self, client):
        self._client = client

    def get_or_create(self) -> str:
        existing_id = self._find_existing()
        if existing_id:
            return existing_id
        return self._create()

    def _find_existing(self) -> str | None:
        response = self._client.conversational_ai.agents.get_all()
        for agent in response.agents:
            if agent.name == AGENT_NAME:
                return agent.agent_id
        return None

    def _create(self) -> str:
        result = self._client.conversational_ai.agents.create(
            name=AGENT_NAME,
            conversation_config={
                "agent": {
                    "language": LANGUAGE,
                    "first_message": FIRST_MESSAGE,
                    "prompt": {
                        "prompt": self.build_system_prompt(),
                        "llm": "gemini-2.0-flash-001",
                    },
                },
                "tts": {
                    "model_id": MODEL_ID,
                    "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Sarah — profissional, confiante
                },
            },
        )
        return result.agent_id

    def build_system_prompt(self) -> str:
        return (
            "Você é um assessor de investimentos virtual, empático, objetivo e consultivo.\n\n"
            "Seu papel é ajudar clientes a entender opções de investimento adequadas ao seu perfil "
            "e momento de vida, sempre dentro das normas regulatórias.\n\n"
            "REGRAS OBRIGATÓRIAS:\n"
            "- Nunca prometa rentabilidade garantida ou retornos futuros.\n"
            "- Ao cliente mencionar preocupação com liquidez ou emergências → sugira CDB de curto prazo ou Tesouro Selic.\n"
            "- Ao cliente demonstrar perfil arrojado ou interesse em renda variável → apresente ações e FIIs.\n"
            "- Ao cliente mencionar aposentadoria ou longo prazo → explore Previdência Privada e Tesouro IPCA+.\n"
            "- Sempre encerre a conversa oferecendo contato com um assessor humano especialista.\n\n"
            "AVISOS REGULATÓRIOS:\n"
            "- Rentabilidade passada não é garantia de rentabilidade futura.\n"
            "- Este serviço é informativo e não substitui recomendação personalizada de um especialista certificado.\n\n"
            "ESTILO:\n"
            "- Respostas curtas e diretas (máximo 3 parágrafos).\n"
            "- Tom cordial e profissional, nunca tecnicista em excesso.\n"
            "- Pergunte sobre o objetivo e prazo antes de recomendar."
        )
