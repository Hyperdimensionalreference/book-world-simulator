@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".web-server.pid" (
  echo 本项目没有正在运行的服务。
  exit /b 0
)
set /p SERVER_PID=<".web-server.pid"
set "PORT=8765"
if exist ".web-port" for /f "usebackq delims=" %%P in (".web-port") do set "PORT=%%P"
powershell -NoProfile -Command "$id = [int]'%SERVER_PID%'; $port = [int]'%PORT%'; $listener = Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -eq $id }; if ($listener) { Stop-Process -Id $id -Force; Remove-Item -LiteralPath '.web-server.pid' -ErrorAction SilentlyContinue; Write-Output '服务已停止。' } else { Write-Output '没有找到匹配的服务进程，未停止其他进程。' }"
