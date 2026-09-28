@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PORT=8765"
if exist ".web-port" for /f "usebackq delims=" %%P in (".web-port") do set "PORT=%%P"
echo 正在启动书中世界模拟器...
echo 需要停止时，请运行 停止杏花沟.bat。
where python >nul 2>nul
if not errorlevel 1 (
  start "" /min python web\server.py --port %PORT% --open
  exit /b 0
)
where py >nul 2>nul
if not errorlevel 1 (
  start "" /min py web\server.py --port %PORT% --open
  exit /b 0
)
echo 未找到 Python，请先安装 Python 3.12+。
pause
exit /b 1
