from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from blocks.base_block import BaseBlock


class OpenBrowserBlock(BaseBlock):
    name = "Abrir Navegador"
    description = "Abre o Google Chrome em uma URL especificada"
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
            "label": "Abrir maximizado",
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

        url = params.get("url", "").strip()
        maximized = params.get("maximized", True)

        # Garante que a URL tem protocolo
        if not url.startswith("http"):
            url = "https://" + url

        try:
            options = Options()
            if maximized:
                options.add_argument("--start-maximized")

            # webdriver-manager baixa o chromedriver automaticamente
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)

            # Salva o driver na classe para blocos seguintes reutilizarem
            OpenBrowserBlock._driver_instance = driver

            return {
                "success": True,
                "message": f"Navegador aberto em: {url}",
                "data": {"driver": driver}
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao abrir navegador: {str(e)}"
            }

    @classmethod
    def get_driver(cls):
        """Retorna o driver ativo para outros blocos usarem."""
        return cls._driver_instance

    @classmethod
    def close_driver(cls):
        """Fecha o navegador e limpa a instância."""
        if cls._driver_instance:
            cls._driver_instance.quit()
            cls._driver_instance = None