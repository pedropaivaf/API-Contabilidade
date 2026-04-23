"""MCP Server — expõe a API contábil como ferramentas para agentes de IA.

Usa FastMCP. Cada tool é uma fachada fina sobre o domínio, reusando os
mesmos adapters do REST. Tools de escrita exigem confirmation token.

Rodar localmente:
    python -m app.mcp.server          # stdio
    python -m app.mcp.server --http   # HTTP/SSE na porta 8001
"""
from __future__ import annotations

from typing import Annotated

from pydantic import Field

from app.adapters.focus_nfe import focus_nfe
from app.adapters.serpro import serpro
from app.mcp.confirmation import consume_confirmation, issue_confirmation

try:
    from fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Instale fastmcp: pip install fastmcp") from exc

mcp = FastMCP(
    name="api-contabil",
    instructions=(
        "Hub contábil brasileiro. Conecta ERPs e agentes de IA às fontes oficiais "
        "(SERPRO Integra Contador, Focus NFe, LegisWeb). "
        "Tools de escrita (emitir_das, emitir_nfe) seguem fluxo de dois passos: "
        "primeira chamada retorna um preview + confirmation_token; a execução "
        "real requer uma segunda chamada passando esse token."
    ),
)


# =========================================================================
# READ TOOLS (sem confirmation)
# =========================================================================

_CNPJ_DESC = "CNPJ somente dígitos, 14 caracteres"


@mcp.tool(
    description=(
        "Consulta dados cadastrais oficiais de um CNPJ na Receita Federal via SERPRO. "
        "Retorna razão social, CNAE principal, regime tributário, endereço e situação."
    )
)
async def consultar_cnpj(
    cnpj: Annotated[str, Field(pattern=r"^\d{14}$", description=_CNPJ_DESC)],
) -> dict:
    return await serpro.consultar_cnpj(cnpj)


@mcp.tool(
    description=(
        "Consulta declaração PGDAS-D do Simples Nacional para um CNPJ e competência "
        "(formato YYYY-MM). Fonte: SERPRO Integra Contador."
    )
)
async def consultar_pgdas(
    cnpj: Annotated[str, Field(pattern=r"^\d{14}$")],
    periodo: Annotated[str, Field(pattern=r"^\d{4}-\d{2}$", examples=["2026-03"])],
) -> dict:
    return await serpro.consultar_pgdas(cnpj, periodo)


_CHAVE_DESC = "Chave de acesso da NFe, 44 dígitos"


@mcp.tool(
    description=(
        "Consulta uma NF-e emitida pela chave de acesso (44 dígitos). Retorna status, "
        "emissor, destinatário, itens e URLs de XML e DANFE."
    )
)
async def consultar_nfe(
    chave: Annotated[str, Field(pattern=r"^\d{44}$", description=_CHAVE_DESC)],
) -> dict:
    return await focus_nfe.consultar_nfe(chave)


# =========================================================================
# WRITE TOOLS (confirmation obrigatório)
# =========================================================================

_CONFIRMATION_HELP = "Token retornado no preview. Omitir na primeira chamada."


@mcp.tool(
    description=(
        "Emite guia DAS do Simples Nacional. FLUXO DE DOIS PASSOS: "
        "(1) chame sem confirmation_token para receber um preview com valor e vencimento; "
        "(2) chame novamente com o confirmation_token recebido para emitir de fato. "
        "Essa verificação evita emissões acidentais por agentes de IA."
    )
)
async def emitir_das(
    cnpj: Annotated[str, Field(pattern=r"^\d{14}$")],
    periodo: Annotated[str, Field(pattern=r"^\d{4}-\d{2}$")],
    confirmation_token: Annotated[str | None, Field(description=_CONFIRMATION_HELP)] = None,
) -> dict:
    if confirmation_token is None:
        preview = {"cnpj": cnpj, "periodo": periodo, "acao": "EMITIR_DAS"}
        token = issue_confirmation("emitir_das", preview, ttl_seconds=300)
        return {
            "status": "PREVIEW",
            "preview": preview,
            "confirmation_token": token,
            "instrucao": "Chame novamente passando confirmation_token para emitir.",
        }
    consume_confirmation("emitir_das", confirmation_token, {"cnpj": cnpj, "periodo": periodo})
    return await serpro.emitir_das(cnpj, periodo)


_REFERENCIA_DESC = "Identificador único da emissão (UUID recomendado)"
_NFE_PAYLOAD_DESC = "Payload NF-e no formato Focus NFe (emitente, destinatário, itens)."


@mcp.tool(
    description=(
        "Emite NF-e modelo 55. FLUXO DE DOIS PASSOS obrigatório (ver emitir_das). "
        "O referencia funciona como Idempotency-Key — mesma referencia nunca emite duas vezes."
    )
)
async def emitir_nfe(
    referencia: Annotated[str, Field(description=_REFERENCIA_DESC)],
    payload: Annotated[dict, Field(description=_NFE_PAYLOAD_DESC)],
    confirmation_token: str | None = None,
) -> dict:
    if confirmation_token is None:
        resumo = {
            "referencia": referencia,
            "emitente": payload.get("emitente", {}).get("cnpj"),
            "itens": len(payload.get("itens", [])),
        }
        token = issue_confirmation("emitir_nfe", resumo, ttl_seconds=300)
        return {"status": "PREVIEW", "preview": resumo, "confirmation_token": token}
    consume_confirmation("emitir_nfe", confirmation_token, {"referencia": referencia})
    return await focus_nfe.emitir_nfe(referencia, payload)


# =========================================================================
# ENTRY POINT
# =========================================================================

if __name__ == "__main__":
    import sys

    if "--http" in sys.argv:
        # Bind 0.0.0.0 é intencional: o MCP server roda em container e
        # precisa aceitar conexões externas ao namespace de rede.
        mcp.run(transport="http", host="0.0.0.0", port=8001)  # noqa: S104  # nosec B104
    else:
        mcp.run()  # stdio
