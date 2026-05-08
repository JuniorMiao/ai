"""LLM configuration DTOs (camelCase JSON)."""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class LlmSettingsItem(CamelModel):
    """Safe projection of one stored LLM row (no secrets)."""

    id: int
    provider: str
    base_url: str
    model: str
    api_key_ref: str | None = None
    has_api_key: bool = Field(
        description="True when an API key is stored or apiKeyRef is set",
    )
    is_default: bool = Field(description="Default profile for NL when llmSettingsId is omitted")


class LlmSettingsListResponse(CamelModel):
    items: list[LlmSettingsItem]
    default_id: int | None = Field(
        default=None,
        description="ID of the default profile, if any",
    )
    has_resolvable_key: bool = Field(
        description="True when env OPENAI_API_KEY / DASHSCOPE_API_KEY or any profile yields a key",
    )


class LlmProviderCatalogItem(CamelModel):
    """One registered vendor for UI (dropdown, defaults, copy)."""

    id: str
    display_name: str = Field(description="Long label for the provider Select")
    short_name: str = Field(description="Short label for tables / badges")
    default_base_url: str
    default_model: str
    primary_api_key_env: str = Field(
        description="Preferred env var name for apiKeyRef placeholder",
    )
    password_placeholder: str = ""
    api_key_inline_hint: str = Field(
        default="",
        description="Helper text when storing an inline key (new profile or no stored secret)",
    )


class LlmProviderCatalogResponse(CamelModel):
    items: list[LlmProviderCatalogItem]


class PostLlmSettingsBody(CamelModel):
    provider: str = Field(
        default="openai",
        description="openai（OpenAI）或 qwen（阿里云通义千问 / DashScope 兼容）",
    )
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    api_key_ref: str | None = Field(
        default=None,
        description="Environment variable name whose value is the API key",
    )
    api_key: str | None = Field(
        default=None,
        description="Optional inline API key; persisted locally only",
    )
    set_as_default: bool = Field(
        default=True,
        description="Make this profile the default for natural-language SQL",
    )


class PutLlmSettingsBody(CamelModel):
    provider: str = Field(
        default="openai",
        description="openai（OpenAI）或 qwen（阿里云通义千问 / DashScope 兼容）",
    )
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    api_key_ref: str | None = None
    api_key: str | None = Field(
        default=None,
        description="Omit to leave unchanged; empty string clears stored inline key",
    )
