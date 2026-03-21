@echo off
title llama-server — Qwen3.5-9B

set LLAMA_EXE=C:\Users\bruno\llama.cpp\build\bin\llama-server.exe
set MODEL=%~dp0backend\models\Qwen3.5-9B-Q4_K_M.gguf

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
