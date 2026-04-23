"""Endpoints de NF-e (modelo 55) via Focus NFe."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header
from pydantic import BaseModel

from app.adapters.focus_nfe import focus_nfe

router = APIRouter()


class Item(BaseModel):
    descricao: str
    quantidade: float
    valorUnitario: float
    ncm: str
    cfop: str


class Destinatario(BaseModel):
    documento: str
    nome: str


class Emitente(BaseModel):
    cnpj: str


class NFeRequest(BaseModel):
    emitente: Emitente
    destinatario: Destinatario
    itens: list[Item]


@router.post("", status_code=202)
async def emitir_nfe(
    payload: NFeRequest,
    idempotency_key: Annotated[UUID, Header(alias="Idempotency-Key")],
) -> dict:
    referencia = str(idempotency_key)
    resultado = await focus_nfe.emitir_nfe(referencia, payload.model_dump())
    return {"referencia": referencia, "resultado": resultado}


@router.get("/{chave}")
async def consultar_nfe(chave: str) -> dict:
    return await focus_nfe.consultar_nfe(chave)
