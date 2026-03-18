#!/usr/bin/env python3
"""
Down News — Wizard de configuração interativo.

Configure serviços monitorados, regiões do Downdetector e canais Discord
sem editar o config.yml manualmente.

Uso: python start.py   ← sem precisar instalar nada antes
"""
import sys
import os
import re
import subprocess


def _bootstrap():
    """Garante que PyYAML está disponível, instalando se necessário."""
    try:
        import yaml  # noqa: F401
        return
    except ImportError:
        pass

    print("  PyYAML não encontrado — instalando automaticamente...")

    # Tenta instalar no ambiente atual (venv ou sistema)
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "pyyaml", "-q"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("  PyYAML instalado com sucesso.\n")
        return

    # Fallback: instala só para o usuário atual
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "pyyaml", "--user", "-q"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("  PyYAML instalado (--user) com sucesso.\n")
        return

    print("  Não foi possível instalar PyYAML automaticamente.")
    print("  Execute manualmente: pip install pyyaml")
    sys.exit(1)


_bootstrap()
import yaml  # noqa: E402 — importado após bootstrap garantido

CONFIG_FILE = "config.yml"

# ─── Paleta de cores no terminal ─────────────────────────────────────────────

def _c(code: str, text: str) -> str:
    """Aplica cor ANSI se o terminal suportar."""
    if not sys.stdout.isatty():
        return text
    codes = {
        "bold": "\033[1m", "green": "\033[92m", "yellow": "\033[93m",
        "red": "\033[91m", "cyan": "\033[96m", "dim": "\033[2m", "reset": "\033[0m",
    }
    return f"{codes.get(code, '')}{text}{codes['reset']}"


def header(title: str):
    print(f"\n{_c('bold', '━' * 50)}")
    print(f"  {_c('bold', title)}")
    print(f"{_c('bold', '━' * 50)}")


def info(msg: str):
    print(f"  {_c('cyan', '→')} {msg}")


def ok(msg: str):
    print(f"  {_c('green', '✓')} {msg}")


def warn(msg: str):
    print(f"  {_c('yellow', '!')} {msg}")


def err(msg: str):
    print(f"  {_c('red', '✗')} {msg}")


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return _default_config()
    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f) or _default_config()


def save_config(config: dict):
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    ok(f"Configuração salva em {CONFIG_FILE}")


def _default_config() -> dict:
    return {
        "services": {},
        "thresholds": {
            "downdetector_spike_ratio": 5.0,
            "downdetector_baseline_hours": 24,
            "request_timeout": 10,
            "retry_attempts": 3,
            "retry_backoff": 2,
        },
        "discord": {
            "mention": "@here",
            "timezone": "America/Sao_Paulo",
            "delay_between_webhooks": 1,
        },
        "channels": ["dn-geral"],
    }


# ─── Helpers de input ─────────────────────────────────────────────────────────

def ask(prompt: str, default: str = "") -> str:
    hint = f" [{_c('dim', default)}]" if default else ""
    try:
        value = input(f"  {prompt}{hint}: ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)
    return value if value else default


def ask_yes(prompt: str, default: bool = True) -> bool:
    hint = "S/n" if default else "s/N"
    try:
        value = input(f"  {prompt} [{hint}]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)
    if not value:
        return default
    return value in ("s", "sim", "y", "yes")


def choose(prompt: str, options: list) -> str:
    """Exibe menu numerado e retorna a opção escolhida."""
    for i, opt in enumerate(options, 1):
        print(f"  {_c('cyan', str(i))}) {opt}")
    while True:
        raw = ask(prompt)
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        err(f"Digite um número entre 1 e {len(options)}")


def _slug_hint(name: str) -> str:
    """Sugere um slug a partir do nome do serviço."""
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")


# ─── Ações do menu ────────────────────────────────────────────────────────────

SERVICE_TYPES = [
    ("statuspage", "Status Page padrão (Anthropic, GitHub, Cloudflare, Discord...)"),
    ("google",     "Google Status (Gemini, Google APIs)"),
    ("google_cloud", "Google Cloud Status (GCP, Vertex AI)"),
    ("microsoft",  "Microsoft Status (Office 365, Teams, Outlook)"),
    ("azure",      "Azure Status"),
    ("aws",        "AWS Health Dashboard"),
    ("downdetector_only", "Somente Downdetector (sem status page oficial)"),
]


def list_services(config: dict):
    header("Serviços configurados")
    services = config.get("services", {})
    if not services:
        warn("Nenhum serviço configurado ainda.")
        return
    for sid, svc in services.items():
        dd = svc.get("downdetector", {})
        dd_info = []
        if dd.get("br"):
            dd_info.append(f"🇧🇷 BR: {dd['br']}")
        if dd.get("global"):
            dd_info.append(f"🌍 Global: {dd['global']}")
        dd_str = f"  ({', '.join(dd_info)})" if dd_info else ""
        svc_type = svc.get("type", "?")
        channel = svc.get("discord_channel", "?")
        print(f"\n  {_c('bold', sid)}")
        print(f"    Nome:    {svc.get('name', '?')}")
        print(f"    Tipo:    {svc_type}")
        if svc.get("base_url"):
            print(f"    URL:     {svc.get('base_url')}")
        print(f"    Canal:   #{channel}")
        if dd_info:
            print(f"    Downdetector:{dd_str}")


def add_service(config: dict):
    header("Adicionar serviço")

    print(f"\n  {_c('bold', 'Tipo de monitoramento:')}")
    type_labels = [label for _, label in SERVICE_TYPES]
    chosen_label = choose("Escolha o tipo", type_labels)
    svc_type = next(t for t, l in SERVICE_TYPES if l == chosen_label)

    name = ask("Nome do serviço (ex: Netflix)")
    if not name:
        err("Nome obrigatório.")
        return

    service_id = ask("ID do serviço (chave interna, sem espaços)", _slug_hint(name))
    if service_id in config.get("services", {}):
        err(f"Serviço '{service_id}' já existe. Use 'Editar serviço' para modificar.")
        return

    svc: dict = {"name": name, "type": svc_type}

    if svc_type != "downdetector_only":
        base_url = ask("URL da status page (ex: https://status.exemplo.com)")
        if base_url:
            svc["base_url"] = base_url

    # Canal Discord
    channels = config.get("channels", ["dn-geral"])
    print(f"\n  {_c('bold', 'Canal Discord:')}")
    info("Canais disponíveis: " + ", ".join(f"#{c}" for c in channels))
    channel_choice = ask("Canal (ou novo nome sem #)", "dn-geral")
    channel_choice = channel_choice.lstrip("#")
    svc["discord_channel"] = channel_choice
    if channel_choice not in channels:
        channels.append(channel_choice)
        config["channels"] = channels
        ok(f"Canal #{channel_choice} adicionado à lista. Crie-o no Discord e adicione o webhook.")

    # Downdetector
    print(f"\n  {_c('bold', 'Downdetector:')}")
    info("Informe os slugs para as regiões que deseja monitorar.")
    info("O slug é a parte final da URL: downdetector.com.br/status/SLUG/")
    info("Deixe em branco para não monitorar aquela região.")

    dd: dict = {}
    slug_br = ask("Slug no Downdetector BR (downdetector.com.br)", _slug_hint(name))
    if slug_br:
        dd["br"] = slug_br
    slug_global = ask("Slug no Downdetector Global (downdetector.com)", _slug_hint(name))
    if slug_global:
        dd["global"] = slug_global

    if dd:
        svc["downdetector"] = dd

    config.setdefault("services", {})[service_id] = svc
    ok(f"Serviço '{name}' ({service_id}) adicionado.")

    if channel_choice not in [c.lstrip("#") for c in config.get("channels", [])]:
        _remind_webhook(channel_choice)


def edit_downdetector(config: dict):
    """Edita apenas os slugs do Downdetector de um serviço existente."""
    header("Editar Downdetector de serviço existente")
    services = config.get("services", {})
    if not services:
        warn("Nenhum serviço configurado.")
        return

    service_names = [f"{sid} ({svc.get('name', '?')})" for sid, svc in services.items()]
    chosen = choose("Qual serviço deseja editar?", service_names)
    service_id = chosen.split(" ")[0]
    svc = services[service_id]

    dd = svc.get("downdetector", {})
    print(f"\n  {_c('bold', 'Slugs atuais:')}")
    print(f"    🇧🇷 BR:     {dd.get('br', _c('dim', 'não configurado'))}")
    print(f"    🌍 Global:  {dd.get('global', _c('dim', 'não configurado'))}")

    print(f"\n  {_c('bold', 'Novos slugs')} (Enter para manter o atual, 'X' para remover):")
    info("Slug é a parte final da URL: downdetector.com.br/status/SLUG/")

    slug_br = ask("🇧🇷  Downdetector BR", dd.get("br", ""))
    slug_global = ask("🌍 Downdetector Global", dd.get("global", ""))

    new_dd = {}
    if slug_br and slug_br.upper() != "X":
        new_dd["br"] = slug_br
    if slug_global and slug_global.upper() != "X":
        new_dd["global"] = slug_global

    svc["downdetector"] = new_dd
    ok(f"Downdetector de '{svc['name']}' atualizado.")


def remove_service(config: dict):
    header("Remover serviço")
    services = config.get("services", {})
    if not services:
        warn("Nenhum serviço configurado.")
        return

    service_names = [f"{sid} ({svc.get('name', '?')})" for sid, svc in services.items()]
    chosen = choose("Qual serviço remover?", service_names)
    service_id = chosen.split(" ")[0]
    name = services[service_id].get("name", service_id)

    if ask_yes(f"Confirma remoção de '{name}' ({service_id})?", default=False):
        del config["services"][service_id]
        ok(f"Serviço '{name}' removido.")
    else:
        info("Cancelado.")


def show_webhooks(config: dict):
    header("Webhooks Discord necessários")
    channels = config.get("channels", [])
    used_channels = set()
    for svc in config.get("services", {}).values():
        ch = svc.get("discord_channel")
        if ch:
            used_channels.add(ch)
    used_channels.add("dn-geral")

    all_channels = sorted(used_channels | set(channels))
    print(f"\n  Crie estes secrets em: {_c('cyan', 'Settings → Secrets → Actions')}\n")
    for ch in all_channels:
        env_name = f"DISCORD_WEBHOOK_{ch.upper().replace('-', '_')}"
        print(f"  {_c('bold', env_name)}")
        print(f"  {_c('dim', f'→ webhook do canal #{ch}')}\n")

    info("Como criar um webhook no Discord:")
    info("Canal → Editar → Integrações → Webhooks → Novo Webhook → Copiar URL")


def edit_thresholds(config: dict):
    header("Configurar thresholds")
    t = config.setdefault("thresholds", {})

    current_ratio = t.get("downdetector_spike_ratio", 5.0)
    print(f"\n  Spike Downdetector atual: {_c('bold', str(current_ratio))}x")
    info("Exemplo: 5.0 = alerta quando relatos atingem 500% acima da média das últimas 24h")
    new_ratio = ask("Novo valor (ex: 3.0 para mais sensível, 10.0 para menos)", str(current_ratio))
    try:
        t["downdetector_spike_ratio"] = float(new_ratio)
        ok(f"Threshold definido para {t['downdetector_spike_ratio']}x")
    except ValueError:
        err("Valor inválido — mantendo o atual.")


def _remind_webhook(channel: str):
    env_name = f"DISCORD_WEBHOOK_{channel.upper().replace('-', '_')}"
    warn(f"Lembre de criar o secret {_c('bold', env_name)} no GitHub.")
    warn(f"Canal Discord: #{channel}")


# ─── Menu principal ───────────────────────────────────────────────────────────

MENU_OPTIONS = [
    "Listar serviços configurados",
    "Adicionar serviço",
    "Editar Downdetector de um serviço",
    "Remover serviço",
    "Ver webhooks Discord necessários",
    "Configurar thresholds",
    "Salvar e sair",
    "Sair sem salvar",
]


def main():
    print(f"\n{_c('bold', '╔══════════════════════════════════╗')}")
    print(f"{_c('bold', '║     DOWN NEWS — Configuração     ║')}")
    print(f"{_c('bold', '╚══════════════════════════════════╝')}")

    config = load_config()
    n_services = len(config.get("services", {}))
    info(f"{n_services} serviço(s) configurado(s) em {CONFIG_FILE}")
    changed = False

    while True:
        header("Menu principal")
        action = choose("O que deseja fazer?", MENU_OPTIONS)

        if action == "Listar serviços configurados":
            list_services(config)

        elif action == "Adicionar serviço":
            add_service(config)
            changed = True

        elif action == "Editar Downdetector de um serviço":
            edit_downdetector(config)
            changed = True

        elif action == "Remover serviço":
            remove_service(config)
            changed = True

        elif action == "Ver webhooks Discord necessários":
            show_webhooks(config)

        elif action == "Configurar thresholds":
            edit_thresholds(config)
            changed = True

        elif action == "Salvar e sair":
            save_config(config)
            print()
            ok("Pronto! Faça push do config.yml atualizado para o GitHub.")
            info("git add config.yml && git commit -m 'config: atualizar serviços' && git push")
            break

        elif action == "Sair sem salvar":
            if changed:
                if not ask_yes("Há alterações não salvas. Deseja mesmo sair?", default=False):
                    continue
            break

    print()


if __name__ == "__main__":
    main()
