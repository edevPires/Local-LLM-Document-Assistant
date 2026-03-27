@echo off
title llama-server — Qwen354B

:: Para usar o PATH do sistema, mantenha apenas: set LLAMA_EXE=llama-server
:: Para usar caminho completo, ajuste abaixo:
set LLAMA_EXE=C:\Users\bruno\llama.cpp\build\bin\llama-server.exe

set MODEL=%~dp0..\models\Qwen354B.gguf

echo.
echo  [llama-server] iniciando Qwen3.5-9B...
echo  modelo : %MODEL%
echo  porta  : 8080
echo  ctx    : 32768
echo.

"%LLAMA_EXE%" ^
    --model "%MODEL%" ^
    --n-gpu-layers -1 ^
    --ctx-size 32768 ^
    --port 8080

echo.
echo  [llama-server] encerrado.
pause
