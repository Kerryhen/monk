from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    LISTMONK_USER: str
    LISTMONK_TOKEN: str
    LISTMONK_API_URL: str
    POCKETBASE_BOT_EMAIL: str
    POCKETBASE_BOT_PASSWORD: str
    POCKETBASE_API_URL: str
    ENVIRONMENT: str = 'PRD'
    # Listmonk template ID for non-email messenger campaigns (must output content as-is, no HTML wrapping).
    # Create a template with body `{{ template "content" . }}` and set its ID here.
    LISTMONK_MESSENGER_TEMPLATE_ID: int = 0
