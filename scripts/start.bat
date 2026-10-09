@echo off
chcp 65001 >nul
REM ============================================
REM  本地大模型知识库 · 启动服务
REM  用法：双击运行，或在命令行执行 scripts\start.bat
REM  启动后浏览器访问 http://127.0.0.1:8000
REM ============================================

cd /d "%~dp0.."

echo 检查依赖（首次运行会自动安装）...
python -c "import flask, sentence_transformers, faiss, pypdf, docx, requests" >nul 2>nul
if errorlevel 1 (
  echo 正在安装依赖 ...
  python -m pip install -r requirements.txt
)

echo 启动服务：http://127.0.0.1:8000
python app.py

pause
