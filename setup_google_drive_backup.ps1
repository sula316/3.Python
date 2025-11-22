# Google Drive 備份設定腳本
# 將 D:\3.Python 複製到 Google Drive 同步資料夾

param(
    [string]$GoogleDrivePath = "G:\我的雲端硬碟\3.Python_Backup"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Google Drive 備份設定" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$sourcePath = "D:\3.Python"
$targetPath = $GoogleDrivePath

# 檢查來源資料夾
if (-not (Test-Path $sourcePath)) {
    Write-Host "❌ 錯誤：找不到來源資料夾：$sourcePath" -ForegroundColor Red
    exit 1
}

Write-Host "✓ 來源資料夾：$sourcePath" -ForegroundColor Green

# 檢查目標磁碟機
$driveLetter = $targetPath.Substring(0, 1)
$driveInfo = [System.IO.DriveInfo]::GetDrives() | Where-Object { $_.Name -eq "$driveLetter`:\" }

if (-not $driveInfo) {
    Write-Host "❌ 錯誤：找不到磁碟機 $driveLetter`:" -ForegroundColor Red
    Write-Host ""
    Write-Host "請確認：" -ForegroundColor Yellow
    Write-Host "1. Google Drive 是否已安裝並同步" -ForegroundColor Gray
    Write-Host "2. 磁碟機代號是否正確" -ForegroundColor Gray
    Write-Host "3. 路徑是否正確：$targetPath" -ForegroundColor Gray
    Write-Host ""
    $manualPath = Read-Host "請手動輸入正確的 Google Drive 路徑（或按 Enter 跳過）"
    if (-not [string]::IsNullOrWhiteSpace($manualPath)) {
        $targetPath = $manualPath
    } else {
        Write-Host "已取消設定" -ForegroundColor Yellow
        exit 0
    }
}

# 檢查目標資料夾是否存在
if (Test-Path $targetPath) {
    Write-Host "⚠ 目標資料夾已存在：$targetPath" -ForegroundColor Yellow
    $overwrite = Read-Host "是否要覆蓋？(y/n)"
    if ($overwrite -ne "y") {
        Write-Host "已取消複製" -ForegroundColor Yellow
        exit 0
    }
    Write-Host "正在刪除舊資料夾..." -ForegroundColor Cyan
    Remove-Item $targetPath -Recurse -Force -ErrorAction SilentlyContinue
}

# 建立目標資料夾的父目錄
$parentPath = Split-Path $targetPath -Parent
if (-not (Test-Path $parentPath)) {
    Write-Host "正在建立父資料夾：$parentPath" -ForegroundColor Cyan
    try {
        New-Item -ItemType Directory -Path $parentPath -Force | Out-Null
        Write-Host "✓ 已建立父資料夾" -ForegroundColor Green
    } catch {
        Write-Host "❌ 無法建立父資料夾：$_" -ForegroundColor Red
        exit 1
    }
}

# 使用 robocopy 複製（對中文路徑支援較好）
Write-Host ""
Write-Host "正在複製資料夾到 Google Drive..." -ForegroundColor Cyan
Write-Host "來源：$sourcePath" -ForegroundColor Gray
Write-Host "目標：$targetPath" -ForegroundColor Gray
Write-Host ""
Write-Host "這可能需要一些時間，請稍候..." -ForegroundColor Yellow
Write-Host ""

$robocopyArgs = @(
    "`"$sourcePath`""
    "`"$targetPath`""
    "/E"           # 包含子資料夾
    "/COPYALL"     # 複製所有檔案屬性
    "/R:3"         # 重試 3 次
    "/W:5"         # 等待 5 秒
    "/NP"          # 不顯示進度百分比
    "/NDL"         # 不記錄目錄清單
    "/NFL"         # 不記錄檔案清單
)

try {
    $process = Start-Process -FilePath "robocopy" -ArgumentList $robocopyArgs -Wait -NoNewWindow -PassThru
    
    # robocopy 的退出代碼：0-7 表示成功，8+ 表示錯誤
    if ($process.ExitCode -le 7) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "✓ 複製完成！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "備份位置：$targetPath" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "注意事項：" -ForegroundColor Yellow
        Write-Host "- Google Drive 會自動同步此資料夾到雲端" -ForegroundColor Gray
        Write-Host "- 如果資料夾很大，同步可能需要一些時間" -ForegroundColor Gray
        Write-Host "- 建議定期更新備份，或使用 GitHub 作為主要版本控制" -ForegroundColor Gray
    } else {
        Write-Host ""
        Write-Host "⚠ 複製過程中可能有錯誤（退出代碼：$($process.ExitCode)）" -ForegroundColor Yellow
        Write-Host "請檢查目標資料夾是否已建立" -ForegroundColor Gray
    }
} catch {
    Write-Host ""
    Write-Host "❌ 複製失敗：$_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "設定完成！" -ForegroundColor Green

