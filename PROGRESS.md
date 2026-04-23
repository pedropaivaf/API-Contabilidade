# PROGRESS — Onde paramos

> Este arquivo é atualizado a cada sessão. Se você é Claude/Claude Code lendo isto em nova máquina: leia junto com `CONTEXT.md` e `SEMANA-1-CHECKLIST.md`.

**Nome oficial do projeto:** Ábaco
**Repositório:** https://github.com/pedropaivaf/API-Contabilidade
**Última sessão:** 2026-04-23

## Estado atual — Semana 1

### ✅ Concluído

- Repositório GitHub público criado e populado.
- CI verde (ruff, bandit, semgrep, trivy, gitleaks, pip-audit, pytest).
- Skeleton FastAPI + MCP server + adapters SERPRO/Focus NFe.
- ADRs 001, 002, 003 + SECURITY.md + CAPABILITIES.md.
- **Neon Postgres** criado em `sa-east-1` (São Paulo). Projeto: `abaco`, endpoint `ep-nameless-mountain-acua0zyy`.
- **Upstash Redis** criado em `sa-east-1` (São Paulo). Database: `abaco`.
- `.env` local preenchido com `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`. **Nunca commitado.**
- `flyctl` (CLI do Fly.io) instalado na máquina do Pedro.
- `fly auth login` concluído — logado como `pedro.p.ferreira@hotmail.com`.

### 🟡 Bloqueado

- **`fly launch` falhou** — conta marcada como "high risk" pelo antifraude do Fly (comum para contas BR novas).
  - Próxima ação: Pedro preenche formulário em https://fly.io/high-risk-unlock com descrição do projeto.
  - Tempo estimado de liberação: minutos a algumas horas.
  - **Plano B**, se negarem: migrar para Railway.app ou Render.com (ambos aceitam contas BR sem fricção).

### ⏳ Pendente (aguardando Pedro)

- Conta Sentry (criar em https://sentry.io/signup — rápido, sem antifraude).
- Resposta do responsável técnico do escritório com as 3 informações do `PEDIDO-INFO.md`:
  1. Consumer Key + Consumer Secret SERPRO **sandbox**.
  2. Certificado A1 do escritório (`.pfx` + senha).
  3. Confirmação de cobertura sandbox no contrato SERPRO.

## Próxima ação (quando retomar)

1. Verificar se a conta Fly.io foi desbloqueada (e-mail).
2. Se **sim**: rodar `fly launch --name abaco-dev --region gru --no-deploy` dentro de `C:\projects\api-contabil`.
3. Se **negado**: avisar o Claude e executar plano B (Railway.app).

### Sequência depois do `fly launch` bem-sucedido

```bash
cd /c/projects/api-contabil

# Setar secrets no Fly (carrega do .env local)
fly secrets set \
  DATABASE_URL="$(grep ^DATABASE_URL .env | cut -d= -f2-)" \
  REDIS_URL="$(grep ^REDIS_URL .env | cut -d= -f2-)" \
  JWT_SECRET="$(grep ^JWT_SECRET .env | cut -d= -f2-)"

# Deploy
fly deploy

# Testar health
curl https://abaco-dev.fly.dev/health
```

Esperado: `{"status":"ok"}`.

## Passos locais para retomar em outra máquina

1. Clonar o repo:
   ```bash
   git clone https://github.com/pedropaivaf/API-Contabilidade.git
   cd API-Contabilidade
   ```
2. Recriar o `.env` a partir do `.env.example`:
   ```bash
   cp .env.example .env
   # Editar com os valores reais (DATABASE_URL, REDIS_URL, JWT_SECRET)
   ```
3. Valores do `.env` estão no **gerenciador de senhas pessoal do Pedro** (1Password / Bitwarden / Doppler). Eles NÃO estão neste repositório — isso é correto por design.
4. Instalar dependências e CLIs:
   ```bash
   pip install -r requirements.txt
   # Windows: instalar fly CLI via PowerShell
   #   iwr https://fly.io/install.ps1 -useb | iex
   # Depois: fly auth login
   ```
5. Continuar a partir da seção "Próxima ação" acima.

## Histórico de decisões desde a última sessão

| Decisão | Motivo |
|--------|--------|
| Nome do projeto: **Ábaco** | Remete ao instrumento histórico de contabilidade, curto, forte, domínio viável |
| Neon em `sa-east-1` | São Paulo disponível, LGPD OK |
| Upstash em `sa-east-1` | São Paulo disponível também |
| Fly.io em `gru` (São Paulo) | LGPD + menor latência para clientes brasileiros |
| `.env` fora do Git | Padrão, reforçado por `.gitignore` e `pre-commit gitleaks` |
| `fly launch --no-deploy` | Criar app primeiro, setar secrets, depois deployar |

## Contexto rápido para um novo Claude

Pedro é solo dev em escritório contábil com 200+ CNPJs (70% Simples Nacional), 28 pessoas no time. Chefe administra credenciais SERPRO. Projeto é uma API-hub (REST + MCP) que substitui robôs/RPA integrando SERPRO + Focus NFe + LegisWeb + Questor + Acessorias. Stack: Python/FastAPI + Neon + Upstash + Fly.io. Primeiro cliente: o próprio escritório. Depois vender para outros.

**Regra mandatória:** `SECURITY.md` tem precedência sobre qualquer decisão. Segredos em KMS/Vault, nunca em código ou logs.
