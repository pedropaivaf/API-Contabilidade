"""Adapter para SERPRO Integra Contador.

Encapsula autenticação OAuth2 + mTLS (certificado A1 do cliente) e expõe
métodos de alto nível para consumo interno. Trocar de fornecedor significa
reescrever APENAS este arquivo.
"""
from __future__ import annotations

import ssl
import time
from dataclasses import dataclass

import httpx

from app.config import settings


@dataclass
class SerproToken:
    access_token: str
    expires_at: float

    @property
    def is_valid(self) -> bool:
        return time.time() < self.expires_at - 30


class SerproAdapter:
    """Cliente do Integra Contador.

    Responsabilidades:
      - Obter e cachear token OAuth2.
      - Montar contexto SSL com certificado A1 (mTLS).
      - Expor operações: consultar CNPJ, emitir DAS, consultar PGDAS.
    """

    def __init__(self) -> None:
        self._token: SerproToken | None = None
        self._ssl_ctx = ssl.create_default_context()
        # Em produção: carregar PFX + senha via KMS; aqui é um stub.
        # self._ssl_ctx.load_cert_chain(
        #     certfile=settings.serpro_cert_pfx_path,
        #     password=settings.serpro_cert_password,
        # )
        self._client = httpx.AsyncClient(
            base_url=settings.serpro_base_url,
            verify=self._ssl_ctx,
            timeout=30.0,
        )

    async def _get_token(self) -> str:
        if self._token and self._token.is_valid:
            return self._token.access_token

        resp = await self._client.post(
            "/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(settings.serpro_client_id, settings.serpro_client_secret),
        )
        resp.raise_for_status()
        payload = resp.json()
        self._token = SerproToken(
            access_token=payload["access_token"],
            expires_at=time.time() + int(payload.get("expires_in", 3600)),
        )
        return self._token.access_token

    async def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {await self._get_token()}"}

    # ---------- Operações de negócio ----------

    async def consultar_cnpj(self, cnpj: str) -> dict:
        resp = await self._client.get(f"/cadastro/cnpj/{cnpj}", headers=await self._headers())
        resp.raise_for_status()
        return resp.json()

    async def emitir_das(self, cnpj: str, periodo: str) -> dict:
        resp = await self._client.post(
            "/simples-nacional/das",
            json={"cnpj": cnpj, "periodo": periodo},
            headers=await self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def consultar_pgdas(self, cnpj: str, periodo: str) -> dict:
        resp = await self._client.get(
            f"/simples-nacional/pgdas/{cnpj}/{periodo}",
            headers=await self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def aclose(self) -> None:
        await self._client.aclose()


serpro = SerproAdapter()
