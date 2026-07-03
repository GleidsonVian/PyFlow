@echo off
echo.
echo ============================================================
echo   PyFlow RPA — Testes Automatizados
echo ============================================================
echo.

cd /d "%~dp0"

where pytest >nul 2>&1
if errorlevel 1 (
    echo [ERRO] pytest nao encontrado. Instale com:
    echo        pip install pytest
    pause
    exit /b 1
)

echo Rodando todos os testes...
echo.
pytest tests/ -v --tb=short

echo.
echo ============================================================
echo   Cobertura de codigo (opcional):
echo   pip install pytest-cov
echo   pytest tests/ --cov=blocks --cov-report=term-missing
echo ============================================================
echo.
pause
