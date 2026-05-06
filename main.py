"""
PyFlow RPA — Entry point.
Instala dependências ausentes automaticamente antes de iniciar a interface.
"""
import sys
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
    except Exception as e:
        print(f"[PyFlow] Erro ao verificar dependencias: {e} — continuando.")


def main():
    _ensure_requirements()

    # Importa a UI só depois de garantir as dependências
    from PySide6.QtWidgets import QApplication
    from ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("PyFlow RPA")
    app.setApplicationVersion("1.0.0")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
