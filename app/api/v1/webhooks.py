"""Endpoints de registro/entrega de webhooks."""
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl

router = APIRouter()


class WebhookSubscription(BaseModel):
    url: HttpUrl
    eventos: list[Literal[
        "das.emitida",
        "nfe.autorizada",
        "nfe.cancelada",
        "dctfweb.transmitida",
        "aliquota.alterada",
    ]]
    secret: str


@router.post("/subscriptions", status_code=201)
async def criar_subscription(sub: WebhookSubscription) -> dict:
    # TODO: persistir no banco, associar ao tenant, começar a entregar assinado com HMAC.
    return {"status": "registrado", "eventos": sub.eventos, "url": str(sub.url)}
