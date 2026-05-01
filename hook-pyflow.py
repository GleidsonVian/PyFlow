# hook-pyflow.py
# Hook customizado do PyInstaller para o PyFlow RPA
# Coloque na raiz do projeto junto com build.py
#
# Garante que todos os blocos e módulos dinâmicos sejam incluídos no .exe

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Coleta todos os submodulos dos blocos dinamicamente
hiddenimports = (
    collect_submodules('blocks') +
    collect_submodules('blocks.browser') +
    collect_submodules('blocks.control') +
    collect_submodules('blocks.files') +
    collect_submodules('blocks.integration') +
    collect_submodules('blocks.system') +
    collect_submodules('ui') +
    collect_submodules('engine') +
    collect_submodules('selenium') +
    collect_submodules('PySide6')
)

# Coleta arquivos de dados necessários
datas = collect_data_files('PySide6')
