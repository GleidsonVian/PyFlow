@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo   PyFlow RPA - Testes Automatizados
echo ============================================================
echo.

cd /d "%~dp0"

where pytest >nul 2>&1
if errorlevel 1 (
    echo [ERRO] pytest nao encontrado. Instale com:
    echo        pip install pytest
    cmd /k
    exit /b 1
)

echo Rodando todos os testes...
echo.
pytest tests/ -v --tb=short
echo.
echo ============================================================
echo   Pressione qualquer tecla para fechar.
echo ============================================================
cmd /k
