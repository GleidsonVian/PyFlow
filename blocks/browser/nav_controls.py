"""
Blocos de navegação avançada para PyFlow RPA.
Coloque este arquivo em blocks/browser/nav_controls.py
"""
from blocks.base_block import BaseBlock
from blocks.browser.open_browser import OpenBrowserBlock


class NavigateToUrlBlock(BaseBlock):
    name = "Navegar para URL"
    description = "Navega para uma URL no navegador já aberto, sem abrir uma nova janela."
    category = "Navegador"

    params_schema = [
        {
            "name": "url",
            "label": "URL",
            "type": "str",
            "required": True,
            "default": "https://",
            "placeholder": "https://exemplo.com"
        }
    ]

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}
        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": False, "message": "Nenhum navegador aberto."}
        url = params.get("url", "").strip()
        if not url.startswith("http"):
            url = "https://" + url
        try:
            driver.get(url)
            return {"success": True, "message": f"Navegou para: {url}"}
        except Exception as e:
            return {"success": False, "message": f"Erro ao navegar: {str(e)}"}


class GoBackBlock(BaseBlock):
    name = "Voltar Página"
    description = "Volta para a página anterior no histórico do navegador."
    category = "Navegador"

    params_schema = []

    def execute(self, params: dict) -> dict:
        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": False, "message": "Nenhum navegador aberto."}
        try:
            driver.back()
            return {"success": True, "message": "Voltou para a página anterior"}
        except Exception as e:
            return {"success": False, "message": f"Erro ao voltar: {str(e)}"}


class GoForwardBlock(BaseBlock):
    name = "Avançar Página"
    description = "Avança para a próxima página no histórico do navegador."
    category = "Navegador"

    params_schema = []

    def execute(self, params: dict) -> dict:
        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": False, "message": "Nenhum navegador aberto."}
        try:
            driver.forward()
            return {"success": True, "message": "Avançou para a próxima página"}
        except Exception as e:
            return {"success": False, "message": f"Erro ao avançar: {str(e)}"}


class RefreshPageBlock(BaseBlock):
    name = "Atualizar Página"
    description = "Recarrega a página atual do navegador (F5)."
    category = "Navegador"

    params_schema = []

    def execute(self, params: dict) -> dict:
        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": False, "message": "Nenhum navegador aberto."}
        try:
            driver.refresh()
            return {"success": True, "message": "Página atualizada"}
        except Exception as e:
            return {"success": False, "message": f"Erro ao atualizar: {str(e)}"}


class OpenNewTabBlock(BaseBlock):
    name = "Abrir Nova Aba"
    description = "Abre uma nova aba no navegador e navega para a URL informada."
    category = "Navegador"

    params_schema = [
        {
            "name": "url",
            "label": "URL (opcional)",
            "type": "str",
            "required": False,
            "default": "",
            "placeholder": "https://exemplo.com (deixe vazio para aba em branco)"
        }
    ]

    def execute(self, params: dict) -> dict:
        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": False, "message": "Nenhum navegador aberto."}
        url = params.get("url", "").strip()
        try:
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            if url:
                if not url.startswith("http"):
                    url = "https://" + url
                driver.get(url)
                return {"success": True, "message": f"Nova aba aberta em: {url}"}
            return {"success": True, "message": "Nova aba em branco aberta"}
        except Exception as e:
            return {"success": False, "message": f"Erro ao abrir nova aba: {str(e)}"}


class CloseTabBlock(BaseBlock):
    name = "Fechar Aba"
    description = "Fecha a aba atual e volta para a aba anterior."
    category = "Navegador"

    params_schema = []

    def execute(self, params: dict) -> dict:
        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": False, "message": "Nenhum navegador aberto."}
        try:
            handles = driver.window_handles
            if len(handles) <= 1:
                return {"success": False, "message": "Só há uma aba aberta. Use 'Fechar Navegador' para encerrar."}
            driver.close()
            driver.switch_to.window(driver.window_handles[-1])
            return {"success": True, "message": "Aba fechada, voltou para a aba anterior"}
        except Exception as e:
            return {"success": False, "message": f"Erro ao fechar aba: {str(e)}"}


class SwitchTabBlock(BaseBlock):
    name = "Trocar de Aba"
    description = "Troca para uma aba específica pelo índice (0 = primeira aba, 1 = segunda...)."
    category = "Navegador"

    params_schema = [
        {
            "name": "tab_index",
            "label": "Índice da aba (0 = primeira)",
            "type": "str",
            "required": True,
            "default": "0",
            "placeholder": "0, 1, 2..."
        }
    ]

    def execute(self, params: dict) -> dict:
        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": False, "message": "Nenhum navegador aberto."}
        try:
            index = int(params.get("tab_index", 0))
        except ValueError:
            return {"success": False, "message": "Índice inválido. Use um número inteiro (0, 1, 2...)."}
        try:
            handles = driver.window_handles
            if index >= len(handles):
                return {"success": False, "message": f"Aba {index} não existe. Total de abas: {len(handles)}"}
            driver.switch_to.window(handles[index])
            return {"success": True, "message": f"Trocou para aba {index} — URL: {driver.current_url}"}
        except Exception as e:
            return {"success": False, "message": f"Erro ao trocar de aba: {str(e)}"}


class CloseBrowserBlock(BaseBlock):
    name = "Fechar Navegador"
    description = "Fecha todas as abas e encerra completamente o navegador."
    category = "Navegador"

    params_schema = []

    def execute(self, params: dict) -> dict:
        driver = OpenBrowserBlock.get_driver()
        if not driver:
            return {"success": True, "message": "Navegador já estava fechado."}
        try:
            driver.quit()
            OpenBrowserBlock._driver_instance = None
            return {"success": True, "message": "Navegador fechado com sucesso"}
        except Exception as e:
            return {"success": False, "message": f"Erro ao fechar navegador: {str(e)}"}
