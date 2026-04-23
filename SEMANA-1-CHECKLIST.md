# Semana 1 — Checklist

**Meta:** ao fim da semana, a sua API está **hospedada em produção** e responde `GET /v1/cadastro/cnpj/{cnpj}` usando o **sandbox do SERPRO**, com KMS, audit log e CI rodando. É a menor fatia que prova a stack inteira.

Divisão de trabalho:
- **[P]** → Pedro executa (precisa de você, CNPJ ou chefe).
- **[C]** → Claude executa (código, configs, docs).
- **[P+C]** → juntos em sessão de 30-60 min.

Marque com `[x]` o que estiver pronto.

---

## Dia 1 — Contas e credenciais (Pedro)

- [ ] **[P]** Criar conta no **GitHub** (se ainda não tiver) e um repositório privado `api-contabil`.
- [ ] **[P]** Criar conta **Fly.io** (https://fly.io). Adicionar cartão de crédito — a cobrança só ativa ao passar do free tier.
- [ ] **[P]** Criar conta **Neon** (https://neon.tech) — free tier para começar.
- [ ] **[P]** Criar conta **Upstash** (https://upstash.com) — Redis pay-per-use.
- [ ] **[P]** Criar conta **AWS** (só usaremos KMS). Se for intimidador, pode começar com o **KMS do Fly.io** (via `fly secrets`) e migrar para AWS KMS na semana 3.
- [ ] **[P]** Criar conta **Sentry** (free) e **Axiom** (free) — observabilidade.
- [ ] **[P]** Criar conta **Cloudflare** (free) e registrar um domínio pra API (ex.: `api-contabil.com.br` ou similar). Pode esperar para semana 2 se quiser.
- [ ] **[P]** Criar conta **Doppler** (https://doppler.com, free tier) para gestão de segredos.
- [ ] **[P]** Instalar localmente: `git`, `python 3.12`, `docker`, `fly` CLI, `gh` CLI.

## Dia 1-2 — Pedido de credencial SERPRO (Pedro + chefe)

- [ ] **[P]** Falar com o chefe e solicitar:
  - Acesso ao painel do Integra Contador para **gerar credenciais de sandbox** (Consumer Key + Consumer Secret).
  - Confirmar que o CNPJ do escritório tem contrato ativo com SERPRO e pode abrir sandbox.
  - Pegar o **certificado A1 do escritório** para uso em desenvolvimento (cópia do `.pfx` + senha, em canal seguro).
- [ ] **[P]** Salvar credenciais/certificado em local seguro (Doppler ou 1Password). **NUNCA** no `.env` comitado.

> E-mail modelo para mandar ao chefe está no final deste arquivo.

## Dia 2 — Subir repositório (Pedro + Claude)

- [ ] **[P+C]** Criar repositório GitHub privado `api-contabil`.
- [ ] **[P]** Fazer o primeiro push com o conteúdo da pasta `outputs/` atual.
  ```bash
  cd outputs
  git init -b main
  git add .
  git commit -m "chore: initial scaffold, ADRs e SECURITY baseline"
  gh repo create api-contabil --private --source=. --push
  ```
- [ ] **[P]** Habilitar **branch protection** em `main` (1 review obrigatório — mesmo sendo solo, força passar por PR).
- [ ] **[C]** Gerar arquivos que faltam para CI rodar (`.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `fly.toml`, `.gitignore`) — **já no projeto**.
- [ ] **[P]** Rodar `pre-commit install` local.

## Dia 3 — Infra base hospedada (Pedro + Claude)

- [ ] **[P]** Provisionar no Neon:
  - Projeto `api-contabil`, branch `main` (prod) e `dev`.
  - Copiar `DATABASE_URL` de cada branch.
- [ ] **[P]** Provisionar no Upstash:
  - Database Redis em `sa-east-1` (São Paulo) — LGPD.
  - Copiar `REDIS_URL`.
- [ ] **[P]** Criar app no Fly.io:
  ```bash
  fly launch --name api-contabil-dev --region gru --no-deploy
  ```
  Selecionar região `gru` (São Paulo). Não deployar ainda.
- [ ] **[P]** Configurar secrets no Fly (ou Doppler):
  ```bash
  fly secrets set \
    DATABASE_URL="..." \
    REDIS_URL="..." \
    SERPRO_CLIENT_ID="..." \
    SERPRO_CLIENT_SECRET="..." \
    SERPRO_CERT_PFX_BASE64="$(base64 -w0 cert_a1.pfx)" \
    SERPRO_CERT_PASSWORD="..."
  ```

## Dia 4 — Adapter SERPRO real e primeira chamada (Pedro + Claude)

- [ ] **[C]** Atualizar `app/adapters/serpro.py` para:
  - Carregar certificado de `SERPRO_CERT_PFX_BASE64` decodificado em memória (nunca disco).
  - Apontar para URL de sandbox (não produção).
  - Cache do token OAuth2 em memória com TTL.
- [ ] **[C]** Adicionar teste `tests/test_serpro_sandbox.py` que faz `consultar_cnpj` e valida payload.
- [ ] **[P+C]** Rodar local:
  ```bash
  docker compose up --build
  curl http://localhost:8000/v1/cadastro/cnpj/00000000000191   # Banco do Brasil, CNPJ público
  ```
- [ ] **[P]** Se funcionar local, deploy:
  ```bash
  fly deploy
  ```
- [ ] **[P]** Testar endpoint público:
  ```bash
  curl https://api-contabil-dev.fly.dev/v1/cadastro/cnpj/00000000000191
  ```

## Dia 5 — Audit log + observabilidade (Pedro + Claude)

- [ ] **[C]** Adicionar middleware de audit log (estruturado JSON) em `app/infra/audit.py`. Cada request grava: timestamp, tenant, endpoint, request_id, resultado, fingerprint do cert usado.
- [ ] **[C]** Integrar Sentry (captura erros) no `main.py`.
- [ ] **[C]** Integrar Axiom (logs estruturados) — via `AXIOM_TOKEN`.
- [ ] **[P]** Fazer 5 chamadas de teste e validar que os logs aparecem em Axiom e nenhum erro aparece em Sentry.

## Sexta — Revisão de segurança (Claude)

- [ ] **[C]** Rodar o skill `engineering:review` sobre o diff da semana, focado em:
  - Vazamento de segredo.
  - Logs com CNPJ em claro.
  - Handling de erro que vaza stacktrace.
  - Falha ao zerar buffer do PFX após uso.
- [ ] **[P]** Aplicar correções sugeridas e abrir PR.
- [ ] **[P]** Mergear `main` com o resultado da semana.

---

## Critérios de aceite da Semana 1

No final da sexta, você deve conseguir:

1. `curl https://api-contabil-dev.fly.dev/v1/cadastro/cnpj/00000000000191` → 200 com dados reais do SERPRO sandbox.
2. CI verde no GitHub a cada push.
3. Sentry sem erros; Axiom com logs estruturados.
4. Nenhum secret comitado no repositório.
5. `SECURITY.md` marcado como lido; primeiro PR com checklist de segurança preenchido.

---

## E-mail modelo para o chefe

```
Assunto: Credenciais SERPRO sandbox + certificado A1 para projeto de automação

[Nome do chefe],

Estou começando o desenvolvimento de uma API interna para automatizar
emissões do SERPRO (DAS, PGDAS, DCTFWeb, consultas cadastrais) — objetivo
é reduzir o tempo que o time gasta com emissões manuais e eventualmente
vender essa automação para outros escritórios.

Para a primeira semana, preciso de três coisas:

1. Credenciais de *sandbox* do SERPRO Integra Contador — Consumer Key e
   Consumer Secret separadas da produção. Posso pegar no painel ou você
   me passa em canal seguro (1Password / mensagem criptografada).

2. Uma cópia do certificado digital A1 do escritório (arquivo .pfx + senha)
   para uso exclusivo em desenvolvimento. Garanto:
   - Nunca grava em disco.
   - Guardado em KMS criptografado, só em memória durante uso.
   - Toda leitura gera log auditável.

3. Confirmação de que o contrato SERPRO atual cobre sandbox ou precisa
   contratar à parte (normalmente é grátis).

Quando o primeiro teste for verde, faço uma demo para você ver como ficou.

Obrigado,
Pedro
```

---

## O que vem depois (preview)

- **Semana 2:** onboarding A1 real via upload + primeira emissão DAS.
- **Semana 3:** emissão em lote + adapter Questor (gravar lançamento).
- **Semana 4:** produção + MCP server acessível do Claude Desktop.
