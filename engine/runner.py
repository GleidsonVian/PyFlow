import re
import time
from blocks.base_block import BaseBlock


def resolve_params(params: dict, context: dict) -> dict:
    """Substitui {{nome_variavel}} pelo valor correspondente no contexto."""
    resolved = {}
    for key, value in params.items():
        if isinstance(value, str):
            def replacer(match):
                var_name = match.group(1).strip()
                return str(context.get(var_name, match.group(0)))
            resolved[key] = re.sub(r"\{\{(.+?)\}\}", replacer, value)
        else:
            resolved[key] = value
    return resolved


class RunnerConfig:
    """Configurações globais de execução do runner."""
    def __init__(self):
        self.retry_enabled   = False
        self.retry_attempts  = 3        # tentativas além da primeira
        self.retry_delay     = 2.0      # segundos entre tentativas
        self.retry_on_error  = True     # retry quando bloco retorna erro
        self.stop_on_failure = True     # para execução na primeira falha definitiva

    def to_dict(self) -> dict:
        return {
            "retry_enabled":   self.retry_enabled,
            "retry_attempts":  self.retry_attempts,
            "retry_delay":     self.retry_delay,
            "retry_on_error":  self.retry_on_error,
            "stop_on_failure": self.stop_on_failure,
        }

    def from_dict(self, data: dict):
        self.retry_enabled   = data.get("retry_enabled",   self.retry_enabled)
        self.retry_attempts  = data.get("retry_attempts",  self.retry_attempts)
        self.retry_delay     = data.get("retry_delay",     self.retry_delay)
        self.retry_on_error  = data.get("retry_on_error",  self.retry_on_error)
        self.stop_on_failure = data.get("stop_on_failure", self.stop_on_failure)


# Instância global de configuração
_config = RunnerConfig()


def get_runner_config() -> RunnerConfig:
    return _config


class Runner:
    """
    Executa uma sequência de blocos em ordem.
    Suporta: variáveis dinâmicas, If/Loop/ForEach e retry automático.
    """

    def __init__(self, on_step_start=None, on_step_done=None,
                 on_step_error=None, on_step_retry=None, config: RunnerConfig = None):
        self.on_step_start = on_step_start
        self.on_step_done  = on_step_done
        self.on_step_error = on_step_error
        self.on_step_retry = on_step_retry   # callback(index, block, attempt, max_attempts)
        self.config = config or _config

    def _get_context(self) -> dict:
        from blocks.browser.extract_text import ExtractTextBlock
        return ExtractTextBlock._context

    def _execute_with_retry(self, index: int, block: BaseBlock, params: dict) -> dict:
        """Executa um bloco com retry automático se configurado."""
        cfg = self.config

        result = block.execute(params)

        # Sem retry ou resultado bem-sucedido
        if not cfg.retry_enabled or result.get("success"):
            return result

        # Retry
        max_attempts = cfg.retry_attempts
        for attempt in range(1, max_attempts + 1):
            print(f"    ↻ Tentativa {attempt}/{max_attempts} em {block.name}...")

            if self.on_step_retry:
                self.on_step_retry(index, block, attempt, max_attempts)

            if cfg.retry_delay > 0:
                time.sleep(cfg.retry_delay)

            # Re-resolve params (contexto pode ter mudado)
            resolved = resolve_params(
                {k: v for k, v in params.items()},
                self._get_context()
            )
            result = block.execute(resolved)

            if result.get("success"):
                result["retried"] = attempt
                print(f"    ✓ Sucesso na tentativa {attempt}")
                return result

        result["exhausted_retries"] = True
        return result

    def run(self, steps: list[dict]) -> list[dict]:
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
                retried = result.get("retried", 0)
                exhausted = result.get("exhausted_retries", False)
                msg = result.get("message", "Erro desconhecido")

                if exhausted:
                    print(f"  ✗ Falhou após {self.config.retry_attempts} tentativas: {msg}")
                else:
                    print(f"  ✗ {msg}")

                if self.on_step_error:
                    self.on_step_error(i, block, result)

                if self.config.stop_on_failure:
                    print(f"\n  Execução interrompida no passo {i + 1}.")
                    break
                else:
                    # Continua para o próximo bloco mesmo com falha
                    i += 1
                    continue

            data = result.get("data", {})
            retried = result.get("retried", 0)
            suffix = f" (após {retried} retry)" if retried else ""
            print(f"  ✓ {result.get('message', 'OK')}{suffix}")

            if self.on_step_done:
                self.on_step_done(i, block, result)

            # ── Bloco If ──────────────────────────────────────────────
            if data.get("skip_blocks", 0) > 0:
                skip = data["skip_blocks"]
                print(f"  → Condição falsa: pulando {skip} bloco(s)")
                i += 1 + skip
                continue

            # ── Bloco Loop ────────────────────────────────────────────
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

            # ── Bloco For Each ────────────────────────────────────────
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

    def _run_sub(self, steps: list[dict], base_index: int) -> list[dict]:
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