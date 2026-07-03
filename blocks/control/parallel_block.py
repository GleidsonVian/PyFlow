import json
import threading
import copy

from blocks.base_block import BaseBlock


class ParallelBlock(BaseBlock):
    name = "Ramos Paralelos"
    description = (
        "Executa múltiplos fluxos simultaneamente e aguarda todos terminarem. "
        "Informe os nomes dos fluxos separados por vírgula (sem .json). "
        "As variáveis do contexto atual são compartilhadas com cada ramo."
    )
    category = "Controle"

    params_schema = [
        {
            "name":        "flows",
            "label":       "Fluxos para executar em paralelo",
            "type":        "str",
            "required":    True,
            "default":     "",
            "placeholder": "Ex: login_sistema, processar_dados, enviar_email",
        },
        {
            "name":        "flows_dir",
            "label":       "Pasta dos fluxos (padrão: flows)",
            "type":        "str",
            "required":    False,
            "default":     "flows",
            "placeholder": "flows",
        },
        {
            "name":        "export_variables",
            "label":       "Exportar variáveis dos ramos para o fluxo pai",
            "type":        "bool",
            "required":    False,
            "default":     False,
        },
        {
            "name":        "stop_on_failure",
            "label":       "Parar se algum ramo falhar",
            "type":        "bool",
            "required":    False,
            "default":     True,
        },
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        import os
        from engine.blocks_registry import BLOCK_BY_NAME
        from engine.execution_context import get as ctx_get
        from engine.runner import Runner, get_runner_config

        flows_raw    = params.get("flows", "").strip()
        flows_dir    = params.get("flows_dir", "flows").strip() or "flows"
        export_vars  = bool(params.get("export_variables", False))
        stop_on_fail = bool(params.get("stop_on_failure", True))

        flow_names = [f.strip() for f in flows_raw.split(",") if f.strip()]
        if not flow_names:
            return {"success": False, "message": "Nenhum fluxo informado."}

        # Resolve caminhos
        paths = []
        for name in flow_names:
            candidates = [
                name,
                os.path.join(flows_dir, name),
                os.path.join(flows_dir, name + ".json"),
            ]
            path = next((p for p in candidates if os.path.exists(p)), None)
            if not path:
                return {"success": False, "message": f"Fluxo não encontrado: '{name}'"}
            paths.append((name, path))

        # Snapshot do contexto pai para cada ramo
        parent_ctx = copy.deepcopy(ctx_get())

        results_map = {}
        errors_map  = {}
        threads     = []

        def _run_branch(branch_name, flow_path):
            try:
                with open(flow_path, encoding="utf-8") as f:
                    data = json.load(f)
                steps_data = data.get("steps", [])

                steps = []
                for s in steps_data:
                    cls = BLOCK_BY_NAME.get(s.get("block"))
                    if cls:
                        raw_p = {k: v for k, v in s.get("params", {}).items()
                                 if not k.startswith("_")}
                        steps.append({"block_instance": cls(), "params": raw_p,
                                      "id": s.get("_id", ""), "_index": len(steps)})

                # Contexto isolado por ramo (cópia do pai)
                branch_ctx = copy.deepcopy(parent_ctx)

                runner = Runner(config=get_runner_config())
                runner._branch_ctx = branch_ctx

                branch_results = runner.run(steps, is_sub_run=True)
                results_map[branch_name] = branch_results

                if export_vars:
                    results_map[f"__ctx_{branch_name}"] = copy.deepcopy(runner._get_context())

            except Exception as e:
                errors_map[branch_name] = str(e)

        for name, path in paths:
            t = threading.Thread(target=_run_branch, args=(name, path), daemon=True)
            threads.append((name, t))
            t.start()

        for name, t in threads:
            t.join()

        # Exporta variáveis dos ramos de volta ao pai
        if export_vars:
            for name, _ in paths:
                branch_ctx = results_map.pop(f"__ctx_{name}", {})
                ctx_get().update(branch_ctx)

        failed = list(errors_map.keys())
        ok_count = len(paths) - len(failed)

        if failed and stop_on_fail:
            detail = "; ".join(f"{n}: {e}" for n, e in errors_map.items())
            return {
                "success": False,
                "message": f"Ramos com falha: {', '.join(failed)} — {detail}",
            }

        return {
            "success": True,
            "message": f"✓ {ok_count}/{len(paths)} ramos concluídos" + (
                f" ({len(failed)} com erro)" if failed else ""
            ),
            "data": {
                "parallel_ok":     ok_count,
                "parallel_total":  len(paths),
                "parallel_failed": failed,
            },
        }
