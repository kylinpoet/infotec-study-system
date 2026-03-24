from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.db.seed import seed_database
from app.db.session import init_db, session_scope

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with session_scope() as session:
        seed_database(session)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/", tags=["root"])
def root():
    return {
        "name": settings.app_name,
        "docs": f"{settings.api_prefix}/health",
        "frontend": "Run the Vite client from /frontend for the full UI.",
    }
