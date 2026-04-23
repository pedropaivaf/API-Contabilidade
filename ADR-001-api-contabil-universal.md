# ADR-001 — API Contábil Universal

**Status:** Proposto
**Data:** 2026-04-23
**Autor:** Pedro

> ⚠️ **Regra mandatória do projeto: segurança é requisito funcional.** Antes de qualquer código, leia `SECURITY.md`. As decisões abaixo devem ser interpretadas sempre em conformidade com ele; em caso de conflito, `SECURITY.md` prevalece.

---

## 1. Contexto

Sistemas contábeis brasileiros dependem de robôs (RPA) para interagir com portais do governo (eCAC, Receita Federal, prefeituras). Esses robôs quebram a cada mudança de layout, sofrem com captcha e não escalam.

O objetivo é construir uma **API própria de contabilidade** que:

- Seja **válida** (usa fontes oficiais homologadas como fonte da verdade).
- **Converse** com qualquer ERP/sistema contábil por padrões abertos (REST, JSON, XML SPED/NFe, webhooks).
- Seja **universal**: um contrato único, agnóstico do sistema do cliente.
- Elimine dependência de robôs — comunicação direta com APIs oficiais.
- Mantenha dados sempre atualizados (cache inteligente + webhooks de invalidação).

## 2. Problema

1. Cada ERP/escritório contábil reinventa a roda para integrar com Receita, prefeituras e bancos.
2. Robôs são frágeis — quebram com qualquer mudança de HTML ou captcha novo.
3. Alíquotas e regras tributárias mudam constantemente (NFe, ICMS, ISS, Simples Nacional).
4. Não existe um contrato único no mercado que abstraia tudo isso.

## 3. Decisão

Construir uma **API REST OpenAPI-first**, em camadas, que funciona como **hub contábil**:

```
ERP do cliente ──REST/Webhook──▶ Nossa API ──▶ Adapters oficiais ──▶ SERPRO / Focus NFe / LegisWeb / Bancos
```

### 3.1 Princípios

- **OpenAPI-first**: o contrato (`openapi.yaml`) é a fonte da verdade. SDKs em Python/Node/Java são gerados automaticamente.
- **Adapter pattern**: cada fonte externa (SERPRO, Focus NFe, LegisWeb, Banco Central) é um adapter isolado. Trocar fornecedor não afeta o cliente.
- **Idempotência obrigatória**: toda operação de escrita aceita `Idempotency-Key` (evita emissão duplicada de guias/notas).
- **Webhooks para assincronia**: emissões que levam tempo (NFe autorização, DAS) retornam 202 + webhook quando prontas.
- **Cache com TTL por tipo de dado**: cadastro CNPJ (24h), tabela CNAE (30 dias), alíquota ISS por município (7 dias), consulta de débito (5 min).
- **Multi-tenant desde o dia 1**: cada escritório contábil é um `tenant_id`, com quotas e credenciais isoladas.

### 3.2 Domínios cobertos (v1)

| Domínio | Endpoints | Fonte oficial |
|--------|-----------|---------------|
| Cadastro | CNPJ, CPF, CNAE, município | SERPRO Integra Contador |
| Simples Nacional | Emitir DAS, consultar PGDAS-D | SERPRO Integra Contador |
| DCTFWeb | Gerar, transmitir, consultar | SERPRO Integra Contador |
| NF-e / NFS-e / CT-e | Emissão, cancelamento, consulta | Focus NFe |
| Tributário | Alíquotas ICMS/ISS por UF/município, regras | LegisWeb |
| Bancário | Extratos OFX/CNAB, conciliação | Open Finance / CNAB |
| Eventos | Webhooks de status, auditoria | Interno |

### 3.3 Stack técnica

| Camada | Escolha | Porquê |
|--------|---------|--------|
| Linguagem/Framework | **Python 3.12 + FastAPI** | OpenAPI nativo, ecossistema de integrações, fácil contratar no Brasil |
| Banco de dados | **PostgreSQL 16** | JSONB para payloads fiscais, transações ACID, confiável |
| Cache/Fila | **Redis + Celery** | Cache de consultas oficiais, fila para emissões assíncronas |
| Autenticação entrada | **OAuth2 + JWT** (clients do ERP) | Padrão de mercado |
| Autenticação saída SERPRO | **OAuth2 + mTLS (certificado A1)** | Exigência do Integra Contador |
| Infra | **Docker + Kubernetes** (GCP/AWS BR) | Dados não podem sair do Brasil (LGPD) |
| Observabilidade | **OpenTelemetry + Grafana + Sentry** | Auditoria fiscal exige rastreabilidade |

### 3.4 Segurança e LGPD

- Dados tributários são pessoais sensíveis. Criptografia **em repouso (AES-256)** e **em trânsito (TLS 1.3)**.
- Certificados digitais A1/A3 dos clientes guardados em **HSM ou KMS**, nunca em disco cru.
- Logs de acesso imutáveis (WORM) por 5 anos — exigência CFC/Receita.
- Retenção configurável por tenant, com rotina de **direito ao esquecimento**.

### 3.5 Interoperabilidade ("converse com qualquer sistema")

Três formas de um ERP falar com a API:

1. **REST JSON** (preferencial): contrato OpenAPI 3.1.
2. **Importação em lote SPED/NFe XML**: endpoint `POST /v1/import/sped` aceita arquivos ECD/ECF/EFD.
3. **Webhooks de saída**: o ERP recebe eventos (`das.emitida`, `nfe.autorizada`, `alterou-aliquota`) em seu endpoint.

SDKs oficiais gerados via **OpenAPI Generator**: Python, Node, Java, .NET, PHP.

## 4. Alternativas consideradas

| Alternativa | Descartada porquê |
|-------------|-------------------|
| Continuar com RPA/robôs | Problema que queremos eliminar |
| Revender só Integra Contador (wrapper fino) | Não cobre NFe, não agrega valor suficiente |
| GraphQL em vez de REST | Fiscal é request/response simples; REST+OpenAPI tem melhor tooling no Brasil |
| Java/Spring | Válido, mas FastAPI entrega o MVP mais rápido |

## 5. Consequências

**Positivas**
- Um único contrato cobre todos os ERPs clientes.
- Mudança de fornecedor oficial (ex: trocar Focus por outra) não quebra clientes.
- Dados oficiais e atualizados, sem risco de "robô parado".
- SDKs gerados reduzem fricção de integração.

**Negativas / riscos**
- Custo SERPRO (R$ 0,96/guia) precisa de repasse bem calculado.
- Dependência de estabilidade do SERPRO — mitigada com circuit breaker + fila de retry.
- Certificado digital por cliente exige fluxo de onboarding bem desenhado.

## 6. Roadmap

| Fase | Entrega | Prazo estimado |
|------|---------|----------------|
| 0 | ADR aprovado + OpenAPI draft | 1 semana |
| 1 | MVP: cadastro CNPJ + emissão DAS | 4 semanas |
| 2 | NFe via Focus + webhooks | 4 semanas |
| 3 | DCTFWeb + PGDAS-D | 4 semanas |
| 4 | Alíquotas LegisWeb + SDKs multi-linguagem | 4 semanas |
| 5 | Open Finance (extratos) | 6 semanas |

## 7. Métricas de sucesso

- Tempo médio de emissão DAS < 3s (p95).
- Uptime da API ≥ 99.9%.
- Zero incidente de "robô quebrado" (N/A, não há robô).
- ≥ 3 ERPs diferentes integrados em 90 dias.
