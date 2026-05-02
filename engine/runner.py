import re
import time
from blocks.base_block import BaseBlock
from engine.asset_manager import AssetManager


# ── Classificação de erros ────────────────────────────────────────────────────

_ERROR_PATTERNS = {
    "timeout": [
        "timeout", "timed out", "time out",
        "TimeoutException", "implicitly_wait",
        "WebDriverWait", "Expected condition",
    ],
    "network": [
        "ConnectionError", "ERR_CONNECTION", "ERR_NAME_NOT_RESOLVED",
        "net::", "connection refused", "connection reset",
        "RemoteDisconnected", "ProtocolError", "socket",
    ],
    "stale": [
        "StaleElementReferenceException", "stale element",
        "element is not attached",
    ],
    "notfound": [
        "NoSuchElementException", "no such element",
        "Unable to locate element", "Element not found",
    ],
    "invalid": [
        "InvalidSelectorException", "invalid selector",
        "SyntaxError", "unexpected character",
        "invalid or illegal selector",
    ],
}


def _classify_error(message: str) -> str:
    msg_lower = message.lower()
    for category, patterns in _ERROR_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in msg_lower:
                return category
    return "unknown"


def _should_retry(message: str, cfg) -> tuple:
    """Retorna (deve_retry: bool, motivo: str)"""
    if not cfg.retry_enabled:
        return False, "retry desativado"

    category = _classify_error(message)

    category_map = {
        "timeout":  cfg.retry_on_timeout,
        "network":  cfg.retry_on_network,
        "stale":    cfg.retry_on_stale,
        "notfound": cfg.retry_on_notfound,
        "invalid":  cfg.retry_on_invalid,
    }

    if category in category_map:
        enabled = category_map[category]
        if enabled:
            return True, f"categoria: {category}"
        else:
            return False, f"categoria '{category}' sem retry configurado"

    # Palavras-chave personalizadas
    if cfg.retry_on_custom:
        keywords = [k.strip().lower() for k in cfg.retry_on_custom.split(",") if k.strip()]
        for kw in keywords:
            if kw in message.lower():
                return True, f"palavra-chave: '{kw}'"

    return True, "erro desconhecido (retry por precaução)"


# ── Resolve params (mantido igual ao seu) ─────────────────────────────────────

def resolve_params(params: dict, context: dict) -> dict:
    """
    Substitui tokens dinâmicos pelo valor real.
    1. {{ASSET:nome}} → Busca no arquivo de credenciais/configurações.
    2. {{nome}}       → Busca nas variáveis de execução (contexto).
    """
    resolved = {}
    for key, value in params.items():
        if isinstance(value, str):
            def asset_replacer(match):
                asset_key = match.group(1).strip()
                val = AssetManager.get_asset(asset_key)
                if val is not None:
                    return str(val)
                return match.group(0)

            temp_value = re.sub(r"\{\{ASSET:(.+?)\}\}", asset_replacer, value)

            def context_replacer(match):
                var_name = match.group(1).strip()
                if var_name.startswith("ASSET:"):
                    return match.group(0)
                return str(context.get(var_name, match.group(0)))

            resolved[key] = re.sub(r"\{\{(.+?)\}\}", context_replacer, temp_value)
        else:
            resolved[key] = value
    return resolved


# ── RunnerConfig — agora com ConditionalRetry ─────────────────────────────────

class RunnerConfig:
    """Configurações globais de execução do runner."""
    def __init__(self):
        self.retry_enabled    = False
        self.retry_attempts   = 3
        self.retry_delay      = 2.0
        self.retry_on_error   = True
        self.stop_on_failure  = True

        # ConditionalRetry — categorias de erro
        self.retry_on_timeout  = True   # TimeoutException — retry resolve
        self.retry_on_network  = True   # ConnectionError  — retry resolve
        self.retry_on_stale    = True   # StaleElement     — retry resolve
        self.retry_on_notfound = False  # NoSuchElement    — raramente resolve
        self.retry_on_invalid  = False  # InvalidSelector  — NUNCA resolve
        self.retry_on_custom   = ""     # palavras-chave personalizadas

    def to_dict(self) -> dict:
        return {
            "retry_enabled":    self.retry_enabled,
            "retry_attempts":   self.retry_attempts,
            "retry_delay":      self.retry_delay,
            "retry_on_error":   self.retry_on_error,
            "stop_on_failure":  self.stop_on_failure,
            "retry_on_timeout": self.retry_on_timeout,
            "retry_on_network": self.retry_on_network,
            "retry_on_stale":   self.retry_on_stale,
            "retry_on_notfound":self.retry_on_notfound,
            "retry_on_invalid": self.retry_on_invalid,
            "retry_on_custom":  self.retry_on_custom,
        }

    def from_dict(self, data: dict):
        self.retry_enabled    = data.get("retry_enabled",    self.retry_enabled)
        self.retry_attempts   = data.get("retry_attempts",   self.retry_attempts)
        self.retry_delay      = data.get("retry_delay",      self.retry_delay)
        self.retry_on_error   = data.get("retry_on_error",   self.retry_on_error)
        self.stop_on_failure  = data.get("stop_on_failure",  self.stop_on_failure)
        self.retry_on_timeout = data.get("retry_on_timeout", self.retry_on_timeout)
        self.retry_on_network = data.get("retry_on_network", self.retry_on_network)
        self.retry_on_stale   = data.get("retry_on_stale",   self.retry_on_stale)
        self.retry_on_notfound= data.get("retry_on_notfound",self.retry_on_notfound)
        self.retry_on_invalid = data.get("retry_on_invalid", self.retry_on_invalid)
        self.retry_on_custom  = data.get("retry_on_custom",  self.retry_on_custom)


_config = RunnerConfig()


def get_runner_config() -> RunnerConfig:
    return _config


# ── Runner ────────────────────────────────────────────────────────────────────

class Runner:
    """
    Motor de execução principal.
    Gerencia a fila de blocos, resolve variáveis/assets e aplica ConditionalRetry.
    """

    def __init__(self, on_step_start=None, on_step_done=None,
                 on_step_error=None, on_step_retry=None, config: RunnerConfig = None):
        self.on_step_start = on_step_start
        self.on_step_done  = on_step_done
        self.on_step_error = on_step_error
        self.on_step_retry = on_step_retry
        self.config = config or _config

    def _get_context(self) -> dict:
        from blocks.browser.extract_text import ExtractTextBlock
        return ExtractTextBlock._context

    def _execute_with_retry(self, index: int, block: BaseBlock, params: dict) -> dict:
        """Executa um bloco com ConditionalRetry."""
        cfg = self.config
        result = block.execute(params)

        if result.get("success") or not cfg.retry_enabled:
            return result

        # Verifica se este tipo de erro merece retry
        error_msg = result.get("message", "")
        should, reason = _should_retry(error_msg, cfg)

        if not should:
            category = _classify_error(error_msg)
            print(f"  ↷ Retry ignorado [{category}] — {reason}")
            result["retry_skipped"]   = True
            result["retry_reason"]    = reason
            result["error_category"]  = category
            return result

        # Executa as tentativas
        max_attempts = cfg.retry_attempts
        for attempt in range(1, max_attempts + 1):
            print(f"  ↻ Tentativa {attempt}/{max_attempts} em {block.name} ({reason})...")

            if self.on_step_retry:
                self.on_step_retry(index, block, attempt, max_attempts)

            if cfg.retry_delay > 0:
                time.sleep(cfg.retry_delay)

            # Re-resolve params (variáveis podem ter mudado entre tentativas)
            resolved = resolve_params(params, self._get_context())
            result = block.execute(resolved)

            if result.get("success"):
                result["retried"]        = attempt
                result["retry_reason"]   = reason
                print(f"  ✓ Sucesso na tentativa {attempt}")
                return result

            # Reclassifica após cada tentativa
            error_msg = result.get("message", "")
            should, reason = _should_retry(error_msg, cfg)
            if not should:
                print(f"  ↷ Retry interrompido após tentativa {attempt} — {reason}")
                break

        result["exhausted_retries"] = True
        result["retry_attempts"]    = max_attempts
        return result

    def run(self, steps: list) -> list:
        results = []
        total = len(steps)
        i = 0

        while i < total:
            step = steps[i]
            block: BaseBlock = step["block_instance"]
            raw_params: dict = step.get("params", {})

            params = resolve_params(raw_params, self._get_context())

            print(f"\n[{i + 1}/{total}] Executando: {block.name}")

            if self.on_step_start:
                self.on_step_start(i, block)

            result = self._execute_with_retry(i, block, params)
            result["step_index"] = i
            result["block_name"] = block.name
            results.append(result)

            if not result.get("success"):
                msg = result.get("message", "Erro desconhecido")
                if result.get("exhausted_retries"):
                    print(f"  ✗ Falhou após {result.get('retry_attempts', '?')} retries: {msg}")
                elif result.get("retry_skipped"):
                    print(f"  ✗ {msg} [sem retry: {result.get('retry_reason', '')}]")
                else:
                    print(f"  ✗ {msg}")

                if self.on_step_error:
                    self.on_step_error(i, block, result)

                if self.config.stop_on_failure:
                    print(f"\n  Execução interrompida no passo {i + 1}.")
                    break
                else:
                    i += 1
                    continue

            retried = result.get("retried", 0)
            suffix = f" (após {retried} retry)" if retried else ""
            print(f"  ✓ {result.get('message', 'OK')}{suffix}")

            if self.on_step_done:
                self.on_step_done(i, block, result)

            # ── Lógica de fluxo (If / Loop / ForEach) ─────────────────
            data = result.get("data", {})

            # IF
            if data.get("skip_blocks", 0) > 0:
                skip = data["skip_blocks"]
                print(f"  → Condição falsa: pulando {skip} bloco(s)")
                i += 1 + skip
                continue

            # LOOP
            if data.get("loop"):
                times        = data["times"]
                blocks_count = data["blocks_count"]
                delay        = data.get("delay_between", 0)
                loop_steps   = steps[i + 1: i + 1 + blocks_count]

                print(f"  → Loop: {times}x sobre {blocks_count} bloco(s)")
                for iteration in range(times):
                    print(f"    Iteração {iteration + 1}/{times}")
                    sub_results = self._run_sub(loop_steps, i + 1)
                    results.extend(sub_results)
                    if any(not r.get("success") for r in sub_results) and self.config.stop_on_failure:
                        break
                    if delay > 0:
                        time.sleep(delay)

                i += 1 + blocks_count
                continue

            # FOR EACH
            if data.get("foreach"):
                from blocks.browser.extract_text import ExtractTextBlock
                items        = data["items"]
                var_name     = data["variable_name"]
                blocks_count = data["blocks_count"]
                delay        = data.get("delay_between", 0)
                foreach_steps = steps[i + 1: i + 1 + blocks_count]

                print(f"  → For Each: {len(items)} item(s), variável '{var_name}'")
                for idx, item in enumerate(items):
                    ExtractTextBlock._context[var_name] = item
                    print(f"    Item {idx + 1}/{len(items)}: {item}")
                    sub_results = self._run_sub(foreach_steps, i + 1)
                    results.extend(sub_results)
                    if any(not r.get("success") for r in sub_results) and self.config.stop_on_failure:
                        break
                    if delay > 0:
                        time.sleep(delay)

                i += 1 + blocks_count
                continue

            i += 1

        return results

    def _run_sub(self, steps: list, base_index: int) -> list:
        """Executa sub-fluxos (usado por Loop e ForEach)."""
        results = []
        for j, step in enumerate(steps):
            block: BaseBlock = step["block_instance"]
            raw_params: dict = step.get("params", {})
            real_index = base_index + j
            params = resolve_params(raw_params, self._get_context())

            if self.on_step_start:
                self.on_step_start(real_index, block)

            result = self._execute_with_retry(real_index, block, params)
            result["step_index"] = real_index
            result["block_name"] = block.name
            results.append(result)

            if result.get("success"):
                if self.on_step_done:
                    self.on_step_done(real_index, block, result)
            else:
                if self.on_step_error:
                    self.on_step_error(real_index, block, result)
                if self.config.stop_on_failure:
                    break

        return results