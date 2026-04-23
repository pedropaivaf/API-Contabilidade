# API Contábil Universal

Hub contábil que elimina robôs/RPA integrando diretamente as fontes oficiais (SERPRO Integra Contador, Focus NFe, LegisWeb, Open Finance) em um contrato único REST/OpenAPI + MCP.

**Começando agora?** Leia `CONTEXT.md` e depois `SEMANA-1-CHECKLIST.md`.

## Regra mandatória

**Leia `SECURITY.md` antes de qualquer outra coisa.** Segurança é requisito funcional deste projeto, não opcional. Qualquer PR que viole as regras de segurança é rejeitado.

## Arquivos nesta entrega

- `SECURITY.md` — **regra mandatória** de segurança (OWASP ASVS L2, LGPD, ISO 27001).
- `ADR-001-api-contabil-universal.md` — decisão arquitetural completa (stack, integrações, segurança, roadmap).
- `ADR-002-onboarding-certificado-a1.md` — fluxo de onboarding do certificado A1 (8 etapas, controles).
- `ADR-003-hub-multifonte-e-mcp.md` — exposição dupla REST + MCP e adapters para ERPs.
- `CAPABILITIES.md` — matriz de fontes (SERPRO, Focus NFe, LegisWeb, Questor, Acessorias).
- `diagrams/onboarding-a1.svg` — fluxograma visual do onboarding A1.
- `app/mcp/` — servidor MCP (FastMCP) com tools para agentes de IA.
- `openapi.yaml` — contrato OpenAPI 3.1 com endpoints principais (cadastro, DAS, PGDAS, DCTFWeb, NFe, alíquotas, webhooks).
- `app/` — esqueleto FastAPI pronto para rodar.
- `docker-compose.yml` — Postgres, Redis, API.
- `.env.example` — variáveis de ambiente.

## Rodar localmente

```bash
cp .env.example .env
docker compose up --build
# Swagger UI: http://localhost:8000/docs
```

## Estrutura

```
app/
├── main.py                # Bootstrap FastAPI
├── config.py              # Settings (pydantic-settings)
├── api/
│   └── v1/
│       ├── cadastro.py
│       ├── simples_nacional.py
│       ├── nfe.py
│       └── webhooks.py
├── adapters/              # Cada fonte oficial em um adapter isolado
│   ├── serpro.py          # Integra Contador (OAuth2 + mTLS)
│   ├── focus_nfe.py
│   └── legisweb.py
├── domain/                # Modelos de negócio (pydantic)
│   ├── empresa.py
│   ├── das.py
│   └── nfe.py
├── infra/
│   ├── db.py              # SQLAlchemy + Postgres
│   ├── cache.py           # Redis
│   └── queue.py           # Celery
└── security/
    ├── auth.py            # OAuth2/JWT
    └── crypto.py          # AES-256, KMS
```

## Próximos passos

1. Aprovar ADR.
2. Provisionar credenciais SERPRO (sandbox) e certificado A1.
3. Implementar adapter SERPRO + endpoint `/cadastro/cnpj`.
4. Implementar fila Celery para emissão assíncrona de DAS.
5. Gerar SDKs via `openapi-generator`.
