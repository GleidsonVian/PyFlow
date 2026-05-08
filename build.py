"""
build.py — PyFlow RPA (Smart Version)
Script de empacotamento automático que detecta novos blocos e dependências.
"""
import os
import sys
import shutil
import subprocess
import glob
from pathlib import Path

# ── Configurações ──────────────────────────────────────────────────────
APP_NAME    = "PyFlowRPA"
APP_VERSION = "1.1.0"
MAIN_SCRIPT = "main.py"
DIST_DIR    = "dist"
BUILD_DIR   = "build"
SPEC_FILE   = f"{APP_NAME}.spec"

def get_block_imports():
    """Descobre automaticamente todos os blocos na pasta blocks/"""
    block_imports = []
    # Busca todos os arquivos .py dentro de subpastas de blocks/
    for file_path in glob.glob("blocks/**/*.py", recursive=True):
        if "__init__.py" in file_path:
            continue
        # Converte path/to/block.py em path.to.block
        mod_name = file_path.replace(os.path.sep, ".").replace("/", ".").replace(".py", "")
        block_imports.append(mod_name)
    return block_imports

def get_ui_imports():
    """Descobre automaticamente todos os módulos da UI"""
    ui_imports = []
    for file_path in glob.glob("ui/*.py"):
        if "__init__.py" in file_path:
            continue
        mod_name = file_path.replace(os.path.sep, ".").replace("/", ".").replace(".py", "")
        ui_imports.append(mod_name)
    return ui_imports

# Pastas e arquivos extras a incluir no .exe
EXTRA_DATAS = [
    ("blocks",  "blocks"),
    ("engine",  "engine"),
    ("ui",      "ui"),
    ("flows",   "flows"),
]

# Bibliotecas base
BASE_IMPORTS = [
    "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets",
    "selenium", "webdriver_manager", "pyautogui", "cv2", 
    "numpy", "pytesseract", "schedule", "requests", "flask"
]

def check_requirements():
    print("✓ Verificando ambiente...")
    libs = ["pyinstaller", "opencv-python", "pyautogui"]
    for lib in libs:
        try:
            __import__(lib.replace("-", "_"))
        except ImportError:
            print(f"✗ {lib} não instalado. Instalando...")
            subprocess.run([sys.executable, "-m", "pip", "install", lib], check=True)

def clean_build():
    print("✓ Limpando lixo de builds anteriores...")
    for folder in [BUILD_DIR, DIST_DIR, "__pycache__"]:
        if os.path.exists(folder):
            shutil.rmtree(folder, ignore_errors=True)

def build():
    print(f"\n🔨 Construindo {APP_NAME} v{APP_VERSION}...\n")
    
    # Coleta todos os imports dinâmicos
    blocks = get_block_imports()
    uis = get_ui_imports()
    all_hidden = list(set(BASE_IMPORTS + blocks + uis + ["engine.blocks_registry", "engine.runner", "engine.execution_context"]))
    
    print(f"  → {len(blocks)} blocos detectados")
    print(f"  → {len(uis)} arquivos de interface detectados")

    # Monta os argumentos
    data_args = []
    sep = ";" if sys.platform == "win32" else ":"
    for src, dst in EXTRA_DATAS:
        if os.path.exists(src):
            data_args += ["--add-data", f"{src}{sep}{dst}"]

    hidden_args = []
    for imp in all_hidden:
        hidden_args += ["--hidden-import", imp]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--distpath", DIST_DIR,
        "--workpath", BUILD_DIR,
        *data_args,
        *hidden_args,
        MAIN_SCRIPT,
    ]

    result = subprocess.run(cmd)
    return result.returncode == 0

def post_build():
    dist_app = os.path.join(DIST_DIR, APP_NAME)
    if not os.path.exists(dist_app): return

    # Cria pastas de runtime
    for folder in ["flows", "saida", "screenshots", "exports", "dados"]:
        os.makedirs(os.path.join(dist_app, folder), exist_ok=True)
    
    # Copia README customizado
    with open(os.path.join(dist_app, "COMO-USAR.txt"), "w", encoding="utf-8") as f:
        f.write(f"PyFlow RPA v{APP_VERSION}\nInstruções: Execute {APP_NAME}.exe para começar.")

if __name__ == "__main__":
    check_requirements()
    clean_build()
    if build():
        post_build()
        print(f"\n✅ SUCESSO! O executável está em: {os.path.abspath(DIST_DIR)}")
    else:
        print("\n❌ FALHA no build.")
