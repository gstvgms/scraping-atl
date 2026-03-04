@echo off
chcp 65001 >nul
echo ============================================
echo   Instalando a Ferramenta de Pesquisa APIB
echo ============================================
echo.

:: Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao foi encontrado no seu computador.
    echo Por favor, instale o Python em: https://www.python.org/downloads/
    echo Marque a opcao "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)

echo [OK] Python encontrado!
echo.

:: Criar pasta data se nao existir
if not exist "data" mkdir data
echo [OK] Pasta de dados criada.
echo.

:: Instalar dependencias
echo Instalando dependencias (isso pode levar alguns minutos)...
echo.
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao instalar dependencias.
    echo Tente executar como Administrador.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Instalacao concluida com sucesso!
echo   Execute o arquivo "run.bat" para abrir
echo   a ferramenta.
echo ============================================
echo.
pause
