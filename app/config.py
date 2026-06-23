"""Local configuration for synthetic TradeFlow AgentOS workflows."""

from pydantic import BaseModel


class Settings(BaseModel):
    environment: str = "local"
    use_synthetic_data: bool = True
    draft_only: bool = True
    external_api_calls_enabled: bool = False


settings = Settings()
