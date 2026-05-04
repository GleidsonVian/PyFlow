"""
build.py — PyFlow RPA
Script de empacotamento para gerar o executável standalone (.exe)

Como usar:
    python build.py

O executável será gerado em: dist/PyFlowRPA/PyFlowRPA.exe
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


# ── Configurações ──────────────────────────────────────────────────────
APP_NAME    = "PyFlowRPA"
APP_VERSION = "1.0.0"
MAIN_SCRIPT = "main.py"
DIST_DIR    = "dist"
BUILD_DIR   = "build"
SPEC_FILE   = f"{APP_NAME}.spec"

# Pastas e arquivos extras a incluir no .exe
EXTRA_DATAS = [
    ("blocks",  "blocks"),
    ("engine",  "engine"),
    ("ui",      "ui"),
    ("flows",   "flows"),
]

# Imports ocultos necessários (módulos que o PyInstaller não detecta automaticamente)
HIDDEN_IMPORTS = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "selenium",
    "selenium.webdriver",
    "selenium.webdriver.chrome",
    "selenium.webdriver.chrome.service",
    "selenium.webdriver.chrome.options",
    "selenium.webdriver.common.by",
    "selenium.webdriver.common.keys",
    "selenium.webdriver.common.action_chains",
    "selenium.webdriver.support.ui",
    "selenium.webdriver.support.expected_conditions",
    "webdriver_manager",
    "webdriver_manager.chrome",
    "schedule",
    "pyautogui",
    "plyer",
    "winotify",
    "blocks.browser.open_browser",
    "blocks.browser.click_element",
    "blocks.browser.fill_field",
    "blocks.browser.screenshot",
    "blocks.browser.extract_text",
    "blocks.browser.extract_list",
    "blocks.browser.press_key",
    "blocks.browser.scroll_page",
    "blocks.browser.get_current_url",
    "blocks.browser.mouse_action",
    "blocks.browser.nav_controls",
    "blocks.browser.execute_script",
    "blocks.browser.smart_wait",
    "blocks.browser.smart_click",
    "blocks.control.wait",
    "blocks.control.if_block",
    "blocks.control.loop_block",
    "blocks.control.for_each_block",
    "blocks.control.show_message",
    "blocks.control.desktop_notification",
    "blocks.control.text_manipulation",
    "blocks.files.read_csv",
    "blocks.files.save_text",
    "blocks.files.save_csv",
    "blocks.files.sqlite_block",
    "blocks.files.excel_block",
    "blocks.files.zip_block",
    "blocks.files.load_env_block",
    "blocks.integration.http_request",
    "blocks.integration.send_email",
    "blocks.integration.ftp_block",
    "blocks.control.subflow_block",
    "blocks.system.keyboard_action",
    "blocks.system.clipboard_block",
    "blocks.system.hash_block",
    "blocks.system.ocr_block",
    "engine.blocks_registry",
    "ui.block_panel",
    "ui.canvas",
    "ui.main_window",
    "ui.properties_panel",
    "ui.param_dialog",
    "ui.log_panel",
    "ui.validation_dialog",
    "ui.run_history_dialog",
    "engine.flow_validator",
    "engine.run_history",
    "ui.flow_manager_dialog",
    "ui.scheduler_dialog",
    "ui.block_docs",
    "engine.runner",
    "engine.flow_manager",
    "engine.flow_exporter",
]


def check_requirements():
    """Verifica se o PyInstaller está instalado."""
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} encontrado")
    except ImportError:
        print("✗ PyInstaller não instalado. Rodando: pip install pyinstaller")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)


def clean_build():
    """Remove pastas de build anteriores."""
    for folder in [BUILD_DIR, DIST_DIR, "__pycache__"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"  Removido: {folder}/")
    if os.path.exists(SPEC_FILE):
        os.remove(SPEC_FILE)
        print(f"  Removido: {SPEC_FILE}")


def create_folders():
    """Garante que as pastas necessárias existam no dist."""
    for folder in ["flows", "saida", "screenshots", "exports", "dados"]:
        os.makedirs(folder, exist_ok=True)


def build():
    """Executa o PyInstaller para gerar o executável."""
    print("\n🔨 Construindo executável...\n")

    # Monta os argumentos --add-data
    data_args = []
    for src, dst in EXTRA_DATAS:
        if os.path.exists(src):
            sep = ";" if sys.platform == "win32" else ":"
            data_args += ["--add-data", f"{src}{sep}{dst}"]

    # Monta os --hidden-import
    hidden_args = []
    for imp in HIDDEN_IMPORTS:
        hidden_args += ["--hidden-import", imp]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onedir",                  # pasta única (mais rápido para iniciar que --onefile)
        "--windowed",                # sem console (remova se quiser ver logs)
        "--noconfirm",               # sobrescreve sem perguntar
        "--clean",                   # limpa cache do PyInstaller
        "--distpath", DIST_DIR,
        "--workpath", BUILD_DIR,
        *data_args,
        *hidden_args,
        MAIN_SCRIPT,
    ]

    print("Comando PyInstaller:")
    print(" ".join(cmd[:6]) + " ...")
    print()

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print("\n❌ Build falhou! Verifique os erros acima.")
        return False

    return True


def post_build():
    """Copia arquivos extras para o dist após o build."""
    dist_app = os.path.join(DIST_DIR, APP_NAME)
    if not os.path.exists(dist_app):
        return

    # Cria pastas necessárias no dist
    for folder in ["flows", "saida", "screenshots", "exports", "dados"]:
        os.makedirs(os.path.join(dist_app, folder), exist_ok=True)

    # Copia fluxos existentes se houver
    if os.path.exists("flows"):
        for f in os.listdir("flows"):
            if f.endswith(".json"):
                shutil.copy(
                    os.path.join("flows", f),
                    os.path.join(dist_app, "flows", f)
                )
                print(f"  Fluxo copiado: {f}")

    # Cria README de uso
    readme = os.path.join(dist_app, "LEIA-ME.txt")
    with open(readme, "w", encoding="utf-8") as f:
        f.write(f"""PyFlow RPA v{APP_VERSION}
====================

Como usar:
  1. Execute PyFlowRPA.exe
  2. Arraste blocos do painel esquerdo para o canvas
  3. Configure os parâmetros de cada bloco
  4. Clique em Executar

Pastas importantes:
  flows/       - Fluxos salvos (.json)
  saida/       - Arquivos gerados pelos blocos
  screenshots/ - Screenshots tiradas durante execução
  exports/     - Scripts Python exportados
  dados/       - Arquivos CSV de entrada

Requisitos do sistema:
  - Windows 10 ou superior
  - Google Chrome instalado (para automação web)
  - ChromeDriver é baixado automaticamente pelo webdriver-manager

Suporte:
  PyFlow RPA é um projeto open source desenvolvido com Python + PySide6.
""")
    print(f"  README criado: {readme}")


def print_summary(success: bool):
    dist_app = os.path.join(DIST_DIR, APP_NAME)
    exe_path = os.path.join(dist_app, f"{APP_NAME}.exe")

    print("\n" + "=" * 60)
    if success and os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"✅ BUILD CONCLUÍDO COM SUCESSO!")
        print(f"")
        print(f"   Executável: {exe_path}")
        print(f"   Tamanho:    {size_mb:.1f} MB")
        print(f"   Pasta:      {dist_app}/")
        print(f"")
        print(f"   Para distribuir: compacte a pasta '{dist_app}/' em um .zip")
        print(f"   Para executar:   {exe_path}")
    else:
        print("❌ BUILD FALHOU!")
        print("   Verifique os erros acima e tente novamente.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print("=" * 60)
    print(f"  PyFlow RPA — Build Script v{APP_VERSION}")
    print("=" * 60)

    print("\n1. Verificando dependências...")
    check_requirements()

    print("\n2. Limpando builds anteriores...")
    clean_build()

    print("\n3. Criando pastas necessárias...")
    create_folders()

    print("\n4. Executando PyInstaller...")
    success = build()

    if success:
        print("\n5. Finalizando dist...")
        post_build()

    print_summary(success)
