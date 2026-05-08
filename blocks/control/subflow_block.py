"""
blocks/control/subflow_block.py — SubfluxoBlock
"""
import json
import os
from blocks.base_block import BaseBlock


class SubfluxoBlock(BaseBlock):
    name        = "Subfluxo"
    description = (
        "Executa outro fluxo JSON dentro do fluxo atual. "
        "Permite reutilizar sequências de automação em múltiplos fluxos."
    )
    category = "Controle"

    params_schema = [
        {
            "name":        "flow_name",
            "label":       "Nome do fluxo",
            "type":        "str",
            "required":    True,
            "default":     "",
            "placeholder": "Ex: login_sistema  (sem .json)"
        },
        {
            "name":    "share_variables",
            "label":   "Compartilhar variáveis com o subfluxo",
            "type":    "bool",
            "required": False,
            "default": True,
        },
        {
            "name":    "export_variables",
            "label":   "Exportar variáveis do subfluxo para o fluxo pai",
            "type":    "bool",
            "required": False,
            "default": True,
        },
        {
            "name":    "stop_on_failure",
            "label":   "Parar fluxo pai se o subfluxo falhar",
            "type":    "bool",
            "required": False,
            "default": True,
        },
        {
            "name":        "flows_dir",
            "label":       "Pasta dos fluxos (padrão: flows/)",
            "type":        "str",
            "required":    False,
            "default":     "flows",
            "placeholder": "flows"
        },
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        flow_name    = params.get("flow_name", "").strip().replace(".json", "")
        share_vars   = params.get("share_variables",  True)
        export_vars  = params.get("export_variables", True)
        stop_on_fail = params.get("stop_on_failure",  True)
        flows_dir    = params.get("flows_dir", "flows").strip() or "flows"

        # ── Localiza os dados (Memória ou Arquivo) ───────────────────
        steps_data = params.get("_internal_steps")
        
        if not steps_data:
            flow_path = os.path.join(flows_dir, f"{flow_name}.json")
            if not os.path.exists(flow_path):
                flow_path = f"{flow_name}.json"
            if not os.path.exists(flow_path):
                available = self._list_available(flows_dir)
                return {
                    "success": False,
                    "message": (
                        f"Subfluxo '{flow_name}' não encontrado em '{flows_dir}/'.\n"
                        f"Disponíveis: {', '.join(available) or 'nenhum'}"
                    )
                }

            # ── Carrega o JSON ────────────────────────────────────────────
            try:
                with open(flow_path, "r", encoding="utf-8") as f:
                    flow_data = json.load(f)
                    steps_data = flow_data.get("steps", [])
            except Exception as e:
                return {"success": False, "message": f"Erro ao ler '{flow_name}.json': {e}"}

        if not steps_data:
            return {"success": True, "message": f"Subfluxo '{flow_name}' executado (0 passos)."}

        # ── Instancia os blocos ───────────────────────────────────────
        try:
            steps = self._build_steps(steps_data)
        except ImportError as e:
            return {"success": False, "message": f"Bloco não encontrado no subfluxo: {e}"}

        # ── Gerencia contexto ─────────────────────────────────────────
        from blocks.browser.extract_text import ExtractTextBlock
        parent_context = dict(ExtractTextBlock._context)

        if not share_vars:
            ExtractTextBlock._context.clear()

        # ── Executa ───────────────────────────────────────────────────
        try:
            from engine.runner import Runner, get_runner_config
            cfg = get_runner_config()
            runner = Runner(
                on_step_start=lambda i, b: print(f"    [sub {i+1}/{len(steps)}] {b.name}"),
                config=cfg,
            )
            results = runner.run_graph(steps)
        except Exception as e:
            if not share_vars:
                ExtractTextBlock._context.clear()
                ExtractTextBlock._context.update(parent_context)
            return {"success": False, "message": f"Erro ao executar subfluxo '{flow_name}': {e}"}

        # ── Exporta variáveis ─────────────────────────────────────────
        sub_context = dict(ExtractTextBlock._context)

        if not share_vars:
            ExtractTextBlock._context.clear()
            ExtractTextBlock._context.update(parent_context)
            if export_vars:
                ExtractTextBlock._context.update(sub_context)

        # Metadados da execução
        total   = len(results)
        ok      = sum(1 for r in results if r.get("success"))
        failed  = [r for r in results if not r.get("success")]
        success = len(failed) == 0

        ExtractTextBlock._context[f"{flow_name}_ok"]     = str(ok)
        ExtractTextBlock._context[f"{flow_name}_total"]  = str(total)
        ExtractTextBlock._context[f"{flow_name}_status"] = "sucesso" if success else "falhou"

        # ── Retorno ───────────────────────────────────────────────────
        if success:
            return {
                "success": True,
                "message": f"Subfluxo '{flow_name}' concluído: {ok}/{total} passos OK.",
                "data": {"subflow": flow_name, "steps_ok": ok, "steps_total": total}
            }

        error_msgs = "; ".join(r.get("message", "")[:60] for r in failed[:3])
        msg = f"Subfluxo '{flow_name}' falhou: {ok}/{total} passos OK. Erros: {error_msgs}"

        if stop_on_fail:
            return {"success": False, "message": msg}
        return {
            "success": True,
            "message": f"[ignorado] {msg}",
            "data": {"subflow": flow_name, "steps_ok": ok, "steps_total": total, "failure_ignored": True}
        }

    def _build_steps(self, steps_data: list) -> list:
        from engine.blocks_registry import BLOCK_BY_NAME as BLOCK_REGISTRY
        import uuid
        steps = []
        for step in steps_data:
            block_name = step.get("block", "")
            block_cls  = BLOCK_REGISTRY.get(block_name)
            if block_cls is None:
                continue
            
            s = {
                "id":             step.get("_id", uuid.uuid4().hex[:8]),
                "block_instance": block_cls(),
                "params":         step.get("params", {}),
                "next_success":   step.get("_next_success"),
                "next_error":     step.get("_next_error"),
                "_index":         step.get("_index", 0)
            }
            steps.append(s)
        return steps

    def _list_available(self, flows_dir: str) -> list:
        if not os.path.exists(flows_dir):
            return []
        return [f.replace(".json", "") for f in os.listdir(flows_dir) if f.endswith(".json")]
