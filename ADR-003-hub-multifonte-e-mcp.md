# ADR-003 — Hub multi-fonte + Interface dupla (REST + MCP)

**Status:** Proposto
**Data:** 2026-04-23
**Depende de:** ADR-001, ADR-002, SECURITY.md, CAPABILITIES.md

## 1. Contexto

O objetivo evoluiu: além de wrapper seguro do SERPRO, a API precisa funcionar como **hub** que converse com:

- **Fontes oficiais** (SERPRO, Focus NFe, LegisWeb) — produzem dados.
- **ERPs contábeis** (Questor, Domínio, Contmatic, Sage, SAP B1) — trocam lançamentos.
- **Plataformas de automação** (Acessorias, Onvio, Conta Azul Pro) — consomem dados.

E precisa ser consumível por **dois tipos de cliente**:

1. **Softwares tradicionais** → chamam REST/OpenAPI.
2. **Agentes de IA / copilotos contábeis** → chamam via **MCP (Model Context Protocol)**.

Expor MCP além de REST é o que transforma a API em "plugin universal" — qualquer assistente (Claude, ChatGPT via conectores, copilotos custom) pode usar os recursos com tipagem e descoberta automáticas.

## 2. Decisão

Uma única camada de domínio, **dois adaptadores de entrada** e **N adaptadores de saída**:

```
                     ┌────────────────────────────────────┐
                     │         Clientes                   │
                     │  ERPs · Apps · Agentes IA (Claude) │
                     └───────┬─────────────┬──────────────┘
                             │             │
                    REST/JSON│             │MCP (stdio/HTTP)
                             ▼             ▼
                     ┌────────────────────────────────────┐
                     │   Interface Layer                  │
                     │   app/api  (FastAPI)               │
                     │   app/mcp  (FastMCP)               │
                     └───────────────┬────────────────────┘
                                     │
                                     ▼
                     ┌────────────────────────────────────┐
                     │   Domain Layer (regras, validações)│
                     │   app/domain                       │
                     └───────────────┬────────────────────┘
                                     │
                                     ▼
                     ┌────────────────────────────────────┐
                     │   Adapters (um por sistema)        │
                     │   serpro · focus_nfe · legisweb    │
                     │   questor · acessorias · dominio   │
                     └───────────────┬────────────────────┘
                                     │
                                     ▼
                    Fontes oficiais · ERPs · Plataformas
```

### Princípios

1. **Uma fonte de lógica** — domínio em `app/domain`; REST e MCP são só *interface*.
2. **Adapter pattern** — cada sistema externo em arquivo próprio, interface comum `SourceAdapter`/`DestinationAdapter`.
3. **Contrato OpenAPI é fonte de verdade** — tools do MCP são geradas a partir dele (script `scripts/generate_mcp_from_openapi.py`), evitando divergência.
4. **Idempotência em escrita** obrigatória nas duas interfaces.
5. **Auth por interface**:
   - REST → OAuth2 Client Credentials + JWT.
   - MCP → MCP Authorization (OAuth2 PKCE) + escopo por tool.
6. **Sem vazamento entre tenants** — `tenant_id` sempre derivado do token, nunca do payload.

## 3. Exposição MCP — quais tools

MVP (fase 1):

| Tool MCP | Descrição para o modelo | Adapter |
|----------|------------------------|--------|
| `consultar_cnpj` | Retorna dados cadastrais oficiais de um CNPJ (razão social, CNAE, regime, endereço). | SERPRO |
| `emitir_das` | Emite guia DAS do Simples Nacional para um CNPJ e competência. | SERPRO |
| `consultar_pgdas` | Consulta declaração PGDAS-D de uma competência. | SERPRO |
| `gerar_dctfweb` | Gera e transmite DCTFWeb. | SERPRO |
| `emitir_nfe` | Emite NF-e modelo 55 a partir de payload estruturado. | Focus NFe |
| `consultar_nfe` | Consulta NF-e por chave de acesso. | Focus NFe |
| `aliquota_iss` | Alíquota de ISS para município/serviço. | LegisWeb |
| `sincronizar_questor` | Envia lançamentos contábeis para o Questor do cliente. | Questor |
| `listar_caixa_postal_ecac` | Lista intimações no e-CAC do cliente. | SERPRO |

Cada tool é uma fachada fina sobre um endpoint REST — reutiliza a mesma função de domínio.

### Fluxo de uma tool

```
Agente IA chama tool `emitir_das` com {cnpj, periodo}
   → MCP server valida escopo do token MCP
   → Chama app/domain/das.py::emitir(cnpj, periodo, tenant_id)
   → Domain chama adapter SerproAdapter.emitir_das()
   → Adapter faz OAuth2 + mTLS + SERPRO
   → Retorno normalizado (DAS model) → JSON para o agente
   → Audit log WORM registra: tool, tenant, cnpj, request_id, fingerprint cert
```

## 4. Segurança específica do MCP

MCP multiplica superfície de ataque (qualquer agente IA pode chamar). Controles extras:

- **Escopo mínimo por tool**: `consultar_cnpj` tem escopo `read:cadastro`; `emitir_das` tem `write:das`. Token MCP emitido com escopo pode ser read-only.
- **Confirmation prompt obrigatório em operações de escrita**: tools que emitem guia, NFe ou transmitem declaração retornam, na primeira chamada, um `preview` + `confirmation_token` com TTL de 5 min. A emissão real só acontece numa segunda chamada passando o token. Evita que um agente confuso emita documento sem intenção humana.
- **Rate-limit mais agressivo em MCP** do que REST (50% do limite REST por default).
- **Tools sensíveis exigem re-autenticação** (step-up auth): trocar certificado, revogar procuração, deletar tenant.
- **Logs MCP marcados**: campo `interface=mcp` no audit log para análise separada.
- **Bloqueio por allow-list de agentes**: cliente pode restringir quais `mcp_client_id`s podem usar tools de escrita.

## 5. Implementação

Stack adicional:

| Camada | Escolha |
|--------|--------|
| MCP server | **FastMCP** (Python) — mesma stack do FastAPI |
| Transporte | stdio (local) + HTTP/SSE (remoto, produção) |
| Geração de tools | Script que lê `openapi.yaml` e emite `app/mcp/tools.py` |
| Autorização MCP | OAuth2 PKCE com mesmo Auth Server do REST |

Pasta nova:

```
app/mcp/
├── server.py        # Bootstrap FastMCP
├── tools.py         # Tools geradas a partir do OpenAPI (não editar à mão)
├── confirmation.py  # Fluxo preview + confirmation_token
└── auth.py          # Validador de token MCP
```

## 6. Consequências

**Positivas**
- Um sistema, duas entradas. Software tradicional e IA consomem a mesma coisa.
- Gera efeito de rede: quanto mais fontes viram adapters, mais poderoso o hub fica para os dois tipos de cliente.
- MCP abre mercado de copilotos contábeis — diferencial competitivo.

**Negativas / riscos**
- Superfície de ataque maior — mitigada com escopo restrito, confirmation tokens e rate-limit específico.
- Custo SERPRO por chamada agora vem de dois fluxos; precisa de quota por tenant independentemente da interface.
- Manter tools MCP em sincronia com REST exige o gerador automático; sem ele, vira dívida técnica.

## 7. Roadmap atualizado

| Fase | Entrega |
|------|---------|
| 1 | REST MVP + MCP com 3 tools read-only (`consultar_cnpj`, `consultar_pgdas`, `aliquota_iss`) |
| 2 | MCP com tools de escrita + confirmation flow + Focus NFe |
| 3 | Adapters ERP (Questor) + tool `sincronizar_questor` |
| 4 | Acessorias + outros ERPs conforme demanda |

## 8. Métricas

- ≥ 90% paridade automática entre tools MCP e endpoints REST (medida pelo gerador).
- Tempo médio de resposta MCP ≤ tempo REST + 50ms.
- Zero incidente de escrita não-intencional via MCP (medido por confirmation tokens não usados / tools invocadas).
