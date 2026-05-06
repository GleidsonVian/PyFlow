from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from blocks.base_block import BaseBlock


class OpenBrowserBlock(BaseBlock):
    name = "Abrir Navegador"
    description = "Abre o Google Chrome em uma URL especificada. O modo Headless é configurado globalmente em ⚙ Configurações → Navegador."
    category = "Navegador"

    params_schema = [
        {
            "name": "url",
            "label": "URL",
            "type": "str",
            "required": True,
            "default": "https://",
            "placeholder": "https://exemplo.com"
        },
        {
            "name": "maximized",
            "label": "Abrir maximizado (ignorado no modo Headless)",
            "type": "bool",
            "required": False,
            "default": True
        }
    ]

    # Guarda a instância do driver para outros blocos reutilizarem
    _driver_instance = None

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        url       = params.get("url", "").strip()
        maximized = params.get("maximized", True)

        if not url.startswith("http"):
            url = "https://" + url

        try:
            from engine.browser_config import get_browser_config
            cfg = get_browser_config()

            # Usa BrowserConfig global; sobrescreve maximized com o param do bloco
            # apenas se não estiver em headless
            if not cfg.headless:
                cfg.maximized = maximized

            options = cfg.to_chrome_options()
            service = Service(ChromeDriverManager().install())
            driver  = webdriver.Chrome(service=service, options=options)
            driver.get(url)

            OpenBrowserBlock._driver_instance = driver

            mode = "headless" if cfg.headless else "visual"
            return {
                "success": True,
                "message": f"Navegador aberto ({mode}): {url}",
                "data":    {"driver": driver}
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao abrir navegador: {str(e)}"
            }

    @classmethod
    def get_driver(cls):
        return cls._driver_instance

    @classmethod
    def close_driver(cls):
        if cls._driver_instance:
            cls._driver_instance.quit()
            cls._driver_instance = None
