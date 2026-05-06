import time
from blocks.base_block import BaseBlock
from blocks.browser.open_browser import OpenBrowserBlock


class ConditionalNavigateBlock(BaseBlock):
    name        = "Aguardar URL / Elemento"
    description = "Aguarda até que a URL contenha um padrão ou um elemento apareça/desapareça. Ação configurável em caso de falha."
    category    = "Navegador"

    params_schema = [
        {
            "name": "condition_type", "label": "Tipo de condição",
            "type": "select",
            "options": ["url_contains", "element_visible", "element_hidden"],
            "default": "url_contains",
            "required": True,
        },
        {
            "name": "pattern", "label": "Padrão / Seletor CSS",
            "type": "str", "required": True, "default": "",
            "placeholder": "parte-da-url  ou  #meu-elemento",
        },
        {
            "name": "timeout", "label": "Timeout (segundos)",
            "type": "str", "required": False, "default": "30",
        },
        {
            "name": "poll_interval", "label": "Intervalo de verificação (s)",
            "type": "str", "required": False, "default": "0.5",
        },
        {
            "name": "on_failure", "label": "Se falhar",
            "type": "select",
            "options": ["stop", "continue", "skip"],
            "default": "stop",
            "required": False,
        },
        {
            "name": "skip_blocks", "label": "Blocos a pular (se 'skip')",
            "type": "str", "required": False, "default": "1",
        },
        {
            "name": "variable_name", "label": "Salvar resultado em variável (opcional)",
            "type": "str", "required": False, "default": "",
            "placeholder": "ex: condicao_atendida  →  True / False",
        },
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": False, "message": "Nenhum navegador aberto."}

        condition_type = params.get("condition_type", "url_contains")
        pattern        = params.get("pattern", "").strip()
        on_failure     = params.get("on_failure", "stop")
        var_name       = params.get("variable_name", "").strip()

        try:
            timeout       = float(params.get("timeout", 30))
            poll_interval = float(params.get("poll_interval", 0.5))
            skip_n        = int(params.get("skip_blocks", 1))
        except ValueError:
            return {"success": False, "message": "Timeout, intervalo ou 'Blocos a pular' inválidos."}

        deadline = time.time() + timeout
        met      = False
        elapsed  = 0.0

        while time.time() < deadline:
            try:
                if condition_type == "url_contains":
                    met = pattern in driver.current_url
                elif condition_type == "element_visible":
                    el = driver.find_elements("css selector", pattern)
                    met = bool(el) and el[0].is_displayed()
                elif condition_type == "element_hidden":
                    el = driver.find_elements("css selector", pattern)
                    met = not el or not el[0].is_displayed()
            except Exception:
                met = False

            if met:
                elapsed = timeout - (deadline - time.time())
                break

            time.sleep(poll_interval)

        if var_name:
            import engine.execution_context as ctx
            ctx.get()[var_name] = str(met)

        if met:
            return {
                "success": True,
                "message": f"Condição atendida em {elapsed:.1f}s: {condition_type} = '{pattern}'",
                "data": {"condition_met": True},
            }

        # Condição não foi atendida dentro do timeout
        msg = f"Timeout ({timeout}s): condição '{condition_type}' não atendida para '{pattern}'"

        if on_failure == "continue":
            return {
                "success": True,
                "message": f"⚠ {msg} — continuando mesmo assim",
                "data": {"condition_met": False},
            }

        if on_failure == "skip":
            return {
                "success": True,
                "message": f"⚠ {msg} — pulando {skip_n} bloco(s)",
                "data": {"condition_met": False, "skip_blocks": skip_n},
            }

        # on_failure == "stop"
        return {"success": False, "message": msg}
