from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import DATA_DIR, get_settings
from app.db.models import Base, LLMProviderConfig

settings = get_settings()
DATA_DIR.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_llm_config_uniqueness()


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _ensure_llm_config_uniqueness():
    with SessionLocal() as session:
        platform_configs = session.scalars(
            select(LLMProviderConfig)
            .where(LLMProviderConfig.scope == "platform")
            .order_by(LLMProviderConfig.updated_at.desc(), LLMProviderConfig.id.desc())
        ).all()
        if len(platform_configs) > 1:
            primary = platform_configs[0]
            for duplicate in platform_configs[1:]:
                if not primary.api_key and duplicate.api_key:
                    primary.api_key = duplicate.api_key
                if not primary.notes and duplicate.notes:
                    primary.notes = duplicate.notes
                session.delete(duplicate)
            session.commit()

    with engine.begin() as connection:
        connection.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS uq_llm_provider_configs_scope ON llm_provider_configs(scope)")
        )
