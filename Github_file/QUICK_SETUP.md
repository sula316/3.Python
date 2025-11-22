# 快速設定指南 - GitHub + Google Drive 雙重備份

## 📋 已建立的檔案

1. **`backup_to_google_drive.bat`** - Google Drive 備份批次檔
2. **`setup_github.bat`** - GitHub Remote 設定批次檔
3. **`GIT_SETUP_GUIDE.md`** - 詳細設定指南
4. **`GOOGLE_DRIVE_BACKUP_INSTRUCTIONS.md`** - Google Drive 備份說明

## 🚀 快速開始

### 步驟 1：設定 GitHub（推薦先做）

1. **雙擊執行** `setup_github.bat`
2. 按照提示操作：
   - 如果已有 GitHub 倉庫，選擇選項 1 並輸入倉庫名稱
   - 如果還沒有，選擇選項 2，然後：
     - 前往 https://github.com/new 建立新倉庫
     - 輸入倉庫名稱（例如：`3.Python`）
     - 不要勾選「Initialize this repository with a README」
     - 建立完成後，回到批次檔輸入倉庫名稱
3. 批次檔會自動設定 remote 並推送程式碼

**你的 GitHub 帳號：** [sula316](https://github.com/sula316)

### 步驟 2：設定 Google Drive 備份

1. **確認 Google Drive 同步資料夾存在**
   - 路徑：`G:\我的雲端硬碟\3.Python_Backup`
   - 如果 `G:\我的雲端硬碟` 不存在，請先確認 Google Drive 是否已正確安裝

2. **雙擊執行** `backup_to_google_drive.bat`
3. 按照提示操作：
   - 如果目標資料夾已存在，會詢問是否覆蓋
   - 複製過程可能需要一些時間（視資料夾大小而定）

## 📝 日常使用

### 提交變更到 GitHub

```bash
cd D:\3.Python
git add .
git commit -m "你的提交訊息"
git push origin master
```

### 更新 Google Drive 備份

- **方法 1：** 雙擊執行 `backup_to_google_drive.bat`（會覆蓋舊備份）
- **方法 2：** 手動複製 `D:\3.Python` 到 `G:\我的雲端硬碟\3.Python_Backup`

## ⚠️ 注意事項

1. **GitHub 設定**
   - 首次推送可能需要登入 GitHub
   - 如果使用 HTTPS，可能需要設定 Personal Access Token
   - 建議使用 SSH 金鑰（更安全）

2. **Google Drive 備份**
   - `.git` 資料夾包含大量檔案，同步可能較慢
   - 多台電腦同時操作同一個 Git 倉庫可能會有衝突
   - 建議主要使用 GitHub，Google Drive 作為額外備份

3. **建議工作流程**
   - 主要版本控制：使用 GitHub
   - 額外備份：定期更新 Google Drive 備份
   - 本地開發：在 `D:\3.Python` 進行

## 🔍 檢查設定狀態

```bash
# 檢查 GitHub remote
git remote -v

# 檢查 Git 狀態
git status

# 查看提交歷史
git log --oneline -10
```

## 🆘 遇到問題？

1. **GitHub 推送失敗**
   - 檢查是否已登入：`git config --global user.name` 和 `git config --global user.email`
   - 檢查 remote 設定：`git remote -v`
   - 確認倉庫存在且有權限

2. **Google Drive 備份失敗**
   - 確認 `G:\我的雲端硬碟` 資料夾存在
   - 確認 Google Drive 桌面應用程式正在運行
   - 檢查磁碟空間是否足夠

3. **批次檔無法執行**
   - 確認檔案路徑沒有中文編碼問題
   - 嘗試以系統管理員身份執行
   - 檢查防毒軟體是否阻擋

## 📚 相關文件

- `GIT_SETUP_GUIDE.md` - 詳細的 Git 設定說明
- `GOOGLE_DRIVE_BACKUP_INSTRUCTIONS.md` - Google Drive 備份詳細說明

