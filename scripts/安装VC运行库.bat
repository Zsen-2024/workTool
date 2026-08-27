@echo off
chcp 65001 >nul
echo ========================================
echo   WorkTool - 安装 VC++ 运行库（x64）
echo ========================================
echo.
echo 若 WorkTool.exe 提示缺少 api-ms-win-core-path-l1-1-0.dll，
echo 通常是因为系统缺少 VC++ 2015-2022 运行库。
echo.
echo 即将打开微软官方下载页，请下载并运行 vc_redist.x64.exe
echo （需要管理员权限，安装一次即可）
echo.
echo 要求：Windows 10/11 64 位。Windows 7/8 不支持本程序。
echo.
pause
start https://aka.ms/vs/17/release/vc_redist.x64.exe
echo.
echo 安装完成后请重启电脑，再运行 WorkTool.exe
pause
