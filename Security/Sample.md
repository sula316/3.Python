# Security Toolkit Samples 安全工具示例

以下範例遵循 `Read_First` 目錄中的套件使用與編碼原則，每段皆有中文說明，方便快速對照。

## psutil（系統資源監控）
- **用途 Purpose**：監控程序、CPU、記憶體、磁碟與網路狀況，可立即找出可疑的 `node.exe` 行程。
- **範例 Sample**：
```python
import psutil

# 逐一檢查所有程序，若發現 node.exe 則列印 PID（協助定位可疑行程）
for proc in psutil.process_iter(['pid', 'name']):
    if proc.info['name'] == 'node.exe':
        print('Found suspicious node.exe with PID', proc.info['pid'])
```

## pywin32（Windows API 操作）
- **用途 Purpose**：透過 Python 呼叫 Windows API，讀取事件檔或控制服務，可追蹤系統層級異常。
- **範例 Sample**：
```python
import win32evtlog

# 開啟 System 事件檔並顯示紀錄總數，便於確認是否有異常事件暴增
handle = win32evtlog.OpenEventLog(None, 'System')
print('Event record count:', win32evtlog.GetNumberOfEventLogRecords(handle))
```

## wmi（系統管理查詢）
- **用途 Purpose**：利用 WMI 取得排程工作、服務與硬體資訊，檢查是否有惡意排程復活。
- **範例 Sample**：
```python
import wmi

# 列出所有排程工作，找出名稱可疑或非預期啟用的項目
c = wmi.WMI()
for task in c.Win32_ScheduledJob():
    print('Scheduled job:', task.Name)
```

## watchdog（檔案系統監控）
- **用途 Purpose**：即時監控特定資料夾（如 System32），一旦出現新檔案立即通知。
- **範例 Sample**：
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class Alert(FileSystemEventHandler):
    """偵測新檔案並輸出中文提示。"""
    def on_created(self, event):
        print('偵測到新增檔案:', event.src_path)


observer = Observer()
observer.schedule(Alert(), path='C:/Windows/System32', recursive=False)
observer.start()
```

## yara-python（惡意特徵比對）
- **用途 Purpose**：撰寫 YARA 規則比對檔案，快速找出含有特定字串或特徵的惡意程式。
- **範例 Sample**：
```python
import yara

# 定義簡單規則：若檔案中出現字串 node.exe，則回報
rule = yara.compile(source='''
rule IntelTask {
    strings: $a = "node.exe"
    condition: $a
}
''')

print(rule.match('C:/Windows/System32/IntelSoftwareAgentTask/app.js'))
```

## pefile（PE 結構分析）
- **用途 Purpose**：解析可疑的 exe/dll，檢查 EntryPoint、匯入表等資訊，確認是否遭篡改。
- **範例 Sample**：
```python
import pefile

# 讀取可疑的 node.exe，輸出進入點位址以供後續比對
pe = pefile.PE('C:/Windows/System32/IntelSoftwareAgentTask/node.exe')
print('EntryPoint:', hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint))
```

## scapy（封包擷取與分析）
- **用途 Purpose**：擷取或自行產生封包，檢查是否有異常連線對外傳送資料。
- **範例 Sample**：
```python
from scapy.all import sniff

# 擷取 5 個 TCP/80 封包並列出摘要，觀察可疑 HTTP 連線
sniff(filter='tcp port 80', prn=lambda pkt: print(pkt.summary()), count=5)
```

## pyshark（tshark Python 介面）
- **用途 Purpose**：以 Python 操控 tshark，取得更高階的封包屬性，適合長時間監控。
- **範例 Sample**：
```python
import pyshark

# 直播擷取 3 筆封包並顯示來源與目的 IP，方便判斷是否外洩
cap = pyshark.LiveCapture(interface='Ethernet')
cap.sniff(packet_count=3)
for pkt in cap:
    print('Layer:', pkt.highest_layer, '|', pkt.ip.src, '->', pkt.ip.dst)
```

---

## 雲端硬碟監控範例

### 使用 watchdog 監控雲端硬碟同步資料夾
- **用途 Purpose**：即時監控 OneDrive、Google Drive 等雲端硬碟資料夾，一旦出現可疑檔案立即通知。
- **範例 Sample**：
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import os

class CloudDriveMonitor(FileSystemEventHandler):
    """監控雲端硬碟中的可疑檔案。"""
    
    # 定義可疑檔案名稱模式
    SUSPECT_PATTERNS = ['node.exe', 'IntelSoftwareAgentTask', 'app.js', 'build.zip']
    
    def on_created(self, event):
        """當新檔案或資料夾被建立時觸發。"""
        if event.is_directory:
            return
        
        file_name = Path(event.src_path).name.lower()
        # 檢查是否匹配可疑模式
        if any(pattern.lower() in file_name for pattern in self.SUSPECT_PATTERNS):
            print(f'⚠️  警告：在雲端硬碟中發現可疑檔案: {event.src_path}')
            # 這裡可以加入自動刪除或通知邏輯

# 自動偵測雲端硬碟路徑
def find_cloud_drives():
    """找出所有雲端硬碟同步資料夾。"""
    user_home = Path.home()
    cloud_drives = []
    
    # 常見的雲端硬碟名稱
    drive_names = ['OneDrive', 'Google Drive', 'GoogleDrive', 'Dropbox']
    for name in drive_names:
        path = user_home / name
        if path.exists():
            cloud_drives.append(path)
    
    return cloud_drives

# 開始監控
observer = Observer()
monitor = CloudDriveMonitor()

for cloud_path in find_cloud_drives():
    print(f'開始監控: {cloud_path}')
    observer.schedule(monitor, str(cloud_path), recursive=True)

observer.start()
print('雲端硬碟監控已啟動，按 Ctrl+C 停止...')

try:
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
    print('監控已停止')
observer.join()
```

### 使用 psutil 檢查雲端硬碟中的可疑程序
- **用途 Purpose**：檢查是否有程序從雲端硬碟路徑執行，這可能是惡意程式透過同步傳播。
- **範例 Sample**：
```python
import psutil
from pathlib import Path

def check_processes_in_cloud_drives():
    """檢查是否有程序從雲端硬碟路徑執行。"""
    user_home = Path.home()
    cloud_paths = [
        user_home / 'OneDrive',
        user_home / 'Google Drive',
        user_home / 'Dropbox',
    ]
    
    suspicious_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            exe_path = proc.info.get('exe')
            if exe_path:
                exe_path_obj = Path(exe_path)
                # 檢查是否在雲端硬碟路徑中
                for cloud_path in cloud_paths:
                    if cloud_path.exists() and cloud_path in exe_path_obj.parents:
                        suspicious_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'path': exe_path
                        })
                        print(f'⚠️  發現從雲端硬碟執行的程序: {exe_path}')
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return suspicious_processes

# 執行檢查
suspicious = check_processes_in_cloud_drives()
if suspicious:
    print(f'共發現 {len(suspicious)} 個可疑程序')
else:
    print('✓ 未發現從雲端硬碟執行的可疑程序')
```

### 批次掃描雲端硬碟中的可疑檔案
- **用途 Purpose**：一次性掃描所有雲端硬碟資料夾，找出所有可疑檔案並列出清單。
- **範例 Sample**：
```python
from pathlib import Path
import os

def scan_cloud_drive_for_suspect_files(cloud_path, max_depth=3):
    """遞迴掃描雲端硬碟，找出可疑檔案。
    
    Args:
        cloud_path: 雲端硬碟根目錄
        max_depth: 最大掃描深度
    """
    suspect_patterns = ['node.exe', 'IntelSoftwareAgentTask', 'app.js', 'build.zip']
    found_files = []
    
    def _scan(current_path, depth):
        if depth > max_depth:
            return
        
        try:
            for item in current_path.iterdir():
                item_name_lower = item.name.lower()
                # 檢查是否匹配可疑模式
                if any(pattern.lower() in item_name_lower for pattern in suspect_patterns):
                    found_files.append(item)
                    print(f'⚠️  發現可疑檔案: {item}')
                
                # 繼續掃描子資料夾
                if item.is_dir() and depth < max_depth:
                    if not item.name.startswith('.'):
                        _scan(item, depth + 1)
        except PermissionError:
            print(f'權限不足，無法存取: {current_path}')
        except Exception as e:
            print(f'掃描錯誤 {current_path}: {e}')
    
    _scan(cloud_path, 0)
    return found_files

# 掃描所有雲端硬碟
user_home = Path.home()
cloud_drives = [
    user_home / 'OneDrive',
    user_home / 'Google Drive',
    user_home / 'Dropbox',
]

all_suspect_files = []
for cloud_path in cloud_drives:
    if cloud_path.exists():
        print(f'掃描: {cloud_path}')
        found = scan_cloud_drive_for_suspect_files(cloud_path)
        all_suspect_files.extend(found)

if all_suspect_files:
    print(f'\n共發現 {len(all_suspect_files)} 個可疑檔案')
    for f in all_suspect_files:
        print(f'  - {f}')
else:
    print('\n✓ 未發現可疑檔案')
```

---

## Python 套件安全檢查

### 供應鏈攻擊風險說明
- **風險說明**：Python 套件本身確實可能包含病毒或惡意程式碼，這稱為「供應鏈攻擊」（Supply Chain Attack）
- **常見攻擊方式**：
  - **Typosquatting**：使用類似名稱的套件（如 `requets` 偽裝成 `requests`）
  - **惡意注入**：在合法套件中注入惡意程式碼
  - **後門程式**：套件包含隱藏的後門或資料外洩功能
  - **依賴劫持**：攻擊套件的依賴項

### 使用 package_security_check.py 檢查套件
- **用途 Purpose**：全面檢查已安裝的 Python 套件是否安全
- **功能 Features**：
  - 檢查套件來源（是否來自可信的 PyPI）
  - 掃描套件檔案中的可疑程式碼模式
  - 偵測 typosquatting（名稱相似的惡意套件）
  - 檢查是否有可疑的網路連線或檔案操作
- **使用方式**：
```bash
# 執行套件安全檢查
python Security/package_security_check.py
```

### 手動檢查套件安全性
- **用途 Purpose**：手動檢查特定套件的詳細資訊
- **範例 Sample**：
```python
import subprocess
import json
import sys

def check_package_info(package_name):
    """檢查套件的詳細資訊。"""
    # 取得套件資訊
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", package_name],
        capture_output=True,
        text=True,
        check=False
    )
    
    if result.returncode == 0:
        print(f"套件資訊 ({package_name}):")
        print(result.stdout)
    else:
        print(f"無法取得 {package_name} 的資訊")
    
    # 檢查套件來源
    pip_list = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--format=json"],
        capture_output=True,
        text=True,
        check=False
    )
    
    if pip_list.returncode == 0:
        packages = json.loads(pip_list.stdout)
        for pkg in packages:
            if pkg["name"].lower() == package_name.lower():
                print(f"\n套件來源: {pkg.get('location', 'unknown')}")

# 檢查特定套件
check_package_info("requests")
```

### 檢查套件檔案中的可疑程式碼
- **用途 Purpose**：掃描套件檔案，找出可疑的程式碼模式
- **範例 Sample**：
```python
import importlib.metadata
from pathlib import Path
import re

def scan_package_for_suspect_code(package_name):
    """掃描套件檔案中的可疑程式碼。"""
    # 可疑模式
    suspect_patterns = [
        r"eval\s*\(",
        r"exec\s*\(",
        r"__import__\s*\(",
        r"subprocess\.",
        r"os\.system\s*\(",
        r"urllib\.request\.urlopen",
        r"requests\.(get|post)\s*\(",
    ]
    
    try:
        # 取得套件位置
        dist = importlib.metadata.distribution(package_name)
        package_path = Path(dist.locate_file(""))
        
        print(f"掃描套件: {package_name}")
        print(f"位置: {package_path}")
        
        suspicious_files = []
        
        # 掃描所有 Python 檔案
        for py_file in package_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                
                for pattern in suspect_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        relative_path = py_file.relative_to(package_path)
                        suspicious_files.append((str(relative_path), pattern))
            except Exception as e:
                print(f"無法讀取 {py_file}: {e}")
        
        if suspicious_files:
            print(f"\n⚠️  發現 {len(suspicious_files)} 個可疑檔案:")
            for file_path, pattern in suspicious_files[:10]:  # 只顯示前 10 個
                print(f"  - {file_path}: {pattern}")
        else:
            print("✓ 未發現可疑程式碼")
            
    except Exception as e:
        print(f"檢查套件時發生錯誤: {e}")

# 檢查特定套件
scan_package_for_suspect_code("requests")
```

### 檢查套件是否來自可信來源
- **用途 Purpose**：確認套件是從官方 PyPI 安裝，而非可疑來源
- **範例 Sample**：
```python
import subprocess
import sys
import json

def verify_package_source(package_name):
    """驗證套件是否來自可信來源。"""
    # 取得套件資訊
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", package_name],
        capture_output=True,
        text=True,
        check=False
    )
    
    if result.returncode != 0:
        print(f"無法取得 {package_name} 的資訊")
        return False
    
    # 檢查安裝位置
    location = None
    for line in result.stdout.splitlines():
        if line.startswith("Location:"):
            location = line.split(":", 1)[1].strip()
            break
    
    # 檢查是否在標準位置（site-packages）
    if location and "site-packages" in location:
        print(f"✓ {package_name} 安裝在標準位置: {location}")
        
        # 檢查是否從 PyPI 安裝
        pip_list = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if pip_list.returncode == 0:
            packages = json.loads(pip_list.stdout)
            for pkg in packages:
                if pkg["name"].lower() == package_name.lower():
                    print(f"✓ 套件版本: {pkg.get('version', 'unknown')}")
                    return True
    else:
        print(f"⚠️  {package_name} 安裝在非標準位置: {location}")
        return False
    
    return False

# 驗證套件來源
verify_package_source("numpy")
```

### 防範套件攻擊的最佳實踐
- **建議 Practices**：
  1. **只從官方 PyPI 安裝**：避免使用 `--index-url` 指向不明來源
  2. **檢查套件名稱**：安裝前確認套件名稱拼寫正確
  3. **查看套件資訊**：使用 `pip show <package>` 查看套件詳細資訊
  4. **檢查下載量**：在 PyPI 上查看套件的下載統計
  5. **查看原始碼**：檢查套件的 GitHub 或官方網站
  6. **定期更新**：保持套件為最新版本
  7. **使用虛擬環境**：隔離不同專案的套件
  8. **定期掃描**：使用 `package_security_check.py` 定期檢查

### 發現可疑套件時的處理步驟
- **處理流程**：
  1. **立即停止使用**：停止執行使用該套件的程式
  2. **備份證據**：保留套件檔案和檢查日誌
  3. **檢查影響範圍**：確認哪些系統或資料可能受影響
  4. **移除套件**：使用 `pip uninstall <package_name>` 移除
  5. **檢查系統**：執行完整的系統掃描
  6. **更換憑證**：如果可能，更換相關的 API 金鑰或密碼
  7. **回報問題**：向 PyPI 或相關安全組織回報

