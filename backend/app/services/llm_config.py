from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import LLMProviderConfig
from app.schemas.contracts import LLMConfigResponse, LLMModelOption


DEFAULT_PROVIDER_NAME = "OpenAI Compatible"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL_NAME = "gpt-4.1-mini"
DEFAULT_TEMPERATURE = 0.4
DEFAULT_MAX_TOKENS = 4096

COMMON_MODEL_OPTIONS = [
    LLMModelOption(label="OpenAI · gpt-4.1-mini", value="gpt-4.1-mini", provider_hint="OpenAI"),
    LLMModelOption(label="OpenAI · gpt-4.1", value="gpt-4.1", provider_hint="OpenAI"),
    LLMModelOption(label="OpenAI · gpt-5-mini", value="gpt-5-mini", provider_hint="OpenAI"),
    LLMModelOption(label="OpenAI · gpt-5", value="gpt-5", provider_hint="OpenAI"),
    LLMModelOption(label="阿里云百炼 · qwen-plus", value="qwen-plus", provider_hint="DashScope"),
    LLMModelOption(label="阿里云百炼 · qwen-max", value="qwen-max", provider_hint="DashScope"),
    LLMModelOption(label="DeepSeek · deepseek-chat", value="deepseek-chat", provider_hint="DeepSeek"),
    LLMModelOption(label="DeepSeek · deepseek-reasoner", value="deepseek-reasoner", provider_hint="DeepSeek"),
]


def get_or_create_llm_config(db: Session) -> LLMProviderConfig:
    config = db.scalar(
        select(LLMProviderConfig)
        .where(LLMProviderConfig.scope == "platform")
        .order_by(LLMProviderConfig.id.asc())
        .limit(1)
    )
    if not config:
        config = LLMProviderConfig(
            scope="platform",
            provider_name=DEFAULT_PROVIDER_NAME,
            base_url=DEFAULT_BASE_URL,
            model_name=DEFAULT_MODEL_NAME,
            temperature=DEFAULT_TEMPERATURE,
            max_tokens=DEFAULT_MAX_TOKENS,
            is_enabled=False,
            notes="支持 OpenAI 兼容接口，模型列表可自定义扩展。",
        )
        db.add(config)
        db.flush()
    return config


def mask_api_key(api_key: str | None) -> str | None:
    if not api_key:
        return None
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}{'*' * max(len(api_key) - 8, 4)}{api_key[-4:]}"


def build_llm_config_response(config: LLMProviderConfig) -> LLMConfigResponse:
    return LLMConfigResponse(
        provider_name=config.provider_name,
        base_url=config.base_url,
        api_key_masked=mask_api_key(config.api_key),
        has_api_key=bool(config.api_key),
        model_name=config.model_name,
        model_options=COMMON_MODEL_OPTIONS,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        is_enabled=config.is_enabled,
        notes=config.notes,
    )
