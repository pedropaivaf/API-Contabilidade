# SECURITY.md — Regra Mandatória do Projeto

> Segurança é **requisito funcional** desta API, não opcional. Qualquer PR que violar as regras abaixo será rejeitado. Este documento tem precedência sobre qualquer outra decisão de design.

**Modelo adotado:** Secure-by-Default + Defense-in-Depth + Zero-Trust interno.
**Referências:** OWASP ASVS L2, OWASP API Security Top 10 (2023), LGPD (Lei 13.709/2018), ISO 27001, CIS Controls v8, Receita Federal/SERPRO — termos de uso Integra Contador.

---

## 1. Princípios não-negociáveis

1. **Least Privilege** — nenhum componente, chave ou token tem permissão além do estritamente necessário.
2. **Zero Trust** — todo request é autenticado e autorizado, mesmo dentro da VPC.
3. **Defense-in-Depth** — falha de uma camada nunca compromete a aplicação sozinha.
4. **Secure-by-Default** — configurações padrão são as mais restritivas; relaxar exige aprovação.
5. **Fail Closed** — em dúvida ou erro, a resposta é negar. Nunca vazar dado por fallback.
6. **Auditabilidade total** — toda ação em dado fiscal é logada imutavelmente por 5 anos.
7. **Privacy-by-Design** — dados pessoais/tributários só existem onde forem essenciais; o resto é pseudonimizado ou descartado.
8. **No Secrets in Code** — segredos só em KMS/Vault; `git push` com segredo = incidente.

## 2. Controles obrigatórios

### 2.1 Autenticação e autorização

- **Entrada (clientes da nossa API):** OAuth2 Client Credentials + JWT assinado (RS256, chave em KMS, rotação 90 dias).
- **Saída SERPRO:** OAuth2 + **mTLS com certificado A1** do cliente, armazenado em HSM/KMS. Nunca em disco cru, nunca em variável de ambiente em texto plano.
- **Autorização:** RBAC por tenant e por escopo (`read:cnpj`, `write:das`, `write:nfe`…). Cheques em **toda** rota, sem exceção.
- **MFA obrigatório** no painel administrativo humano.
- **Rotação automática** de tokens internos a cada 24h; segredos externos a cada 90 dias.

### 2.2 Criptografia

- **Em trânsito:** TLS 1.3 mínimo, HSTS, ciphers modernos. Proibido TLS ≤ 1.1.
- **Em repouso:** AES-256-GCM para dados sensíveis; chaves gerenciadas via KMS (AWS KMS / GCP KMS).
- **Certificados digitais A1/A3 dos clientes:** sempre em HSM ou envelope KMS. Acesso auditado por request.
- **Hash de senhas (se aplicável):** Argon2id.
- **Proibido:** MD5, SHA-1, DES, 3DES, RC4, chaves < 2048 bits RSA ou < 256 bits EC.

### 2.3 Entrada e saída de dados

- **Validação estrita com Pydantic** em todo payload. Nunca aceitar campo não modelado.
- **Output encoding** em tudo que sai (escape contextual).
- **Idempotency-Key obrigatória** em operações fiscais (evita emissão duplicada = risco regulatório).
- **Limites de tamanho** em request body (default: 1 MB; SPED/XML: 25 MB; rejeitar acima).
- **Rate limiting por tenant e por IP** (token bucket, Redis). Padrão: 100 req/s por tenant; burst 500.
- **Content-Type strict:** só aceita o que o endpoint declarou.

### 2.4 Segredos e configuração

- `.env` **nunca** commitado. `.env.example` apenas com nomes.
- Secrets em produção: **AWS Secrets Manager / GCP Secret Manager / HashiCorp Vault**.
- CI/CD injeta segredos em runtime, nunca em build.
- **Pre-commit hook obrigatório:** `gitleaks` + `detect-secrets`. Block push se encontrar.

### 2.5 Dependências e supply chain

- **SBOM** gerado a cada build (CycloneDX).
- **Dependabot** ativo. Vulnerabilidades críticas/high: fix em ≤ 48h.
- **SCA** obrigatório no CI: `pip-audit`, `trivy fs`, `safety`.
- **SAST** no CI: `bandit`, `semgrep` com regras OWASP.
- **DAST** semanal em staging: `ZAP`.
- **Container scan** antes do deploy: `trivy image` — bloqueia crítico/high.
- Imagens base **distroless** ou `python:slim` fixadas por digest.
- **Pin de versões** em `requirements.txt` com hash (`--require-hashes`).

### 2.6 Rede e infraestrutura

- VPC privada; API pública **só via WAF/CDN** (Cloudflare/CloudFront + WAF).
- Banco e Redis **sem IP público**, acesso via security group interno.
- **Egress allowlist:** API só consegue falar com `*.serpro.gov.br`, `api.focusnfe.com.br`, `api.legisweb.com.br` e demais aprovados. Resto é bloqueado.
- Kubernetes: NetworkPolicy deny-all por default; libera só o necessário.
- Hospedagem **obrigatoriamente no Brasil** (LGPD — dados fiscais de brasileiros).
- Backups diários criptografados, retenção 5 anos, teste de restore trimestral.

### 2.7 Logs, auditoria e detecção

- **Log estruturado JSON**, sem PII em texto plano (CPF/CNPJ pseudonimizados nos logs).
- **Audit log imutável (WORM)** por 5 anos: quem acessou, qual CNPJ, qual operação, resultado.
- **Correlation-ID** em todo request, propagado entre serviços.
- **OpenTelemetry** + SIEM (ex: Datadog, Grafana, Elastic).
- **Alertas** em tempo real para: picos 4xx/5xx, novo IP admin, falha repetida de auth, acesso a certificado, egress inesperado.

### 2.8 LGPD — obrigações específicas

- **Base legal** registrada por categoria de dado (execução de contrato + obrigação legal fiscal).
- **Direitos do titular** implementados: acesso, correção, exclusão, portabilidade, oposição. SLA 15 dias.
- **DPIA** (Relatório de Impacto) obrigatório antes de nova integração.
- **Encarregado (DPO)** nomeado e canal público.
- **Notificação de incidente** à ANPD em ≤ 48h se houver risco a titulares.
- **Minimização:** só coletar o que SERPRO/Focus/LegisWeb exigem; nada a mais.
- **Retenção configurável por tenant**, com job de expurgo rodando diariamente.

### 2.9 Desenvolvimento seguro

- **Branch protegida** em `main`: 1+ review obrigatório, CI verde, sem force-push.
- **Checklist de segurança em todo PR** (ver §4).
- **Threat modeling** (STRIDE) para toda feature nova que toque certificado, pagamento ou novo dado pessoal.
- **Code review humano** obrigatório — revisor diferente do autor.
- **Pair programming** para código que manipula chaves criptográficas.
- **Chaos/security drills** trimestrais.

### 2.10 Resposta a incidentes

- Runbook público interno em `/ops/incident-response.md`.
- Severidade SEV1/SEV2/SEV3 definida; SEV1 aciona on-call em ≤ 15 min.
- **Postmortem blameless** em ≤ 5 dias úteis para qualquer SEV1/SEV2.
- Exercício de simulação (tabletop) a cada 6 meses.

## 3. Ameaças tratadas (OWASP API Top 10 — 2023)

| # | Ameaça | Controle nesta API |
|---|--------|-------------------|
| API1 | Broken Object Level Auth | RBAC + verificação `tenant_id == resource.tenant_id` em toda query |
| API2 | Broken Authentication | OAuth2 + JWT RS256 + rotação + MFA admin |
| API3 | Broken Object Property Level | Pydantic com campos explícitos; nunca `extra="allow"` em response |
| API4 | Unrestricted Resource Consumption | Rate limit + body size + timeout + circuit breaker |
| API5 | Broken Function Level Auth | Scope por rota, decorator obrigatório |
| API6 | Unrestricted Access to Sensitive Flows | Idempotency-Key + quotas por operação fiscal |
| API7 | SSRF | Egress allowlist; proibido aceitar URL arbitrária do cliente |
| API8 | Security Misconfiguration | IaC com `checkov`/`tfsec`; hardening baseline imutável |
| API9 | Improper Inventory | Versionamento `/v1/`; OpenAPI é verdade; endpoints órfãos = CI quebra |
| API10 | Unsafe Consumption of APIs | Validação de resposta das APIs oficiais; circuit breaker; timeouts |

## 4. Checklist obrigatório de PR

Todo PR deve marcar:

- [ ] Não introduz segredo em código, log ou teste.
- [ ] Toda rota nova tem auth + scope + rate limit.
- [ ] Input validado com Pydantic; output sem vazar campos internos.
- [ ] Erros não vazam stacktrace nem detalhes de infra.
- [ ] Logs não contêm PII em claro.
- [ ] Dependências adicionadas passaram em `pip-audit`/`trivy`.
- [ ] Mudanças em fluxo fiscal têm teste de idempotência.
- [ ] Mudanças que tocam certificado A1 foram revisadas por 2 devs.
- [ ] Documento atualizado se contrato OpenAPI mudou.
- [ ] Threat model revisto se surgiu novo vetor.

## 5. Canal de reporte (responsible disclosure)

- E-mail: `security@contabil.exemplo.com` (PGP-encrypted preferido).
- SLA de resposta inicial: **24h úteis**.
- Safe harbor para pesquisadores agindo em boa fé.

---

**Esta regra aplica-se a código, infraestrutura, documentação, dados de teste e qualquer contribuição humana ou automatizada ao projeto.**
