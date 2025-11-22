@echo off
chcp 65001 >nul
echo ========================================
echo GitHub Remote 設定批次檔
echo ========================================
echo.

set "GITHUB_USER=sula316"
set "GITHUB_URL=https://github.com/%GITHUB_USER%"

echo GitHub 帳號: %GITHUB_USER%
echo GitHub URL: %GITHUB_URL%
echo.

REM 檢查是否已有 remote
cd /d "%~dp0"
git remote -v >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo 目前的 remote 設定:
    git remote -v
    echo.
    set /p "ADD_NEW=是否要新增另一個 remote？(Y/N，預設 N): "
    if /i not "%ADD_NEW%"=="Y" (
        echo 已取消
        pause
        exit /b 0
    )
    set "REMOTE_NAME=github"
) else (
    set "REMOTE_NAME=origin"
)

echo.
echo 請選擇操作：
echo 1. 使用現有的 GitHub 倉庫
echo 2. 建立新的 GitHub 倉庫（需要手動在 GitHub 網站建立）
echo.
set /p "CHOICE=請輸入選項 (1 或 2): "

if "%CHOICE%"=="1" (
    echo.
    set /p "REPO_NAME=請輸入 GitHub 倉庫名稱: "
    if "%REPO_NAME%"=="" (
        echo [錯誤] 倉庫名稱不能為空
        pause
        exit /b 1
    )
    set "REPO_URL=https://github.com/%GITHUB_USER%/%REPO_NAME%.git"
    
) else if "%CHOICE%"=="2" (
    echo.
    echo 請按照以下步驟建立新倉庫：
    echo 1. 前往 https://github.com/new
    echo 2. 輸入倉庫名稱（例如：3.Python）
    echo 3. 選擇 Public 或 Private
    echo 4. 不要勾選「Initialize this repository with a README」
    echo 5. 點擊「Create repository」
    echo.
    set /p "REPO_NAME=建立完成後，請輸入倉庫名稱: "
    if "%REPO_NAME%"=="" (
        echo [錯誤] 倉庫名稱不能為空
        pause
        exit /b 1
    )
    set "REPO_URL=https://github.com/%GITHUB_USER%/%REPO_NAME%.git"
) else (
    echo [錯誤] 無效的選項
    pause
    exit /b 1
)

echo.
echo 倉庫 URL: %REPO_URL%
echo Remote 名稱: %REMOTE_NAME%
echo.

REM 新增 remote
git remote add %REMOTE_NAME% %REPO_URL% 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [✓] 已新增 GitHub remote
) else (
    echo [錯誤] 新增 remote 失敗
    echo 可能原因：
    echo - remote 名稱已存在（請使用不同的名稱）
    echo - 倉庫 URL 不正確
    pause
    exit /b 1
)

echo.
echo 目前的 remote 設定:
git remote -v
echo.

REM 詢問是否要推送
set /p "PUSH=是否要立即推送到 GitHub？(Y/N，預設 Y): "
if /i "%PUSH%"=="" set "PUSH=Y"
if /i "%PUSH%"=="Y" (
    echo.
    echo [資訊] 正在推送到 GitHub...
    echo.
    git push -u %REMOTE_NAME% master
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [✓] 推送成功！
    ) else (
        echo.
        echo [警告] 推送可能失敗，請檢查：
        echo - 是否已登入 GitHub
        echo - 是否有推送權限
        echo - 倉庫是否存在
    )
) else (
    echo.
    echo 稍後可以執行以下命令推送：
    echo   git push -u %REMOTE_NAME% master
)

echo.
echo ========================================
echo 設定完成！
echo ========================================
echo.
pause

