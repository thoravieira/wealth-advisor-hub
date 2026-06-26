FSI_DOCUMENTS = [
    {
        "name": "products",
        "content": (
            "Produtos de Investimento Disponíveis:\n\n"
            "CDB (Certificado de Depósito Bancário): Renda fixa, baixo risco, liquidez variável. "
            "Indicado para perfis conservadores que buscam segurança e rentabilidade acima da poupança. "
            "Prazo: 30 dias a 5 anos. Rentabilidade: % do CDI ou taxa prefixada.\n\n"
            "LCI/LCA (Letras de Crédito Imobiliário/Agroindustrial): Isentos de IR para pessoa física. "
            "Renda fixa, prazo mínimo de 90 dias. Alta segurança (garantia FGC até R$250k).\n\n"
            "Tesouro Direto: Títulos públicos federais. Mais seguro do mercado. "
            "Tesouro Selic (liquidez diária), Tesouro IPCA+ (proteção contra inflação), "
            "Tesouro Prefixado (taxa garantida no momento da compra).\n\n"
            "Fundos de Investimento: Diversificação automática com gestão profissional. "
            "Renda fixa, multimercado, ações. Taxa de administração variável.\n\n"
            "Previdência Privada (PGBL/VGBL): Planejamento de longo prazo. "
            "PGBL deduz IR na declaração completa. VGBL ideal para declaração simplificada.\n\n"
            "Renda Variável (Ações/FIIs): Maior potencial de retorno, maior risco. "
            "Indicado para perfil moderado a arrojado com horizonte de longo prazo."
        ),
    },
    {
        "name": "faq",
        "content": (
            "Perguntas Frequentes sobre Investimentos:\n\n"
            "Q: Qual o investimento mais seguro?\n"
            "A: Tesouro Selic e CDB de grandes bancos são os mais seguros, "
            "com proteção do FGC até R$250.000 por CPF por instituição.\n\n"
            "Q: Preciso de muito dinheiro para investir?\n"
            "A: Não. Tesouro Direto aceita a partir de R$30. Muitos CDBs a partir de R$500.\n\n"
            "Q: O que é CDI?\n"
            "A: CDI é a taxa de referência do mercado interbancário, próxima à Selic. "
            "Muitos investimentos rendem um percentual do CDI (ex: 100% do CDI).\n\n"
            "Q: Posso perder dinheiro em renda fixa?\n"
            "A: Em títulos públicos e CDB dentro do limite do FGC, o risco é muito baixo. "
            "Em debêntures e alguns fundos, há risco de crédito.\n\n"
            "Q: Qual a diferença entre PGBL e VGBL?\n"
            "A: PGBL permite deduzir até 12% da renda bruta no IR (declaração completa). "
            "VGBL é melhor para quem usa declaração simplificada ou já atingiu o limite do PGBL."
        ),
    },
    {
        "name": "compliance",
        "content": (
            "Avisos Regulatórios Obrigatórios (CVM/Bacen):\n\n"
            "IMPORTANTE: Rentabilidade passada não é garantia de rentabilidade futura.\n\n"
            "Investimentos em renda variável estão sujeitos a oscilações e o investidor "
            "pode resgatar valor inferior ao investido.\n\n"
            "Este assistente virtual fornece informações educacionais e não constitui "
            "recomendação de investimento personalizada. Para decisões de investimento, "
            "consulte um assessor humano certificado pela ANCORD/CFP.\n\n"
            "Os produtos citados possuem riscos próprios descritos em seus prospectos. "
            "Leia o material antes de investir."
        ),
    },
]


class KnowledgeBaseManager:
    def __init__(self, client):
        self._client = client

    def get_default_documents(self) -> list[dict]:
        return FSI_DOCUMENTS

    def create(self, name: str, content: str) -> str:
        result = self._client.conversational_ai.knowledge_base.create(
            name=name,
            text=content,
        )
        return result.id
