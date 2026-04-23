"""Endpoints de cadastro (CNPJ, CPF, CNAE)."""
from fastapi import APIRouter, HTTPException

from app.adapters.serpro import serpro

router = APIRouter()


@router.get("/cnpj/{cnpj}")
async def consultar_cnpj(cnpj: str) -> dict:
    if len(cnpj) != 14 or not cnpj.isdigit():
        raise HTTPException(status_code=400, detail="CNPJ inválido")
    try:
        return await serpro.consultar_cnpj(cnpj)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Falha ao consultar SERPRO: {exc}",
        ) from exc
