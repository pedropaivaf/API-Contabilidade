# ADR-002 — Onboarding do Certificado Digital A1

**Status:** Proposto
**Data:** 2026-04-23
**Depende de:** ADR-001, SECURITY.md

> Este ADR descreve como o cliente (escritório contábil ou empresa) autoriza nossa API a agir em nome dele perante a Receita Federal, fazendo o certificado A1 chegar ao sistema de forma segura e legalmente válida. É o ponto mais sensível da aplicação — se vazar, vaza a "identidade fiscal" do cliente.

Fluxograma visual: `diagrams/onboarding-a1.svg`

## 1. Contexto

Toda operação no Integra Contador do SERPRO exige duas provas:

1. **Prova legal:** procuração eletrônica no eCAC autorizando o CNPJ da nossa empresa a executar serviços específicos em nome do cliente.
2. **Prova técnica:** certificado digital A1 (ICP-Brasil) do cliente, usado em mTLS para cada request ao SERPRO.

Sem as duas, a chamada é rejeitada. O fluxo abaixo garante as duas.

## 2. Fluxo (8 etapas)

### Etapa 1 — Cadastro do cliente
Cliente cria conta, informa CNPJ e aceita termos (inclusive autorização expressa LGPD para uso do certificado em nome dele).

### Etapa 2 — Procuração eletrônica no eCAC
Cliente vai ao e-Procurações da Receita e cadastra nosso CNPJ como procurador, com serviços específicos liberados (ex.: "Simples Nacional — PGDAS-D", "DCTFWeb — Transmissão", "Consulta Cadastral"). **Exigência legal.** Nossa plataforma oferece passo-a-passo e deep link para o portal.

### Etapa 3 — Upload do PFX
Cliente envia o `.pfx` e a senha. Obrigatório:
- Canal TLS 1.3 direto do navegador para nosso endpoint.
- Arquivo **nunca** persistido em disco — lido em memória, criptografado com AES-256-GCM via KMS, e só então armazenado.
- **Senha do PFX jamais** é logada, exibida ou armazenada junto com o arquivo. Guardada em campo separado, também envelopada pelo KMS.
- Alternativa preferencial: **certificado em nuvem** (HSM gerenciado — AWS CloudHSM, SafeID, Valid) — nossa API só recebe a referência, nunca o material privado.

### Etapa 4 — Validação automática
Antes de aceitar, sua API valida:
- Arquivo abre com a senha fornecida.
- CNPJ dentro do certificado = CNPJ cadastrado pelo cliente.
- Certificado não expirado e não está na CRL da AC emissora.
- Emissor é AC credenciada pela ICP-Brasil.

Se qualquer uma falhar: aborta, não persiste nada, devolve erro específico ao cliente.

### Etapa 5 — Teste real no SERPRO
Faz uma chamada simples (ex.: consulta do próprio CNPJ) para confirmar que a procuração eletrônica da etapa 2 está ativa. Sem esse teste, o cliente descobriria que a procuração está errada só ao tentar emitir uma guia real.

### Etapa 6 — Criptografia + guarda
Certificado válido é armazenado em KMS/HSM:
- Chave mestra gerenciada (AWS KMS / GCP KMS / HashiCorp Vault Transit).
- Isolamento por `tenant_id` — cada cliente tem sua própria envelope key.
- Acesso só via IAM role específica do serviço que fala com SERPRO. Nem DevOps lê em claro.

### Etapa 7 — Uso em runtime
Quando chega request do cliente (ex.: emitir DAS):
- API descriptografa o PFX em memória **só pelo tempo** do handshake mTLS com SERPRO.
- Zera o buffer imediatamente após.
- Loga apenas o fingerprint SHA-256 do cert, nunca o conteúdo.
- Cada leitura gera **audit log WORM**: quem, quando, qual CNPJ, request-id, resultado. Retenção 5 anos.

### Etapa 8 — Expiração e revogação (ciclo contínuo)
A1 vale 1 ano. Ciclo obrigatório:
- Alertas automáticos ao cliente: **60 / 30 / 15 / 7 dias** antes do vencimento.
- Cert expirado = operações bloqueadas com mensagem clara.
- Renovação = onboarding idêntico + substituição atômica, sem interromper operações em andamento.
- Cancelamento de contrato: revoga procuração no eCAC + **destrói envelope key** no KMS (crypto-shredding). Audit log é preservado pelo prazo legal.

## 3. Decisões

| Decisão | Alternativa descartada | Porquê |
|---------|-----------------------|--------|
| PFX envelopado em KMS | Guardar em banco com pgcrypto | KMS entrega isolamento de chaves por tenant e auditoria nativa |
| Teste real no SERPRO antes de confirmar onboarding | Confiar que a procuração está ok | Evita cliente descobrir erro só na primeira emissão de guia |
| Log só do fingerprint SHA-256 | Log do serial do cert | Serial é informação do titular, fingerprint é identificador técnico estável |
| Crypto-shredding em vez de delete | Delete lógico | Torna recuperação impossível mesmo com backup — alinhado a LGPD |
| Oferecer cert em nuvem como opção | Só aceitar PFX | Reduz superfície de ataque para clientes maduros |

## 4. Controles de segurança por etapa

| Etapa | Controle obrigatório |
|-------|---------------------|
| 1 | Base legal LGPD registrada; aceite versionado |
| 2 | Nunca aceitamos "confiamos que foi feito"; testamos na etapa 5 |
| 3 | TLS 1.3; upload streaming, zero disco; senha em campo dedicado |
| 4 | Valida cadeia ICP-Brasil online; falha fecha e notifica |
| 5 | Rate-limit do teste; falha fecha e orienta cliente |
| 6 | KMS envelope encryption; IAM role mínima; rotação de master key |
| 7 | Buffer zerado após uso; OpenTelemetry com correlation-id; WORM log |
| 8 | Job diário de expiração; crypto-shredding idempotente |

## 5. Consequências

**Positivas**
- Compliance LGPD + ICP-Brasil com controles auditáveis.
- Superfície de comprometimento mínima (material privado só existe em memória, por milissegundos).
- Suporte natural para certificado em nuvem à medida que clientes maturarem.

**Negativas**
- Custo de KMS por request aumenta com volume — mitigar com cache de envelope keys de curta duração em memória (≤ 60s).
- UX de procuração eletrônica é atrito inevitável — mitigado com onboarding guiado.

## 6. Métricas

- Taxa de sucesso do onboarding ≥ 95% (indicador: quantos clientes completam as 8 etapas sem suporte humano).
- Tempo médio do onboarding ≤ 10 minutos.
- Zero incidente de vazamento de material privado (imutável).
- 100% dos certificados renovados antes da expiração.
