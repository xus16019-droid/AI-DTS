@echo off
chcp 65001 >nul
echo ========================================
echo AI-DTS Git 初始化脚本
echo ========================================
echo.

set /p github_user="请输入您的GitHub用户名: "
set /p github_email="请输入您的GitHub邮箱: "
set /p repo_name="请输入仓库名称 (默认: AI-DTS): "

if "%repo_name%"=="" set repo_name=AI-DTS

echo.
echo [1/4] 配置Git用户信息...
git config --global user.name "%github_user%"
git config --global user.email "%github_email%"

echo.
echo [2/4] 添加文件到暂存区...
git add .

echo.
echo [3/4] 创建首次提交...
git commit -m "Initial commit: AI-DTS 制造偏差处理方案自动生成系统"

echo.
echo [4/4] 关联远程仓库并推送...
git remote add origin https://github.com/%github_user%/%repo_name%.git
git branch -M main
git push -u origin main

echo.
echo ========================================
echo 初始化完成！
echo ========================================
echo 仓库地址: https://github.com/%github_user%/%repo_name%
echo ========================================
pause
