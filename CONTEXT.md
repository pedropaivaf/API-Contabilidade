# CONTEXT — Briefing para retomar em qualquer máquina

**Repositório oficial:** https://github.com/pedropaivaf/API-Contabilidade

> **Se você é Claude lendo isto em uma nova sessão:** este documento tem o estado completo do projeto. Leia-o primeiro. Depois leia os ADRs na ordem (001 → 002 → 003), SECURITY.md e CAPABILITIES.md. Com isso, consegue continuar de onde paramos.

> **Se você é Pedro em outra máquina:** suba este repositório no GitHub e, ao abrir o Claude em qualquer lugar, peça para ele ler `CONTEXT.md` primeiro. Todo contexto volta.

Última atualização: 2026-04-23.

## 1. Quem é o dono do projeto

- **Pedro** — único dev do projeto. Trabalha em escritório contábil.
- Conta com **Claude como "super poder"**: pair programming contínuo, geração de código, revisão, decisões de arquitetura.
- Tem orçamento para infra como aposta (espera-se ~R$ 600/mês nos primeiros 6 meses).

## 2. Contexto do escritório

| Dado | Valor |
|------|-------|
| Nº de CNPJs atendidos | 200+ |
| % no Simples Nacional | ~70% (premissa do Pedro) |
| Tamanho do time que opera sistemas | 28 pessoas |
| Admin técnico dos sistemas (Questor/SERPRO) | **O chefe do Pedro** — ponto único de contato para credenciais |
| Software contábil instalado | Questor (edição exata ainda a confirmar com o chefe) |
| Hub de automação usado | Acessorias |
| Acesso SERPRO | Contrato ativo; credenciais de produção com o chefe; sandbox ainda a pedir |

## 3. O que queremos construir

**Uma API-hub contábil universal** que:
- Elimina robôs/RPA — integra direto com fontes oficiais (SERPRO, Focus NFe, LegisWeb).
- Converse com qualquer ERP/plataforma (Questor, Acessorias, Domínio, Contmatic, etc.) via adapters isolados.
- Expõe **dupla interface**: REST (OpenAPI 3.1) para software tradicional + **MCP (Model Context Protocol)** para agentes de IA.
- Primeiro cliente: o próprio escritório do Pedro (dogfooding).
- Depois: vender para outros escritórios.

## 4. Decisões arquiteturais fechadas (ADRs)

Ler em ordem:

1. **ADR-001** — Arquitetura geral (hub multi-fonte, FastAPI, Postgres, Redis, Celery).
2. **ADR-002** — Onboarding do certificado digital A1 (8 etapas, KMS, crypto-shredding).
3. **ADR-003** — Exposição dupla REST + MCP com adapters para ERPs; confirmation flow obrigatório em tools de escrita.

Documentos transversais:

- **SECURITY.md** — regra mandatória (OWASP ASVS L2, LGPD, ISO 27001). Tem precedência sobre qualquer outra decisão.
- **CAPABILITIES.md** — matriz de fontes (SERPRO, Focus NFe, LegisWeb, Questor, Acessorias) com capacidades, auth e cobrança.

## 5. Stack técnica oficial (recalibrada para solo dev)

Simplificamos a stack do ADR-001 (que estava para time grande) para realidade de **dev único + IA**:

| Camada | Escolha | Porquê |
|--------|---------|--------|
| Linguagem | Python 3.12 | Comunidade forte no BR, bom tooling contábil |
| Framework API | FastAPI | OpenAPI nativo, async, Pydantic |
| MCP | FastMCP | Mesma stack que FastAPI |
| Hospedagem | **Fly.io** | Deploy 1-comando, sem Kubernetes |
| Banco | **Neon** (Postgres serverless) | Branch por ambiente, free tier decente |
| Cache/fila | **Upstash Redis** | Pay-per-use |
| Worker | Celery rodando no Fly.io | Para emissões assíncronas |
| KMS | **AWS KMS** (isolado, só o KMS) | $1/chave/mês |
| Secrets | **Doppler** ou 1Password Secrets | Sem Vault self-hosted |
| Observabilidade | **Sentry** + **Axiom** (ou Better Stack) | Free tier atende início |
| CDN/WAF | **Cloudflare** | Free/Pro |
| CI/CD | GitHub Actions | Gratuito |

**O que NÃO vamos usar nos primeiros 6 meses:** Kubernetes, Vault self-hosted, HSM dedicado, SOC 2 formal, DAST semanal, multi-região. Volta no escopo quando houver cliente externo pagando.

## 6. Estado atual do repositório

Estrutura em `outputs/` (vira a raiz do repo Git):

```
.
├── CONTEXT.md                    ← este arquivo
├── README.md
├── SECURITY.md
├── CAPABILITIES.md
├── ADR-001-api-contabil-universal.md
├── ADR-002-onboarding-certificado-a1.md
├── ADR-003-hub-multifonte-e-mcp.md
├── SEMANA-1-CHECKLIST.md         ← próximos passos
├── openapi.yaml
├── docker-compose.yml
├── Dockerfile
├── fly.toml
├── requirements.txt
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── .github/workflows/ci.yml
├── diagrams/
│   └── onboarding-a1.svg
└── app/
    ├── main.py
    ├── config.py
    ├── api/v1/                    (cadastro, simples_nacional, nfe, webhooks)
    ├── adapters/                  (serpro, focus_nfe)
    └── mcp/                       (server, confirmation)
```

## 7. O que JÁ está feito

- Skeleton FastAPI funcional (com endpoints stub).
- Adapter SERPRO (auth OAuth2 + mTLS) — stub carregando PFX comentado, pronto para ativar.
- Adapter Focus NFe — funcional com token.
- MCP server (FastMCP) com tools `consultar_cnpj`, `consultar_pgdas`, `consultar_nfe`, `emitir_das`, `emitir_nfe`.
- Confirmation flow em tools de escrita MCP (anti-emissão acidental por IA).
- OpenAPI 3.1 contrato inicial.
- Docker Compose para dev local.
- Diagrama SVG do onboarding A1.
- Todos os ADRs + SECURITY.md + CAPABILITIES.md.

## 8. O que FALTA fazer (semana 1 em diante)

Ver `SEMANA-1-CHECKLIST.md` para o passo a passo.

Resumo por fase:

- **Semana 1:** infra hospedada + primeira chamada real contra sandbox SERPRO (`consultar_cnpj` ponta a ponta).
- **Semana 2:** onboarding A1 real + primeira emissão de DAS do próprio escritório.
- **Semana 3:** lote + integração Questor (gravar lançamento do DAS).
- **Semana 4:** produção + MCP em Claude Desktop + primeiro fechamento mensal automatizado.

## 9. Respostas do Pedro ao questionário de calibração

Perguntas 1-25 do chat. O que foi respondido:

| # | Pergunta | Resposta |
|---|----------|----------|
| 1 | CNPJs totais | 200+ |
| 2 | % por regime | ~70% Simples (demais não sei) |
| 3 | Pessoas operando | 28 |
| 4-12 | Detalhes Questor/Acessorias/SERPRO | Chefe tem as respostas |
| Adm técnico | Quem opera Questor/SERPRO | Chefe do Pedro |

Pedro é **solo dev**. Tem condição de investir em infra como aposta.

## 10. Como continuar em outra máquina

### Se você vai trabalhar em nova máquina

1. Repositório oficial: https://github.com/pedropaivaf/API-Contabilidade
   ```bash
   git clone https://github.com/pedropaivaf/API-Contabilidade.git
   cd API-Contabilidade
   ```
2. Na nova máquina, clone e abra com Claude.
3. Diga a Claude: "Leia `CONTEXT.md` primeiro e confirme onde paramos".

### Se você vai continuar com Claude em outro produto

Cole este arquivo no primeiro turno da nova conversa, com a instrução:
> "Este é o estado do projeto. Leia `CONTEXT.md`, `SECURITY.md`, `ADR-001`, `ADR-002`, `ADR-003`, `CAPABILITIES.md` e `SEMANA-1-CHECKLIST.md`. Confirme o entendimento e diga onde paramos."

## 11. Princípios que **não se negociam**

Estes princípios vêm do SECURITY.md e devem ser lembrados por qualquer IA/pessoa que contribuir:

1. **Segurança é requisito funcional** — precede design, precede prazo.
2. **Nenhum segredo em código ou log** — sempre KMS/Vault.
3. **LGPD desde o dia 1** — dados de CNPJs de terceiros exigem base legal, minimização, crypto-shredding na saída.
4. **Confirmation flow obrigatório em tools MCP de escrita** — IA não emite guia/NFe sem dois passos.
5. **Audit log WORM** em toda operação fiscal — retenção 5 anos.
6. **Dogfooding primeiro** — só vendemos pra fora depois que o escritório do Pedro opera em produção.
