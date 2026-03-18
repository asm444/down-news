# Down News — Design Spec

**Data:** 2026-03-18
**Status:** Aprovado
**Objetivo:** Bot Discord que monitora status de serviços de IA, cloud e infra em tempo real, alertando canais específicos com @here em incidentes críticos.

---

## 1. Visão Geral

Bot de monitoramento passivo baseado em **GitHub Actions** (cron a cada 5 minutos), sem servidor dedicado. Compara estado atual vs. anterior (persistido em branch `status-state`), e envia webhooks Discord quando detecta mudanças.

### Requisitos funcionais
- Monitorar ~15 serviços via APIs de status (statuspage.io) e scraping
- Detectar spikes no Downdetector BR para os mesmos serviços
- Alertar canais Discord separados por categoria de serviço
- Usar @here apenas em incidentes críticos (`major_outage` ou spike >500% Downdetector)
- Registrar histórico de incidentes via git (branch `status-state`)

### Requisitos não-funcionais
- **Custo:** $0 (GitHub Actions free tier, repo público)
- **Latência de detecção:** ≤ 5 minutos
- **Disponibilidade:** Depende do GitHub Actions (SLA ~99.9%)
- **Linguagem:** Python 3.13

---

## 2. Serviços Monitorados

### IA
| Serviço | Status Page | API Type |
|---|---|---|
| Claude (Anthropic) | status.claude.com | statuspage.io |
| ChatGPT (OpenAI) | status.openai.com | statuspage.io |
| Gemini (Google) | status.google.com | Custom JSON |

### Microsoft
| Serviço | Status Page | API Type |
|---|---|---|
| Office 365 / Teams | status.office.com | Custom JSON |
| Azure | status.azure.com | Custom JSON |

### Cloud & Infra
| Serviço | Status Page | API Type |
|---|---|---|
| AWS | health.aws.amazon.com | Custom JSON |
| GCP | status.cloud.google.com | Custom JSON |
| Cloudflare | www.cloudflarestatus.com | statuspage.io |
| Hetzner | status.hetzner.com | statuspage.io |
| GitHub | githubstatus.com | statuspage.io |
| Discord | discordstatus.com | statuspage.io |

### Downdetector BR (scraping)
Mesmos serviços acima — extrai contagem de relatos em tempo real para detectar spikes de usuários BR.

---

## 3. Arquitetura

```
GitHub Actions (cron: */5 * * * *)
        │
        ▼
   monitor.py  (orquestrador)
        │
        ├── services/statuspage.py     # adapter statuspage.io JSON API
        ├── services/google.py         # adapter Google Cloud Status
        ├── services/microsoft.py      # adapter Microsoft Status
        ├── services/aws.py            # adapter AWS Health Dashboard
        └── services/downdetector.py   # scraper Downdetector BR
        │
        ├── state_manager.py           # lê/escreve state.json (branch status-state)
        ├── diff_engine.py             # compara estado anterior vs atual
        └── discord_notifier.py        # monta embeds e envia webhooks
```

### Fluxo de execução

```
1. Ler state.json do branch status-state
2. Para cada serviço: buscar status atual (API ou scrape)
3. Comparar com estado anterior via diff_engine
4. Para cada diferença detectada:
   a. Atualizar state.json
   b. Enviar webhook Discord no canal correto
   c. Se crítico: incluir @here
5. Salvar novo state.json no branch status-state
```

---

## 4. Estrutura do Repositório

```
down-news/
├── .github/
│   └── workflows/
│       └── monitor.yml          # cron job principal
├── services/
│   ├── __init__.py
│   ├── base.py                  # interface ServiceAdapter
│   ├── statuspage.py            # adapter genérico statuspage.io
│   ├── google.py
│   ├── microsoft.py
│   ├── aws.py
│   └── downdetector.py
├── monitor.py                   # orquestrador principal
├── state_manager.py             # persistência no branch status-state
├── diff_engine.py               # lógica de comparação
├── discord_notifier.py          # webhooks Discord
├── config.yml                   # serviços, canais, thresholds
├── requirements.txt
└── README.md
```

---

## 5. Schema de Estado (state.json)

```json
{
  "last_check": "2026-03-18T14:30:00Z",
  "services": {
    "claude": {
      "status": "operational",
      "indicator": "none",
      "components": {
        "claude_api": "operational",
        "claude_ai": "operational"
      },
      "active_incidents": [],
      "downdetector_br": {
        "reports_1h": 12,
        "baseline": 10,
        "spike_ratio": 1.2
      },
      "last_changed": "2026-03-18T10:00:00Z"
    }
  }
}
```

---

## 6. Estrutura Discord

### Canais
```
📂 DOWN NEWS
├── #dn-claude          → Claude / Anthropic
├── #dn-openai          → ChatGPT / OpenAI
├── #dn-gemini          → Gemini / Google AI
├── #dn-microsoft       → Office 365, Azure, Teams
├── #dn-cloud           → AWS, GCP, Cloudflare, Hetzner
├── #dn-dev             → GitHub, Discord
└── #dn-geral           → Resumo + @here em críticos
```

### Formato de Embed

**Incidente crítico:**
```
🔴 [CRÍTICO] Claude API — Outage confirmado           @here
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Componente: claude.ai API
📊 Status: operational → major_outage
🕐 Detectado: 14:32 BRT
🔗 status.claude.com
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📣 Downdetector BR: 1.243 relatos (+890% em 1h)
```

**Degradação:**
```
🟠 [DEGRADADO] OpenAI API — Performance reduzida
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Componente: Chat Completions API
📊 Status: operational → degraded_performance
🕐 Detectado: 09:15 BRT
🔗 status.openai.com
```

**Resolução:**
```
🟢 [RESOLVIDO] Cloudflare — Serviço normalizado
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱ Duração do incidente: 47 minutos
🕐 Resolvido: 11:02 BRT
```

### Níveis de Alerta

| Ícone | Nível | Trigger | Canal | @here |
|---|---|---|---|---|
| 🔴 | Crítico | `major_outage` ou spike Downdetector >500% | canal + #dn-geral | ✅ |
| 🟠 | Degradado | `degraded_performance` ou `partial_outage` | canal específico | ❌ |
| 🟡 | Manutenção | `under_maintenance` | canal específico | ❌ |
| 🟢 | Resolvido | Volta para `operational` | canal específico | ❌ |

---

## 7. Configuração (config.yml)

```yaml
services:
  claude:
    name: "Claude (Anthropic)"
    type: statuspage
    url: "https://status.claude.com"
    discord_channel: dn-claude
    downdetector_slug: "chatbot-anthropic"

  openai:
    name: "ChatGPT (OpenAI)"
    type: statuspage
    url: "https://status.openai.com"
    discord_channel: dn-openai
    downdetector_slug: "chatgpt"

  # ... demais serviços

thresholds:
  downdetector_spike_ratio: 5.0      # 500% acima da baseline = crítico
  downdetector_baseline_hours: 24    # janela para calcular baseline

discord:
  mention_role: "@here"
  timezone: "America/Sao_Paulo"
```

---

## 8. GitHub Actions Workflow

```yaml
name: Down News Monitor
on:
  schedule:
    - cron: '*/5 * * * *'
  workflow_dispatch:            # permite execução manual

jobs:
  monitor:
    runs-on: ubuntu-latest
    permissions:
      contents: write           # para commitar state.json

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: pip install -r requirements.txt
      - run: python monitor.py
        env:
          DISCORD_WEBHOOK_CLAUDE: ${{ secrets.DISCORD_WEBHOOK_CLAUDE }}
          DISCORD_WEBHOOK_OPENAI: ${{ secrets.DISCORD_WEBHOOK_OPENAI }}
          DISCORD_WEBHOOK_GEMINI: ${{ secrets.DISCORD_WEBHOOK_GEMINI }}
          DISCORD_WEBHOOK_MICROSOFT: ${{ secrets.DISCORD_WEBHOOK_MICROSOFT }}
          DISCORD_WEBHOOK_CLOUD: ${{ secrets.DISCORD_WEBHOOK_CLOUD }}
          DISCORD_WEBHOOK_DEV: ${{ secrets.DISCORD_WEBHOOK_DEV }}
          DISCORD_WEBHOOK_GERAL: ${{ secrets.DISCORD_WEBHOOK_GERAL }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 9. Persistência de Estado

O `state.json` é mantido no branch `status-state` do mesmo repositório:

1. No início de cada run: `git fetch origin status-state && git checkout status-state -- state.json`
2. Após processar: commit do `state.json` atualizado no branch `status-state`
3. Branch `main` nunca recebe commits automáticos — mantém código limpo

---

## 10. Tratamento de Erros

- **Timeout de API:** Retry com backoff exponencial (3 tentativas, 2s/4s/8s)
- **API indisponível:** Log de warning, não altera estado anterior
- **Downdetector inacessível:** Alerta apenas via status page oficial, sem dados BR
- **Rate limiting Discord:** Fila de envio com delay de 1s entre webhooks
- **State corrompido:** Recria state.json zerado (próxima run detectará diferenças)

---

## 11. Critérios de Sucesso

- [ ] Detecção de incidente em ≤ 5 minutos após mudança na status page
- [ ] Zero falsos positivos (alertas sem incidente real)
- [ ] Alertas formatados corretamente por categoria no canal certo
- [ ] @here apenas em incidentes críticos confirmados
- [ ] Histórico de incidentes rastreável via git log no branch status-state
- [ ] Custo: $0
