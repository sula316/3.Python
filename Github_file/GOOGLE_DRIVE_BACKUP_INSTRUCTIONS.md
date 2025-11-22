# Google Drive 備份設定說明

## 目標路徑
`G:\我的雲端硬碟\3.Python_Backup`

## 設定步驟

### 方法 1：使用 Windows 檔案總管（最簡單）

1. 開啟檔案總管
2. 確認 `G:\我的雲端硬碟` 資料夾存在（如果不存在，請先確認 Google Drive 是否已正確安裝並同步）
3. 在 `G:\我的雲端硬碟` 中建立資料夾 `3.Python_Backup`（如果還沒有）
4. 將整個 `D:\3.Python` 資料夾複製到 `G:\我的雲端硬碟\3.Python_Backup`

### 方法 2：使用 PowerShell 命令

在 PowerShell 中執行以下命令：

```powershell
# 設定路徑
$source = "D:\3.Python"
$target = "G:\我的雲端硬碟\3.Python_Backup"

# 建立目標資料夾（如果不存在）
$parentPath = Split-Path $target -Parent
if (-not (Test-Path $parentPath)) {
    New-Item -ItemType Directory -Path $parentPath -Force
}
if (-not (Test-Path $target)) {
    New-Item -ItemType Directory -Path $target -Force
}

# 使用 robocopy 複製（推薦，支援中文路徑）
robocopy "$source" "$target" /E /COPYALL /R:3 /W:5
```

### 方法 3：使用 robocopy 命令（命令提示字元）

在命令提示字元（cmd）中執行：

```cmd
robocopy "D:\3.Python" "G:\我的雲端硬碟\3.Python_Backup" /E /COPYALL /R:3 /W:5
```

## 注意事項

⚠️ **重要提醒：**
- 確保 Google Drive 桌面應用程式已安裝並正在運行
- 確保 `G:\我的雲端硬碟` 資料夾存在且可以存取
- 如果資料夾很大，複製可能需要一些時間
- Google Drive 會自動同步此資料夾到雲端
- 建議定期更新備份，或使用 GitHub 作為主要版本控制

## 驗證備份

複製完成後，檢查：
1. `G:\我的雲端硬碟\3.Python_Backup` 資料夾是否存在
2. 資料夾中是否有 `.git` 資料夾（確認 Git 倉庫也被複製）
3. Google Drive 圖示是否顯示同步中或已完成

## 更新備份

如果需要更新備份，可以：
1. 刪除舊的 `3.Python_Backup` 資料夾
2. 重新複製 `D:\3.Python` 到該位置

或者使用 robocopy 的 `/MIR` 參數來鏡像同步（**注意：這會刪除目標中不存在的檔案**）：

```powershell
robocopy "D:\3.Python" "G:\我的雲端硬碟\3.Python_Backup" /MIR /R:3 /W:5
```

