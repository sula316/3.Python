# Git 設定指南 - GitHub + Google Drive 雙重備份

## 目前狀態
- ✅ Git 倉庫已初始化
- ✅ 所有變更已提交
- ⏳ 等待設定 GitHub remote
- ⏳ 等待設定 Google Drive 同步

## 設定步驟

### 1. 設定 GitHub Remote

#### 方法 A：在 GitHub 建立新倉庫後設定
```bash
# 在 GitHub 建立新倉庫後，執行：
cd D:\3.Python
git remote add origin https://github.com/你的帳號/你的倉庫名稱.git
git branch -M main  # 如果需要改分支名稱為 main
git push -u origin master  # 或 main
```

#### 方法 B：使用現有 GitHub 倉庫
```bash
cd D:\3.Python
git remote add origin https://github.com/你的帳號/你的倉庫名稱.git
git push -u origin master
```

### 2. 設定 Google Drive 同步

#### 選項 A：複製整個資料夾到 Google Drive
1. 找到你的 Google Drive 同步資料夾位置（通常在 `C:\Users\你的帳號\Google Drive` 或 `D:\Google Drive`）
2. 在 Google Drive 中建立一個資料夾，例如：`3.Python_Backup`
3. 將 `D:\3.Python` 整個資料夾複製到 Google Drive 的資料夾中

#### 選項 B：使用符號連結（進階）
```powershell
# 以系統管理員身份執行 PowerShell
# 在 Google Drive 建立資料夾後，建立符號連結
New-Item -ItemType SymbolicLink -Path "D:\Google Drive\3.Python" -Target "D:\3.Python"
```

### 3. 日常使用流程

#### 提交變更到 GitHub
```bash
cd D:\3.Python
git add .
git commit -m "你的提交訊息"
git push origin master
```

#### Google Drive 會自動同步（如果使用選項 A）
- 如果資料夾在 Google Drive 同步資料夾中，會自動同步
- 如果只是複製備份，需要手動更新

## 注意事項

⚠️ **重要提醒：**
- Google Drive 同步 `.git` 資料夾可能會較慢（檔案很多）
- 多台電腦同時操作同一個 Git 倉庫可能會有衝突
- 建議主要使用 GitHub，Google Drive 作為額外備份

## 檢查設定狀態

```bash
# 檢查 remote 設定
git remote -v

# 檢查分支狀態
git status

# 查看提交歷史
git log --oneline -10
```

