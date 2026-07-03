"""
Verificador de atualizações do PyFlow RPA.
Consulta a GitHub Releases API em background e notifica a UI quando
uma versão mais nova estiver disponível.
"""
from __future__ import annotations

import threading
from typing import Callable

import requests

from version import __version__, GITHUB_REPO


def _parse_version(v: str) -> tuple[int, ...]:
    """Converte '1.2.3' em (1, 2, 3) para comparação."""
    v = v.lstrip("v").strip()
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return (0,)


def check_for_update(on_update_available: Callable[[str, str, str], None],
                     timeout: int = 6) -> None:
    """
    Verifica atualizações em background.

    Parâmetros
    ----------
    on_update_available : callable(latest_version, release_url, release_notes)
        Chamado na thread de worker quando há versão mais nova.
        A UI deve usar QTimer/signal para executar no thread principal.
    timeout : int
        Timeout em segundos para a requisição HTTP.
    """
    def _worker():
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            resp = requests.get(url, timeout=timeout,
                                headers={"Accept": "application/vnd.github+json"})
            if resp.status_code != 200:
                return

            data = resp.json()
            latest = data.get("tag_name", "")
            release_url = data.get("html_url", "")
            notes = data.get("body", "") or ""

            if _parse_version(latest) > _parse_version(__version__):
                on_update_available(latest.lstrip("v"), release_url, notes)

        except Exception:
            pass  # falha silenciosa — update check nunca deve travar o app

    thread = threading.Thread(target=_worker, daemon=True, name="pyflow-update-check")
    thread.start()
