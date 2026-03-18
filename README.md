# Down News

Bot Discord de monitoramento de status de IA e infraestrutura, 100% gratuito via GitHub Actions.

## Serviços monitorados

| Categoria | Serviço | Canal Discord |
|---|---|---|
| IA | Claude (Anthropic) | `#dn-claude` |
| IA | ChatGPT (OpenAI) | `#dn-openai` |
| IA | Gemini (Google) | `#dn-gemini` |
| Microsoft | Office 365 / Teams | `#dn-microsoft` |
| Microsoft | Azure | `#dn-microsoft` |
| Cloud | AWS | `#dn-cloud` |
| Cloud | GCP | `#dn-cloud` |
| Cloud | Cloudflare | `#dn-cloud` |
| Cloud | Hetzner | `#dn-cloud` |
| Dev | GitHub | `#dn-dev` |
| Dev | Discord | `#dn-dev` |

Todos os serviços também são monitorados no **Downdetector BR** para detectar spikes de relatos de usuários brasileiros.

## Como funciona

1. GitHub Actions executa `monitor.py` a cada **5 minutos** (gratuito)
2. O script consulta as APIs de status de cada serviço
3. Compara com o estado anterior (salvo em `state.json` no branch `status-state`)
4. Envia webhook Discord apenas quando detecta **mudança de estado**
5. Incidentes críticos enviam `@here` no canal do serviço + `#dn-geral`

## Configuração

### 1. Canais Discord

Crie os seguintes canais no seu servidor Discord:
- `#dn-claude`, `#dn-openai`, `#dn-gemini`
- `#dn-microsoft`, `#dn-cloud`, `#dn-dev`
- `#dn-geral` (alertas críticos com @here)

### 2. Webhooks Discord

Para cada canal, crie um webhook:
`Configurações do canal → Integrações → Webhooks → Novo Webhook`

### 3. Secrets do GitHub

Adicione os webhooks como secrets no repositório:
`Settings → Secrets and variables → Actions → New repository secret`

| Secret | Canal |
|---|---|
| `DISCORD_WEBHOOK_DN_CLAUDE` | `#dn-claude` |
| `DISCORD_WEBHOOK_DN_OPENAI` | `#dn-openai` |
| `DISCORD_WEBHOOK_DN_GEMINI` | `#dn-gemini` |
| `DISCORD_WEBHOOK_DN_MICROSOFT` | `#dn-microsoft` |
| `DISCORD_WEBHOOK_DN_CLOUD` | `#dn-cloud` |
| `DISCORD_WEBHOOK_DN_DEV` | `#dn-dev` |
| `DISCORD_WEBHOOK_DN_GERAL` | `#dn-geral` |

### 4. Ativar Actions

Após fazer push, vá em `Actions → Down News Monitor → Enable workflow`.

## Tipos de alerta

| Ícone | Nível | Trigger | @here |
|---|---|---|---|
| 🔴 | Crítico | `major_outage` ou spike Downdetector >500% | ✅ |
| 🟠 | Degradado | `degraded_performance` ou `partial_outage` | ❌ |
| 🟡 | Manutenção | `under_maintenance` | ❌ |
| 🟢 | Resolvido | Volta para `operational` | ❌ |

## Histórico de incidentes

O histórico completo fica no branch `status-state` — cada run commita o `state.json` atualizado, criando um log auditável de todos os status.

## Desenvolvimento local

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pytest tests/ -v
```
