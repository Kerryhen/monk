from typing import override

from app.handlers.base import VariableResolverBase


class DefaultVariableResolver(VariableResolverBase):
    """Resolves template variable references against a context dict.

    Reference format: "<schema>.<field>[.<subfield>][:<default>]"
    The default separator is the first colon only, so URLs are valid defaults.
    """

    @override
    def resolve(self, ref: str, context: dict) -> tuple[bool, str]:
        if ':' in ref:
            path, default = ref.split(':', 1)
            has_default = True
        else:
            path = ref
            default = ''
            has_default = False

        value: object = context
        for part in path.split('.'):
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(part)

        if not value:
            if has_default:
                return (True, default)
            return (False, '')

        return (True, str(value))
