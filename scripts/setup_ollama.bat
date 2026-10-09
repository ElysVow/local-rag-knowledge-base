@echo off
chcp 65001 >nul
REM ============================================
REM  本地大模型知识库 · 一键安装 Ollama 模型
REM  用法：双击运行，或命令行执行 scripts\setup_ollama.bat
REM ============================================

echo [1/2] 检查 Ollama ...
where ollama >nul 2>nul
if errorlevel 1 (
  echo 未检测到 Ollama，请先到 https://ollama.com/download 安装，或执行:
  echo   winget install --id Ollama.Ollama -e
  pause
  exit /b 1
)

echo [2/2] 拉取 qwen2.5:7b（约 4.5GB，首次较慢，之后离线可用）...
ollama pull qwen2.5:7b

echo.
echo 完成！可选的其它模型（按需执行）：
echo   ollama pull qwen2.5:3b    ^(低配机器推荐^)
echo   ollama pull llama3.1:8b   ^(英文效果好^)
echo   ollama pull deepseek-r1:7b
pause
