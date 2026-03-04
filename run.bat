@echo off
chcp 65001 >nul
echo ============================================
echo   Abrindo Ferramenta de Pesquisa APIB...
echo ============================================
echo.
echo O navegador vai abrir automaticamente.
echo Nao feche esta janela enquanto estiver usando.
echo.
echo Para encerrar: feche esta janela ou pressione CTRL+C
echo.

:: Criar pasta data se nao existir
if not exist "data" mkdir data

python -m streamlit run app.py

pause
