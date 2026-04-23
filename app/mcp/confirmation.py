"""Confirmation token flow — obriga dois passos em tools de escrita.

Evita emissões acidentais por agentes de IA. Na primeira chamada, a tool
retorna um preview + token de curta duração. A execução real só acontece
numa segunda chamada que apresente o token.

Produção: trocar _STORE por Redis com TTL real. Este é um stub in-memory.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any

from app.config import settings


@dataclass
class _Entry:
    tool: str
    payload_hash: str
    expires_at: float


_STORE: dict[str, _Entry] = {}


def _hash_payload(payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hmac.new(settings.jwt_secret.encode(), normalized.encode(), hashlib.sha256).hexdigest()


def issue_confirmation(tool: str, payload: dict[str, Any], ttl_seconds: int = 300) -> str:
    token = secrets.token_urlsafe(24)
    _STORE[token] = _Entry(
        tool=tool,
        payload_hash=_hash_payload(payload),
        expires_at=time.time() + ttl_seconds,
    )
    return token


def consume_confirmation(tool: str, token: str, payload: dict[str, Any]) -> None:
    entry = _STORE.pop(token, None)
    if entry is None:
        raise PermissionError("confirmation_token inválido ou já consumido")
    if entry.tool != tool:
        raise PermissionError("confirmation_token pertence a outra tool")
    if entry.expires_at < time.time():
        raise PermissionError("confirmation_token expirado — refaça o preview")
    if entry.payload_hash != _hash_payload(payload):
        raise PermissionError(
            "payload da confirmação difere do preview — emissão bloqueada por segurança"
        )
