"""API Contábil Universal — bootstrap FastAPI."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import cadastro, nfe, simples_nacional, webhooks
from app.config import settings

app = FastAPI(
    title="API Contábil Universal",
    version="0.1.0",
    description="Hub contábil que unifica SERPRO, Focus NFe, LegisWeb e Open Finance.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cadastro.router, prefix="/v1/cadastro", tags=["Cadastro"])
app.include_router(
    simples_nacional.router,
    prefix="/v1/simples-nacional",
    tags=["Simples Nacional"],
)
app.include_router(nfe.router, prefix="/v1/nfe", tags=["NFe"])
app.include_router(webhooks.router, prefix="/v1/webhooks", tags=["Webhooks"])


@app.get("/health", tags=["infra"])
def health() -> dict:
    return {"status": "ok"}
