"""
PyFlow RPA — Entry point.
Instala dependências ausentes automaticamente antes de iniciar a interface.
"""
import os
import sys

# Força o DPI Awareness e silencia avisos do Qt antes de importar qualquer coisa da UI
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.window=false"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

# No Windows, tenta setar a consciência de DPI via ctypes se falhar via Qt
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

import subprocess
import importlib
from pathlib import Path


def _ensure_requirements():
    """
    Verifica o requirements.txt e instala pacotes ausentes com pip.
    Executado silenciosamente antes da UI abrir.
    """
    req_file = Path(__file__).parent / "requirements.txt"
    if not req_file.exists():
        return

    # Lê os pacotes do requirements (ignora comentários e linhas vazias)
    packages = []
    for line in req_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            packages.append(line)

    if not packages:
        return

    print("[PyFlow] Verificando dependências...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
             "-r", str(req_file)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print("[PyFlow] Dependencias OK.")
        else:
            print(f"[PyFlow] Aviso ao instalar dependencias:\n{result.stderr[:500]}")
    except subprocess.TimeoutExpired:
        print("[PyFlow] Timeout ao verificar dependencias — continuando.")
    except BaseException as e:
        print(f"[PyFlow] Aviso ao verificar dependencias: {e} — continuando.")


def main():
    _ensure_requirements()

    # Importa a UI só depois de garantir as dependências
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QIcon
    from ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("PyFlow RPA")
    app.setApplicationVersion("1.0.0")

    # Ícone da aplicação (janela + taskbar)
    icon_path = Path(__file__).parent / "assets" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    if "--daemon" in sys.argv:
        print("[PyFlow] Iniciando no modo Daemon (Background)...")
        from engine.api_server import get_api_server
        from ui.scheduler_dialog import get_engine
        server = get_api_server()
        server.start()
        get_engine().start()
        print(f"[PyFlow] Daemon rodando silenciosamente. API escutando em http://localhost:{server.port}")
        sys.exit(app.exec())

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
