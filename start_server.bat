@echo off
REM Vai para a pasta do projeto
cd /d D:\GIT\OrcamentosBolos\python\server

REM Ativa o virtualenv
call venv\Scripts\activate.bat

REM Pega o IP da rede local (IPv4 da interface principal)
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R "IPv4"') do (
    set IP=%%a
)
REM Remove espaços do começo do IP
set IP=%IP: =%
echo Servidor rodando na rede local em http://%IP%:5080

REM Roda o app e grava log
python src\app.py >> server_log.txt 2>&1
pause
