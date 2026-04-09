@echo off
chcp 65001 >nul
echo ========================================
echo AI-DTS Git 推送脚本
echo ========================================
echo.

set /p commit_msg="请输入提交信息: "

echo.
echo [1/3] 添加文件到暂存区...
git add .

echo.
echo [2/3] 创建提交...
git commit -m "%commit_msg%"

echo.
echo [3/3] 推送到远程仓库...
git push

echo.
echo ========================================
echo 推送完成！
echo ========================================
pause
