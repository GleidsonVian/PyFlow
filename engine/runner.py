import time
import os
from datetime import datetime
from blocks.base_block import BaseBlock
import engine.execution_context as ctx
from engine.execution_context import resolve_params


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
        self._stopped = False

    def stop(self):
        """Solicita a parada segura da execução."""
        self._stopped = True

    def _take_error_screenshot(self, index: int, block: BaseBlock, result: dict):
        """Captura screenshot se houver um navegador ativo."""
        try:
            from blocks.browser.open_browser import OpenBrowserBlock
            driver = OpenBrowserBlock.get_driver()
            if not driver:
                return

            if not os.path.exists("screenshots"):
                os.makedirs("screenshots")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Limpa o nome do bloco para o nome do arquivo
            safe_name = "".join(c for c in block.name if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_")
            filename = f"ERRO_{index + 1}_{safe_name}_{timestamp}.png"
            filepath = os.path.abspath(os.path.join("screenshots", filename))

            driver.save_screenshot(filepath)
            result["screenshot"] = filepath
            print(f"  📸 Screenshot de erro salvo: {filepath}")
        except Exception as e:
            print(f"  ⚠ Falha ao capturar screenshot: {e}")

    def _get_context(self):
        return ctx.get()

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

    # ── Helpers para blocos de controle ──────────────────────────────────

    @staticmethod
    def _block_type(step) -> str:
        return type(step["block_instance"]).__name__

    @staticmethod
    def _find_scope_end(steps, start: int, end_type: str, start_type: str) -> int:
        """
        Busca o índice do marcador de fim (end_type) a partir de start.
        Lida com aninhamento: ignora end_type dentro de start_type aninhados.
        Retorna -1 se não encontrar.
        """
        depth = 0
        for j in range(start, len(steps)):
            t = type(steps[j]["block_instance"]).__name__
            if t == start_type:
                depth += 1
            elif t == end_type:
                if depth == 0:
                    return j
                depth -= 1
        return -1

    @staticmethod
    def _find_else(steps, start: int, end_type: str, start_type: str) -> int:
        """
        Busca o índice do ElseBlock dentro do escopo atual.
        Retorna -1 se não houver Else (ou se estiver dentro de If aninhado).
        """
        depth = 0
        for j in range(start, len(steps)):
            t = type(steps[j]["block_instance"]).__name__
            if t == start_type:
                depth += 1
            elif t == end_type:
                if depth == 0:
                    return -1   # chegou ao fim sem Else
                depth -= 1
            elif t == "ElseBlock" and depth == 0:
                return j
        return -1

    @staticmethod
    def _find_branch(steps, start: int, end_type: str, start_type: str,
                     branch_type: str) -> int:
        """
        Versão genérica de _find_else — acha qualquer bloco de ramo (CatchBlock, etc.)
        dentro do escopo atual. Retorna -1 se não encontrar.
        """
        depth = 0
        for j in range(start, len(steps)):
            t = type(steps[j]["block_instance"]).__name__
            if t == start_type:
                depth += 1
            elif t == end_type:
                if depth == 0:
                    return -1
                depth -= 1
            elif t == branch_type and depth == 0:
                return j
        return -1

    def run(self, steps: list, start_index: int = 0) -> list:
        if start_index == 0:
            # Preserva variáveis de webhook injetadas pela API antes de limpar o contexto
            _webhook_snapshot = {k: v for k, v in ctx.get().items() if k.startswith("webhook_")}
            ctx.clear()
            ctx.get().update(_webhook_snapshot)

        results = []
        total = len(steps)
        i = max(0, start_index)

        # Tipos de marcadores — consumidos pelo bloco de controle, não executar diretamente
        _SKIP_TYPES = frozenset({
            "EndLoopBlock", "EndForEachBlock", "EndIfBlock", "ElseBlock",
            "EndTryBlock", "CatchBlock", "EndWhileBlock",
        })

        while i < total:
            if self._stopped:
                print("  ⚠ Parada solicitada pelo usuário.")
                break

            step  = steps[i]
            block: BaseBlock = step["block_instance"]
            btype = self._block_type(step)
            raw_params: dict = step.get("params", {})

            # Marcadores de fim/else são consumidos pelo bloco de controle — não executar
            if btype in _SKIP_TYPES:
                i += 1
                continue

            print(f"\n[{i + 1}/{total}] Executando: {block.name}")

            if self.on_step_start:
                self.on_step_start(i, block)

            try:
                params = resolve_params(raw_params, self._get_context())
                result = self._execute_with_retry(i, block, params)
            except ValueError as e:
                result = {"success": False, "message": str(e)}

            result["step_index"] = i
            result["block_name"] = block.name
            results.append(result)

            if not result.get("success"):
                msg = result.get("message", "Erro desconhecido")
                
                # Screenshot automático para erros de navegador
                if getattr(block, "category", "") == "Navegador":
                    self._take_error_screenshot(i, block, result)
                    if result.get("screenshot"):
                        msg += f" (📸 {os.path.basename(result['screenshot'])})"
                        result["message"] = msg

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
            suffix  = f" (após {retried} retry)" if retried else ""
            print(f"  ✓ {result.get('message', 'OK')}{suffix}")

            if self.on_step_done:
                self.on_step_done(i, block, result)

            data = result.get("data", {})

            # ── LOOP ──────────────────────────────────────────────────
            if data.get("loop"):
                end_idx = self._find_scope_end(steps, i + 1, "EndLoopBlock", "LoopBlock")
                if end_idx == -1:
                    print("  ⚠ Loop sem 'Fim do Loop' — pulando.")
                    i += 1
                    continue

                times      = data["times"]
                delay      = data.get("delay_between", 0)
                body_steps = steps[i + 1: end_idx]
                print(f"  → Loop: {times}x, {len(body_steps)} bloco(s) internos")

                for iteration in range(times):
                    print(f"    Iteração {iteration + 1}/{times}")
                    sub = self._run_sub(body_steps, i + 1)
                    results.extend(sub)
                    if any(not r.get("success") for r in sub) and self.config.stop_on_failure:
                        break
                    if delay > 0:
                        time.sleep(delay)

                i = end_idx + 1
                continue

            # ── FOR EACH ──────────────────────────────────────────────
            if data.get("foreach"):
                end_idx = self._find_scope_end(steps, i + 1, "EndForEachBlock", "ForEachBlock")
                if end_idx == -1:
                    print("  ⚠ Para Cada sem 'Fim do Para Cada' — pulando.")
                    i += 1
                    continue

                items      = data["items"]
                var_name   = data["variable_name"]
                delay      = data.get("delay_between", 0)
                body_steps = steps[i + 1: end_idx]
                print(f"  → Para Cada: {len(items)} item(s), variável '{var_name}'")

                for idx, item in enumerate(items):
                    self._get_context()[var_name] = item
                    print(f"    Item {idx + 1}/{len(items)}: {item}")
                    sub = self._run_sub(body_steps, i + 1)
                    results.extend(sub)
                    if any(not r.get("success") for r in sub) and self.config.stop_on_failure:
                        break
                    if delay > 0:
                        time.sleep(delay)

                i = end_idx + 1
                continue

            # ── IF / SE ───────────────────────────────────────────────
            if "if_result" in data:
                condition   = data["if_result"]
                else_idx    = self._find_else(steps, i + 1, "EndIfBlock", "IfBlock")
                end_idx     = self._find_scope_end(steps, i + 1, "EndIfBlock", "IfBlock")

                if end_idx == -1:
                    print("  ⚠ Se sem 'Fim do Se' — pulando.")
                    i += 1
                    continue

                if condition:
                    # Executa ramo verdadeiro (até Else ou EndIf)
                    true_end  = else_idx if else_idx != -1 else end_idx
                    true_steps = steps[i + 1: true_end]
                    print(f"  → Se VERDADEIRO: executando {len(true_steps)} bloco(s)")
                    sub = self._run_sub(true_steps, i + 1)
                    results.extend(sub)
                else:
                    if else_idx != -1:
                        # Executa ramo falso (entre Else e EndIf)
                        false_steps = steps[else_idx + 1: end_idx]
                        print(f"  → Se FALSO (Senão): executando {len(false_steps)} bloco(s)")
                        sub = self._run_sub(false_steps, else_idx + 1)
                        results.extend(sub)
                    else:
                        print("  → Se FALSO: pulando bloco(s)")

                i = end_idx + 1
                continue

            # ── TRY / CATCH ───────────────────────────────────────────
            if data.get("try"):
                catch_idx = self._find_branch(steps, i + 1, "EndTryBlock",
                                              "TryBlock", "CatchBlock")
                end_idx   = self._find_scope_end(steps, i + 1, "EndTryBlock", "TryBlock")

                if end_idx == -1:
                    print("  ⚠ Tentar sem 'Fim do Tentar' — pulando.")
                    i += 1
                    continue

                try_steps   = steps[i + 1: catch_idx if catch_idx != -1 else end_idx]
                print(f"  → Tentar: {len(try_steps)} bloco(s) no ramo protegido")

                sub = self._run_sub(try_steps, i + 1)
                failed = [r for r in sub if not r.get("success")]

                if failed:
                    error_msg = failed[0].get("message", "Erro desconhecido")
                    print(f"  ↳ Erro capturado: {error_msg}")
                    results.extend(sub)   # registra os resultados do try (incluindo falha)

                    if catch_idx != -1:
                        # Salva mensagem do erro na variável configurada no CatchBlock
                        catch_step = steps[catch_idx]
                        save_to = catch_step.get("params", {}).get("save_error_to", "").strip()
                        if save_to:
                            self._get_context()[save_to] = error_msg
                            print(f"  ↳ Erro salvo em '{save_to}'")

                        catch_steps = steps[catch_idx + 1: end_idx]
                        print(f"  → Capturar: executando {len(catch_steps)} bloco(s)")
                        sub_catch = self._run_sub(catch_steps, catch_idx + 1)
                        results.extend(sub_catch)
                else:
                    results.extend(sub)

                i = end_idx + 1
                continue

            # ── WHILE / ENQUANTO ─────────────────────────────────────
            if data.get("while"):
                end_idx = self._find_scope_end(steps, i + 1, "EndWhileBlock", "WhileBlock")
                if end_idx == -1:
                    print("  ⚠ Enquanto sem 'Fim do Enquanto' — pulando.")
                    i += 1
                    continue

                condition_met  = data["condition_met"]
                max_iter       = data.get("max_iterations", 100)
                delay          = data.get("delay_between", 0)
                body_steps     = steps[i + 1: end_idx]
                iteration      = 0

                if not condition_met:
                    print(f"  → Enquanto: condição já falsa — pulando {len(body_steps)} bloco(s)")
                    i = end_idx + 1
                    continue

                print(f"  → Enquanto: iniciando (máx {max_iter} iterações)")

                while condition_met and iteration < max_iter:
                    iteration += 1
                    print(f"    Iteração {iteration}/{max_iter}")
                    sub = self._run_sub(body_steps, i + 1)
                    results.extend(sub)

                    if any(not r.get("success") for r in sub) and self.config.stop_on_failure:
                        print("  ↳ Enquanto interrompido por falha.")
                        break

                    if delay > 0:
                        time.sleep(delay)

                    # Reavalia a condição executando o WhileBlock novamente
                    re_params = resolve_params(raw_params, self._get_context())
                    re_result = block.execute(re_params)
                    if not re_result.get("success"):
                        print(f"  ↳ Erro ao reavaliar condição: {re_result.get('message')}")
                        break
                    condition_met = re_result.get("data", {}).get("condition_met", False)

                if iteration >= max_iter and condition_met:
                    print(f"  ⚠ Enquanto: limite de {max_iter} iterações atingido — encerrando.")

                i = end_idx + 1
                continue

            i += 1

        return results

    def _run_sub(self, steps: list, base_index: int) -> list:
        """
        Executa sub-fluxos (Loop / ForEach / If).
        Delega ao run() principal para que If/Loop/ForEach aninhados funcionem corretamente.
        """
        return self.run(steps)

    def run_graph(self, graph: list, start_index: int = 0) -> list:
        """
        Execução condicional baseada em grafo.
        graph: lista de {id, block_instance, params, next_success, next_error, _index}
        Cada nó decide o próximo baseado no resultado real (success → next_success, error → next_error).
        """
        if not graph:
            return []

        if start_index == 0:
            # Preserva variáveis de webhook injetadas pela API antes de limpar o contexto
            _webhook_snapshot = {k: v for k, v in ctx.get().items() if k.startswith("webhook_")}
            ctx.clear()
            ctx.get().update(_webhook_snapshot)

        node_map = {n["id"]: n for n in graph}
        results  = []
        # visited  = set()   # REMOVIDO: permite loops manuais no grafo (estilo n8n/node-red)

        # Raízes: nós não referenciados como destino de nenhuma conexão
        if start_index > 0:
            target_node = next((n for n in graph if n.get("_index") == start_index), None)
            roots = [target_node] if target_node else []
        else:
            all_targets = set()
            for n in graph:
                if n.get("next_success"): all_targets.add(n["next_success"])
                if n.get("next_error"):   all_targets.add(n["next_error"])
            roots = [n for n in graph if n["id"] not in all_targets]
            if not roots and graph:
                roots = [graph[0]]

        def _exec_node(node_id: str):
            if self._stopped or node_id not in node_map:
                return
            
            node  = node_map[node_id]
            block = node["block_instance"]
            index = node["_index"]

            raw_params = {k: v for k, v in node.get("params", {}).items()
                          if not k.startswith("_")}
            
            print(f"\n[{index + 1}] Executando: {block.name}")
            if self.on_step_start:
                self.on_step_start(index, block)

            try:
                params = resolve_params(raw_params, self._get_context())
                result = self._execute_with_retry(index, block, params)
            except ValueError as e:
                result = {"success": False, "message": str(e)}

            result["step_index"] = index
            result["block_name"] = block.name
            results.append(result)

            data = result.get("data", {})
            next_id = None

            if result.get("success"):
                suffix = f" (após {result['retried']} retry)" if result.get("retried") else ""
                print(f"  ✓ {result.get('message', 'OK')}{suffix}")
                if self.on_step_done:
                    self.on_step_done(index, block, result)
                
                # Suporte a desvio condicional via portas no grafo
                if "if_result" in data:
                    if data["if_result"]:
                        print("  → Caminho: VERDADEIRO")
                        next_id = node.get("next_success")
                    else:
                        print("  → Caminho: FALSO")
                        next_id = node.get("next_error")
                else:
                    next_id = node.get("next_success")
            else:
                msg = result.get("message", "Erro desconhecido")
                print(f"  ✗ {msg}")
                if self.on_step_error:
                    self.on_step_error(index, block, result)
                
                # Se for um erro real (não um 'if_result' falso), segue a porta de erro
                next_id = node.get("next_error")
                
                if not next_id:
                    if self.config.stop_on_failure:
                        print(f"\n  Execução interrompida — sem rota de erro para '{block.name}'.")
                        return
                    return

            if next_id:
                # Usa recursion limit para segurança ou um pequeno delay se necessário
                _exec_node(next_id)

        for root in roots:
            if not self._stopped:
                _exec_node(root["id"])

        return results

