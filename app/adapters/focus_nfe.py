"""Adapter para Focus NFe — emissão/consulta de NF-e, NFS-e e CT-e."""
from __future__ import annotations

import httpx

from app.config import settings


class FocusNFeAdapter:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.focusnfe_base_url,
            auth=(settings.focusnfe_token, ""),
            timeout=60.0,
        )

    async def emitir_nfe(self, referencia: str, payload: dict) -> dict:
        resp = await self._client.post(f"/v2/nfe?ref={referencia}", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def consultar_nfe(self, referencia: str) -> dict:
        resp = await self._client.get(f"/v2/nfe/{referencia}")
        resp.raise_for_status()
        return resp.json()

    async def cancelar_nfe(self, referencia: str, justificativa: str) -> dict:
        resp = await self._client.delete(
            f"/v2/nfe/{referencia}", params={"justificativa": justificativa}
        )
        resp.raise_for_status()
        return resp.json()

    async def aclose(self) -> None:
        await self._client.aclose()


focus_nfe = FocusNFeAdapter()
