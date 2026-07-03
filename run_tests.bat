@echo off
chcp 65001 >nul

:: Se ainda nao foi relancado, abre uma nova janela persistente e sai
if "%RELAUNCHED%"=="" (
    set RELAUNCHED=1
    start cmd /k ""%~f0""
    exit
)

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
    echo.
    pause
    exit /b 1
)

echo Rodando todos os testes...
echo.
pytest tests/ -v --tb=short
echo.
echo ============================================================
echo   88 testes concluidos. Feche esta janela quando quiser.
echo ============================================================
