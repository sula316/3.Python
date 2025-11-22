# Git 雙重備份設定腳本
# 功能：設定 GitHub remote 和 Google Drive 同步

param(
    [string]$GitHubRepoUrl = "",
    [string]$GoogleDrivePath = ""
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Git 雙重備份設定腳本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查當前目錄
$currentDir = Get-Location
if (-not (Test-Path "$currentDir\.git")) {
    Write-Host "❌ 錯誤：當前目錄不是 Git 倉庫！" -ForegroundColor Red
    Write-Host "請在 D:\3.Python 目錄下執行此腳本" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ 確認在 Git 倉庫中：$currentDir" -ForegroundColor Green
Write-Host ""

# ========== 1. 設定 GitHub Remote ==========
Write-Host "[步驟 1] 設定 GitHub Remote" -ForegroundColor Yellow
Write-Host ""

# 檢查是否已有 remote
$existingRemote = git remote -v
if ($existingRemote) {
    Write-Host "目前已有的 remote：" -ForegroundColor Cyan
    Write-Host $existingRemote
    Write-Host ""
    $addNew = Read-Host "是否要新增另一個 remote？(y/n)"
    if ($addNew -ne "y") {
        Write-Host "跳過 GitHub remote 設定" -ForegroundColor Yellow
    } else {
        $remoteName = Read-Host "請輸入 remote 名稱 (預設: github)"
        if ([string]::IsNullOrWhiteSpace($remoteName)) {
            $remoteName = "github"
        }
    }
} else {
    $remoteName = "origin"
}

if ($addNew -eq "y" -or -not $existingRemote) {
    if ([string]::IsNullOrWhiteSpace($GitHubRepoUrl)) {
        Write-Host "請提供 GitHub 倉庫 URL：" -ForegroundColor Cyan
        Write-Host "範例：https://github.com/你的帳號/你的倉庫名稱.git" -ForegroundColor Gray
        $GitHubRepoUrl = Read-Host "GitHub 倉庫 URL"
    }
    
    if (-not [string]::IsNullOrWhiteSpace($GitHubRepoUrl)) {
        try {
            git remote add $remoteName $GitHubRepoUrl
            Write-Host "✓ 已新增 GitHub remote: $remoteName -> $GitHubRepoUrl" -ForegroundColor Green
        } catch {
            Write-Host "❌ 新增 remote 失敗：$_" -ForegroundColor Red
        }
    } else {
        Write-Host "⚠ 跳過 GitHub remote 設定（未提供 URL）" -ForegroundColor Yellow
    }
}

Write-Host ""

# ========== 2. 尋找 Google Drive 資料夾 ==========
Write-Host "[步驟 2] 設定 Google Drive 同步" -ForegroundColor Yellow
Write-Host ""

$possiblePaths = @(
    "$env:USERPROFILE\Google Drive",
    "$env:USERPROFILE\Google 雲端硬碟",
    "D:\Google Drive",
    "C:\Google Drive"
)

$foundDrivePath = $null
foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $foundDrivePath = $path
        Write-Host "✓ 找到 Google Drive：$path" -ForegroundColor Green
        break
    }
}

if (-not $foundDrivePath) {
    Write-Host "⚠ 未找到 Google Drive 預設位置" -ForegroundColor Yellow
    if ([string]::IsNullOrWhiteSpace($GoogleDrivePath)) {
        $GoogleDrivePath = Read-Host "請手動輸入 Google Drive 同步資料夾的完整路徑"
    }
    if (-not [string]::IsNullOrWhiteSpace($GoogleDrivePath) -and (Test-Path $GoogleDrivePath)) {
        $foundDrivePath = $GoogleDrivePath
    }
}

if ($foundDrivePath) {
    $backupFolder = Join-Path $foundDrivePath "3.Python_Backup"
    Write-Host ""
    Write-Host "建議的備份位置：$backupFolder" -ForegroundColor Cyan
    $confirm = Read-Host "是否要複製資料夾到 Google Drive？(y/n)"
    
    if ($confirm -eq "y") {
        try {
            if (Test-Path $backupFolder) {
                $overwrite = Read-Host "資料夾已存在，是否覆蓋？(y/n)"
                if ($overwrite -eq "y") {
                    Remove-Item $backupFolder -Recurse -Force
                } else {
                    Write-Host "跳過複製" -ForegroundColor Yellow
                    $foundDrivePath = $null
                }
            }
            
            if ($foundDrivePath) {
                Write-Host "正在複製資料夾到 Google Drive..." -ForegroundColor Cyan
                Copy-Item -Path $currentDir -Destination $backupFolder -Recurse -Force
                Write-Host "✓ 已複製到：$backupFolder" -ForegroundColor Green
                Write-Host ""
                Write-Host "注意：Google Drive 會自動同步此資料夾" -ForegroundColor Yellow
                Write-Host "建議：定期手動更新此備份，或使用 GitHub 作為主要版本控制" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "❌ 複製失敗：$_" -ForegroundColor Red
        }
    } else {
        Write-Host "已跳過 Google Drive 複製" -ForegroundColor Yellow
        Write-Host "你可以稍後手動將資料夾複製到：$backupFolder" -ForegroundColor Gray
    }
} else {
    Write-Host "⚠ 無法找到 Google Drive 資料夾，請稍後手動設定" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "設定完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 顯示當前狀態
Write-Host "當前 Git Remote 設定：" -ForegroundColor Cyan
git remote -v
Write-Host ""

Write-Host "使用說明：" -ForegroundColor Cyan
Write-Host "1. 推送到 GitHub：git push origin master" -ForegroundColor Gray
Write-Host "2. Google Drive 會自動同步（如果已複製）" -ForegroundColor Gray
Write-Host "3. 查看詳細說明：cat GIT_SETUP_GUIDE.md" -ForegroundColor Gray

