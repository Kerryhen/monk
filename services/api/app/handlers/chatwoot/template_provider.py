from typing import override

from app.handlers.base import TemplateProviderBase
from app.handlers.chatwoot.schemas import ChatwootButtonParam, ChatwootTemplateConfig, ChatwootTemplateParams

# P-01 resolution: Chatwoot API does not expose WhatsApp template definitions,
# so templates are defined locally via Pydantic (Option B from RF-01).
_TEMPLATES: list[ChatwootTemplateConfig] = [
    ChatwootTemplateConfig(
        template_name='cobranca_v2',
        language='pt_BR',
        category='UTILITY',
        params=ChatwootTemplateParams(
            body={
                '1': 'lead.name:amigo',
                '2': 'instancia.razao_social',
                '3': 'campanha.subject:<sem assunto>',
            },
            buttons=[
                ChatwootButtonParam(
                    type='url',
                    parameter='lead.attribs.payment_link',
                    url='https://xpto.domain/path/{{1}}',
                    variables=['1'],
                )
            ],
        ),
    ),
]


class ChatwootTemplateProvider(TemplateProviderBase):
    @override
    def get_templates(self) -> list[dict]:
        return [t.model_dump() for t in _TEMPLATES]
