from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import decrypt_secret, encrypt_secret
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
    config = get_platform_llm_config(db)
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
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            config = get_platform_llm_config(db)
            if not config:
                raise
    return config


def get_platform_llm_config(db: Session) -> LLMProviderConfig | None:
    return db.scalar(
        select(LLMProviderConfig)
        .where(LLMProviderConfig.scope == "platform")
        .order_by(LLMProviderConfig.updated_at.desc(), LLMProviderConfig.id.desc())
        .limit(1)
    )


def mask_api_key(api_key: str | None) -> str | None:
    if not api_key:
        return None
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}{'*' * max(len(api_key) - 8, 4)}{api_key[-4:]}"


def build_llm_config_response(config: LLMProviderConfig) -> LLMConfigResponse:
    resolved_api_key = decrypt_secret(config.api_key)
    return LLMConfigResponse(
        provider_name=config.provider_name,
        base_url=config.base_url,
        api_key_masked=mask_api_key(resolved_api_key),
        has_api_key=bool(resolved_api_key),
        model_name=config.model_name,
        model_options=COMMON_MODEL_OPTIONS,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        is_enabled=config.is_enabled,
        notes=config.notes,
    )


def set_encrypted_api_key(config: LLMProviderConfig, api_key: str | None):
    config.api_key = encrypt_secret(api_key) if api_key else None


def get_decrypted_api_key(config: LLMProviderConfig) -> str | None:
    return decrypt_secret(config.api_key)
