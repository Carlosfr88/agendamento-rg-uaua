@echo off
setlocal
title Agendamento RG - SEDES Uaua - Etapa 1

echo ==========================================================
echo   AGENDAMENTO ELETRONICO DE RG - SEDES Uaua
echo   ETAPA 1 - PREPARACAO DO AMBIENTE
echo ==========================================================
echo.

if not exist "E:\" (
    echo ERRO: a unidade E: nao foi encontrada.
    pause
    exit /b 1
)

cd /d E:\
if not exist "E:\agendamento-rg-uaua" mkdir "E:\agendamento-rg-uaua"
cd /d E:\agendamento-rg-uaua

if not exist "venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    py -3.13 -m venv venv
    if errorlevel 1 (
        echo.
        echo ERRO ao criar o ambiente virtual.
        echo Verifique se o Python 3.13 esta instalado.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

if not exist ".env" copy ".env.example" ".env"

echo.
echo ==========================================================
echo ETAPA 1 PREPARADA COM SUCESSO
echo ==========================================================
echo.
echo Para iniciar:
echo   cd /d E:\agendamento-rg-uaua
echo   venv\Scripts\activate
echo   python run.py
echo.
pause
