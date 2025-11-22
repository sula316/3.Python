@echo off
chcp 65001 >nul
echo ========================================
echo Google Drive 備份批次檔
echo ========================================
echo.

set "SOURCE=D:\3.Python"
set "TARGET=G:\我的雲端硬碟\3.Python_Backup"

echo 來源資料夾: %SOURCE%
echo 目標資料夾: %TARGET%
echo.

REM 檢查來源資料夾是否存在
if not exist "%SOURCE%" (
    echo [錯誤] 找不到來源資料夾: %SOURCE%
    pause
    exit /b 1
)

echo [✓] 來源資料夾存在
echo.

REM 檢查目標磁碟機是否存在
if not exist "G:\" (
    echo [警告] 找不到 G: 磁碟機
    echo 請確認 Google Drive 是否已正確安裝並同步
    echo.
    set /p "CONTINUE=是否要繼續？(Y/N): "
    if /i not "%CONTINUE%"=="Y" (
        echo 已取消
        pause
        exit /b 0
    )
)

REM 建立目標資料夾的父目錄（如果不存在）
set "PARENT=G:\我的雲端硬碟"
if not exist "%PARENT%" (
    echo [資訊] 正在建立父資料夾: %PARENT%
    mkdir "%PARENT%" 2>nul
    if errorlevel 1 (
        echo [錯誤] 無法建立父資料夾
        pause
        exit /b 1
    )
)

REM 檢查目標資料夾是否存在
if exist "%TARGET%" (
    echo [警告] 目標資料夾已存在: %TARGET%
    echo.
    set /p "OVERWRITE=是否要覆蓋？(Y/N): "
    if /i not "%OVERWRITE%"=="Y" (
        echo 已取消
        pause
        exit /b 0
    )
    echo [資訊] 正在刪除舊資料夾...
    rmdir /s /q "%TARGET%" 2>nul
)

echo.
echo [資訊] 開始複製資料夾到 Google Drive...
echo 這可能需要一些時間，請稍候...
echo.

REM 使用 robocopy 複製（對中文路徑支援較好）
robocopy "%SOURCE%" "%TARGET%" /E /COPYALL /R:3 /W:5 /NP /NDL /NFL

REM robocopy 的退出代碼：0-7 表示成功，8+ 表示錯誤
if %ERRORLEVEL% LEQ 7 (
    echo.
    echo ========================================
    echo [✓] 複製完成！
    echo ========================================
    echo.
    echo 備份位置: %TARGET%
    echo.
    echo 注意事項:
    echo - Google Drive 會自動同步此資料夾到雲端
    echo - 如果資料夾很大，同步可能需要一些時間
    echo - 建議定期更新備份，或使用 GitHub 作為主要版本控制
) else (
    echo.
    echo [警告] 複製過程中可能有錯誤（退出代碼: %ERRORLEVEL%）
    echo 請檢查目標資料夾是否已建立
)

echo.
pause

