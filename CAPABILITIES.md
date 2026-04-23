# CAPABILITIES — Mapa de Fontes e Destinos

> Matriz de capacidades das integrações suportadas pela API. Fonte da verdade para decidir o que cada adapter implementa e em que ordem.

Atualizado em 2026-04-23.

## 1. Tipologia das integrações

A API-hub conversa com três tipos de sistema:

| Tipo | Papel | Exemplos |
|------|-------|----------|
| **Fonte oficial** | Produz dados obrigatórios (fiscal) | SERPRO Integra Contador, Focus NFe, LegisWeb |
| **ERP/sistema contábil** | Consome nossa API e envia seus dados | Questor, Domínio, Sage, Contmatic, SAP B1 |
| **Plataforma de automação** | Orquestra processos contábeis | Acessorias, Onvio, Conta Azul Pro |

## 2. SERPRO Integra Contador  (fonte oficial — prioridade máxima)

| | |
|--|--|
| Papel | Hub oficial da Receita Federal |
| Auth | OAuth2 + **mTLS** com certificado A1/A3 do cliente |
| Endpoint de auth | `POST https://autenticacao.sapi.serpro.gov.br/authenticate` (Consumer Key/Secret em base64 → Bearer + JWT) |
| Cobrança | Pay-per-use em 8 faixas tarifárias (categorias: Queries / Emissão / Declaração). Ex.: DAS ≈ R$ 0,80 (2025) |
| Faturamento | Mensal por consumo; NFS-e enviada por e-mail |
| Docs | https://apicenter.estaleiro.serpro.gov.br/documentacao/api-integra-contador/ |

Serviços cobertos (v1 da nossa API):

| Serviço | Método SERPRO | Endpoint nosso |
|---------|---------------|-----------------|
| Consulta cadastral CNPJ | Consultar | `GET /v1/cadastro/cnpj/{cnpj}` |
| PGDAS-D (consulta) | Consultar | `GET /v1/simples-nacional/pgdas/{cnpj}/{periodo}` |
| PGDAS-D (declarar) | Declarar | `POST /v1/simples-nacional/pgdas` |
| DAS (emissão) | Emissão | `POST /v1/simples-nacional/das` |
| DCTFWeb (gerar/transmitir) | Declarar | `POST /v1/dctfweb` |
| DCTFWeb (consultar) | Consultar | `GET /v1/dctfweb/{cnpj}/{periodo}` |
| e-CAC — Caixa Postal | Apoiar/Consultar | `GET /v1/ecac/caixa-postal/{cnpj}` |
| Procurações eletrônicas | Consultar | `GET /v1/ecac/procuracoes/{cnpj}` |
| ECD / ECF / DCTF | Consultar | `GET /v1/escrituracao/{tipo}/{cnpj}` |
| Situação fiscal | Consultar | `GET /v1/situacao-fiscal/{cnpj}` |

## 3. Focus NFe  (fonte oficial — NF-e/NFS-e/CT-e)

| | |
|--|--|
| Papel | Emissão e consulta de documentos fiscais |
| Auth | Token HTTP Basic (token como usuário, senha em branco) |
| Cobrança | Por assinatura + volume |
| Docs | https://focusnfe.com.br/doc/ |

Serviços:
- `POST /v1/nfe` — emitir NF-e modelo 55
- `GET /v1/nfe/{chave}` — consultar NF-e
- `DELETE /v1/nfe/{chave}` — cancelar
- `POST /v1/nfse` — NFS-e por município
- `POST /v1/cte` — CT-e transporte

## 4. LegisWeb  (fonte oficial — tabelas tributárias)

| | |
|--|--|
| Papel | Alíquotas ICMS/ISS por UF/município, regras fiscais |
| Auth | API key |
| Cobrança | Assinatura |

Serviços:
- `GET /v1/tributario/aliquotas/iss?ibge=&codigoServico=`
- `GET /v1/tributario/aliquotas/icms?uf_origem=&uf_destino=&ncm=`
- `GET /v1/tributario/regras?cnae=&regime=`

## 5. Questor  (ERP contábil — destino / consumidor)

| | |
|--|--|
| Papel | ERP contábil proprietário; nossa API envia/recebe dados |
| API pública? | Parcial — API SYN documentada; demais endpoints sob acordo de parceria |
| Auth | Token emitido pelo escritório (aprovação por cliente no módulo "Autorizar Acesso a Parceiros") |
| Capacidades | Sincronização de lançamentos contábeis, AP/AR, folha, variáveis de ponto. Wrapper próprio do Integra Contador |
| Docs | https://docs.questor.com.br/pt-br/Produtos/ERP_-_Questor_Negocio/APIQuestorNegocio |

Nossa integração:
- `POST /v1/integracoes/questor/lancamentos` — envia lançamentos para o Questor do cliente.
- `GET /v1/integracoes/questor/lancamentos?periodo=` — lê lançamentos.
- `POST /v1/webhooks/questor` — recebe eventos do Questor (quando suportado).

Importante: cliente precisa aprovar a integração dentro do Questor. Sem isso, token não funciona.

## 6. Acessorias  (plataforma de automação — cliente)

| | |
|--|--|
| Papel | Hub de workflows para escritórios contábeis; consumidor do nosso hub |
| API pública? | Token por usuário (Settings → Integrations). Spec técnica não é pública. |
| Capacidades | Automação de entregas, sincronização de documentos, alertas de prazos, orquestração de tarefas. |
| Docs | https://acessorias.com/site/integracoes/ |

Nossa integração (modelo de consumidor):
- Acessorias chama nossa API REST com token do escritório.
- Nossa API dispara webhooks de status para Acessorias.
- Fase 2 do roadmap; exige contato comercial para alinhar spec.

## 7. Outros ERPs previstos (fase 3)

| ERP | Auth típica | Status |
|-----|------------|--------|
| Domínio Sistemas (Thomson Reuters) | API proprietária | previsto |
| Contmatic Phoenix | API proprietária | previsto |
| Sage 50/100 | OData | previsto |
| SAP Business One | Service Layer | previsto |
| Conta Azul | OAuth2 | previsto |

Cada um vira um **adapter** na nossa camada `app/adapters/erp/`, isolado dos demais. Qualquer um deles pode ser substituído sem afetar clientes.

## 8. Matriz resumo

| Fonte | Tipo | Prioridade | Fase |
|-------|------|-----------|------|
| SERPRO Integra Contador | Fonte oficial federal | ★★★ | 1 (MVP) |
| Focus NFe | Fonte oficial fiscal | ★★★ | 1 |
| LegisWeb | Fonte oficial tributária | ★★ | 2 |
| Questor | ERP destino | ★★ | 2 |
| Acessorias | Plataforma consumidora | ★ | 3 |
| Domínio / Contmatic / Sage / SAP | ERP destino | ★ | 3 |

## 9. O que não está no escopo público

Informações não encontradas publicamente — exigem contato comercial:

- Rate-limits detalhados por faixa SERPRO.
- SLA formal de Questor API SYN.
- Spec OpenAPI completa de Acessorias.
- Contratos de dados para repasse regulamentado de informações fiscais de terceiros.

**Fontes consultadas (2026-04-23):** SERPRO API Center, Questor Docs, Acessorias Integrações. Confirmar preços e métodos antes de produção.
