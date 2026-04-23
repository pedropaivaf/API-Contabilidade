"""Endpoints do Simples Nacional — DAS e PGDAS-D."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.adapters.serpro import serpro

router = APIRouter()


class EmitirDASRequest(BaseModel):
    cnpj: str = Field(pattern=r"^\d{14}$")
    periodo: str = Field(pattern=r"^\d{4}-\d{2}$", examples=["2026-03"])


@router.post("/das", status_code=202)
async def emitir_das(
    payload: EmitirDASRequest,
    idempotency_key: Annotated[UUID, Header(alias="Idempotency-Key")],
) -> dict:
    # TODO: persistir idempotency_key em Redis com TTL; retornar mesmo resultado se repetir.
    try:
        resultado = await serpro.emitir_das(payload.cnpj, payload.periodo)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "operacaoId": str(idempotency_key),
        "status": "CONCLUIDA",
        "resultado": resultado,
    }


@router.get("/pgdas/{cnpj}/{periodo}")
async def consultar_pgdas(cnpj: str, periodo: str) -> dict:
    return await serpro.consultar_pgdas(cnpj, periodo)
