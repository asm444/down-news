# Down News

Bot Discord que monitora status de serviços de IA e infraestrutura em tempo real — **100% gratuito**, sem servidor, via GitHub Actions.

Detecta incidentes em Claude, ChatGPT, Gemini, AWS, Azure, Cloudflare e mais, e envia alertas formatados nos canais certos do Discord. Também monitora o **Downdetector BR** para capturar spikes de relatos de usuários brasileiros antes mesmo das páginas oficiais atualizarem.

---

## Serviços monitorados

| Categoria | Serviço | Canal Discord |
|---|---|---|
| IA | Claude (Anthropic) | `#dn-claude` |
| IA | ChatGPT / OpenAI | `#dn-openai` |
| IA | Gemini (Google) | `#dn-gemini` |
| Microsoft | Office 365 / Teams | `#dn-microsoft` |
| Microsoft | Azure | `#dn-microsoft` |
| Cloud | AWS | `#dn-cloud` |
| Cloud | GCP | `#dn-cloud` |
| Cloud | Cloudflare | `#dn-cloud` |
| Cloud | Hetzner | `#dn-cloud` |
| Dev | GitHub | `#dn-dev` |
| Dev | Discord | `#dn-dev` |

---

## Como funciona

```
GitHub Actions (cron a cada 5 min)
        │
        ▼
   monitor.py consulta APIs de status
        │
        ├── Compara com estado anterior (branch status-state)
        │
        └── Mudança detectada? → Webhook Discord no canal certo
                                      └── Incidente crítico? → @here + #dn-geral
```

Só envia notificação quando **algo muda** — sem spam de status repetido a cada run.

---

## Pré-requisitos

- Conta no **GitHub** (gratuita)
- Servidor **Discord** com permissão de administrador
- Nenhum servidor, nenhuma VPS, nenhum custo

---

## Instalação — Passo a Passo

### Passo 1 — Fork ou clone o repositório

**Opção A — Fork (recomendado):**
1. Clique em **Fork** no topo desta página
2. Escolha sua conta e clique em **Create fork**

**Opção B — Clone e crie um repositório novo:**
```bash
git clone https://github.com/SEU-USUARIO/down-news.git
cd down-news
# Crie um repositório público no GitHub e faça push
git remote set-url origin https://github.com/SEU-USUARIO/down-news.git
git push -u origin main
git push origin status-state
```

---

### Passo 2 — Criar os canais no Discord

No seu servidor Discord, crie os seguintes canais de texto:

```
#dn-claude       → alertas do Claude / Anthropic
#dn-openai       → alertas do ChatGPT / OpenAI
#dn-gemini       → alertas do Gemini / Google
#dn-microsoft    → alertas do Office 365 e Azure
#dn-cloud        → alertas do AWS, GCP, Cloudflare, Hetzner
#dn-dev          → alertas do GitHub e Discord
#dn-geral        → resumo + @here para incidentes críticos
```

> **Dica:** Crie uma categoria chamada `DOWN NEWS` para organizar os canais.

---

### Passo 3 — Criar webhooks no Discord

Para **cada um dos 7 canais**, repita este processo:

1. Clique com o botão direito no canal → **Editar canal**
2. Vá em **Integrações** → **Webhooks** → **Novo Webhook**
3. Dê um nome (ex: `Down News`)
4. Clique em **Copiar URL do Webhook**
5. Guarde a URL — você vai precisar dela no próximo passo

> Cada canal terá sua própria URL única. Não compartilhe essas URLs — quem tiver acesso pode enviar mensagens no seu servidor.

---

### Passo 4 — Adicionar os secrets no GitHub

No repositório do GitHub, vá em:
**Settings → Secrets and variables → Actions → New repository secret**

Adicione os 7 secrets abaixo, colando a URL do webhook correspondente:

| Nome do Secret | Canal Discord |
|---|---|
| `DISCORD_WEBHOOK_DN_CLAUDE` | `#dn-claude` |
| `DISCORD_WEBHOOK_DN_OPENAI` | `#dn-openai` |
| `DISCORD_WEBHOOK_DN_GEMINI` | `#dn-gemini` |
| `DISCORD_WEBHOOK_DN_MICROSOFT` | `#dn-microsoft` |
| `DISCORD_WEBHOOK_DN_CLOUD` | `#dn-cloud` |
| `DISCORD_WEBHOOK_DN_DEV` | `#dn-dev` |
| `DISCORD_WEBHOOK_DN_GERAL` | `#dn-geral` |

---

### Passo 5 — Ativar o workflow

1. No repositório, vá na aba **Actions**
2. Clique em **Down News Monitor** na lista à esquerda
3. Clique em **Enable workflow** (botão azul)

Pronto. O bot vai rodar automaticamente a cada **5 minutos**.

---

### Passo 6 — Testar manualmente

Para confirmar que está tudo configurado antes de esperar o primeiro cron:

1. Vá em **Actions → Down News Monitor**
2. Clique em **Run workflow → Run workflow**
3. Aguarde ~30 segundos
4. Verifique os logs clicando na execução

Se os webhooks estiverem corretos, o bot não vai enviar mensagem na primeira run (não há estado anterior para comparar — comportamento esperado). Na segunda run em diante, qualquer mudança de status gera alerta.

> **Para forçar um alerta de teste:** Edite temporariamente o `state.json` no branch `status-state`, alterando o status de um serviço para `"degraded"`. Na próxima run, quando a API retornar `"operational"`, um alerta de resolução será disparado.

---

## Tipos de alerta

| Ícone | Nível | Quando dispara | @here |
|---|---|---|---|
| 🔴 | **Crítico** | `major_outage` ou spike Downdetector >500% | ✅ |
| 🟠 | **Degradado** | `degraded_performance` ou `partial_outage` | ❌ |
| 🟡 | **Manutenção** | `under_maintenance` | ❌ |
| 🟢 | **Resolvido** | Serviço volta para `operational` | ❌ |

### Exemplo de mensagem crítica

```
🔴 [CRÍTICO] Claude (Anthropic)                          @here
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Incidente: API Outage
📊 Status: operational → major_outage
🕐 Detectado: 14:32 BRT
📣 Downdetector BR: 1.243 relatos (+890%)
🔗 https://status.claude.com
```

### Exemplo de mensagem de resolução

```
🟢 [RESOLVIDO] ChatGPT (OpenAI)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱ Status anterior: minor
🕐 Resolvido: 15:19 BRT
```

---

## Personalização

### Usando o wizard interativo (recomendado)

```bash
python start.py
```

O wizard permite adicionar, editar e remover serviços sem editar o YAML manualmente. Ao sair, mostra exatamente quais secrets do GitHub precisam ser criados.

---

### Editando o config.yml manualmente

#### Adicionar um serviço com status page oficial

```yaml
services:
  netflix:
    name: "Netflix"
    type: statuspage          # statuspage | google | microsoft | aws | google_cloud
    base_url: "https://status.netflix.com"
    discord_channel: dn-geral
    downdetector:
      br: "netflix"           # slug do downdetector.com.br/status/netflix/
      global: "netflix"       # slug do downdetector.com/status/netflix/
```

#### Adicionar um serviço somente pelo Downdetector

Para serviços sem status page oficial, use o tipo `downdetector_only`:

```yaml
services:
  whatsapp:
    name: "WhatsApp"
    type: downdetector_only
    discord_channel: dn-geral
    downdetector:
      br: "whatsapp"
      global: "whatsapp"
```

#### Monitorar apenas uma região do Downdetector

Omita a chave da região que não quer monitorar:

```yaml
downdetector:
  br: "hetzner-online"    # só BR — sem "global:"
```

#### Remover um serviço

Apague a entrada correspondente do `config.yml`.

### Ajustar o threshold do Downdetector

Por padrão, um spike de **5x** (500%) acima da média das últimas 24h é considerado crítico. Para mudar:

```yaml
thresholds:
  downdetector_spike_ratio: 3.0   # 300% já é considerado crítico
```

### Mudar a frequência de verificação

Edite `.github/workflows/monitor.yml`:

```yaml
on:
  schedule:
    - cron: '*/10 * * * *'  # a cada 10 minutos
```

> O GitHub Actions tem limite de 500 minutos/mês no plano gratuito para repositórios privados. Para repos **públicos** não há limite. A cada 5 minutos em repo público = ~4.320 runs/mês, cada uma levando ~20s = ~1.440 minutos/mês — dentro do limite gratuito mesmo em repo privado.

---

## Histórico de incidentes

O bot versiona automaticamente o estado de todos os serviços. Para consultar:

```bash
# Ver histórico de mudanças de estado
git log origin/status-state --oneline

# Ver estado em um momento específico
git show origin/status-state:state.json | python -m json.tool

# Ver o estado atual de todos os serviços
git fetch origin status-state
git show FETCH_HEAD:state.json | python -m json.tool
```

---

## Desenvolvimento local

```bash
# Clonar e configurar ambiente
git clone https://github.com/SEU-USUARIO/down-news.git
cd down-news
python -m venv venv
source venv/bin/activate       # Linux/macOS
# venv\Scripts\activate        # Windows

pip install -r requirements-dev.txt

# Rodar os testes
pytest tests/ -v

# Rodar o monitor localmente (sem enviar para Discord)
# Crie um arquivo .env com os webhooks (não commite este arquivo)
export DISCORD_WEBHOOK_DN_CLAUDE="https://discord.com/api/webhooks/..."
python monitor.py
```

---

## Troubleshooting

### O bot não envia nenhuma mensagem

- Verifique se os secrets estão criados corretamente em **Settings → Secrets → Actions**
- Na primeira run, nenhuma mensagem é enviada (sem estado anterior para comparar) — isso é esperado
- Verifique os logs da Action em **Actions → Down News Monitor → [última execução]**

### O workflow não aparece na aba Actions

- GitHub Actions só ativa workflows novos após o primeiro push do arquivo `.github/workflows/monitor.yml`
- Vá em **Actions** e clique em **Enable workflow** se aparecer o botão

### Erro `git checkout status-state` nos logs

- O branch `status-state` precisa existir no remoto
- Execute: `git push origin status-state`

### Downdetector não está detectando nada

- O Downdetector pode bloquear scraping ocasionalmente (retorna 403/429)
- Quando bloqueado, o bot usa apenas as APIs oficiais de status — comportamento esperado
- Os logs da Action mostrarão `HTTP 403 (possível bloqueio de scraping)`

### Quero receber @everyone em vez de @here

Edite `discord_notifier.py`, linha com `"@here"`, e substitua por `"@everyone"`.

---

## Estrutura do projeto

```
down-news/
├── monitor.py              # orquestrador — ponto de entrada
├── diff_engine.py          # lógica de detecção de mudanças
├── discord_notifier.py     # formatação e envio de webhooks
├── state_manager.py        # persistência de estado no branch status-state
├── config.yml              # lista de serviços e configurações
├── services/
│   ├── base.py             # interface ServiceAdapter
│   ├── statuspage.py       # adapter para APIs statuspage.io
│   ├── google.py           # adapter para Google Status
│   ├── microsoft.py        # adapter para Microsoft Status
│   ├── aws.py              # adapter para AWS Health Dashboard
│   └── downdetector.py     # scraper do Downdetector BR
├── tests/                  # 18 testes cobrindo todos os módulos
└── .github/workflows/
    └── monitor.yml         # cron job GitHub Actions
```
