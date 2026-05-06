"""
Configuração global do navegador Chrome para o PyFlow RPA.
Singleton compartilhado entre OpenBrowserBlock e a interface.
"""


class BrowserConfig:
    """Configurações do Chrome aplicadas ao abrir o navegador."""

    def __init__(self):
        self.headless       = False   # True = sem janela (produção/servidor)
        self.maximized      = True    # Abre maximizado (só no modo visual)
        self.window_width   = 1920    # Largura quando não maximizado
        self.window_height  = 1080    # Altura quando não maximizado
        self.user_agent     = ""      # Vazio = padrão do Chrome
        self.disable_images = False   # True = mais rápido, sem imagens
        self.incognito      = False   # Aba anônima
        self.extra_args     = ""      # Args extras separados por espaço

    def to_chrome_options(self):
        """Retorna um objeto Options configurado para o webdriver."""
        from selenium.webdriver.chrome.options import Options
        opts = Options()

        if self.headless:
            opts.add_argument("--headless=new")   # headless moderno (Chrome 112+)
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--disable-gpu")
            opts.add_argument(f"--window-size={self.window_width},{self.window_height}")
        else:
            if self.maximized:
                opts.add_argument("--start-maximized")
            else:
                opts.add_argument(f"--window-size={self.window_width},{self.window_height}")

        if self.user_agent:
            opts.add_argument(f"--user-agent={self.user_agent}")

        if self.disable_images:
            prefs = {"profile.managed_default_content_settings.images": 2}
            opts.add_experimental_option("prefs", prefs)

        if self.incognito:
            opts.add_argument("--incognito")

        # Remove a flag "Chrome is being controlled by automated software"
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        if self.extra_args:
            for arg in self.extra_args.split():
                opts.add_argument(arg)

        return opts

    def to_dict(self) -> dict:
        return {
            "headless":       self.headless,
            "maximized":      self.maximized,
            "window_width":   self.window_width,
            "window_height":  self.window_height,
            "user_agent":     self.user_agent,
            "disable_images": self.disable_images,
            "incognito":      self.incognito,
            "extra_args":     self.extra_args,
        }

    def from_dict(self, data: dict):
        self.headless       = data.get("headless",       self.headless)
        self.maximized      = data.get("maximized",      self.maximized)
        self.window_width   = data.get("window_width",   self.window_width)
        self.window_height  = data.get("window_height",  self.window_height)
        self.user_agent     = data.get("user_agent",     self.user_agent)
        self.disable_images = data.get("disable_images", self.disable_images)
        self.incognito      = data.get("incognito",      self.incognito)
        self.extra_args     = data.get("extra_args",     self.extra_args)


# ── Singleton ──────────────────────────────────────────────────────────────────

_browser_config = BrowserConfig()


def get_browser_config() -> BrowserConfig:
    return _browser_config
