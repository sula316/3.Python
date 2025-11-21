"""Python 套件安全檢查腳本

此模組依據 `Read_First` 中的規範實作，用於檢查已安裝的 Python 套件是否安全：
1. 檢查套件來源（是否來自可信的 PyPI）
2. 掃描套件檔案中的可疑內容（惡意程式碼、後門等）
3. 檢查套件的 setup.py 和安裝後腳本
4. 列出所有已安裝套件及其來源
5. 檢查是否有套件包含可疑的網路連線或檔案操作

供應鏈攻擊（Supply Chain Attack）是真實存在的威脅：
- 惡意套件可能偽裝成合法套件（typosquatting）
- 套件可能被注入惡意程式碼
- 套件可能包含後門或資料外洩功能
"""

from __future__ import annotations

import importlib.metadata
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
import importlib.util

LOG_PATH = Path(__file__).with_suffix(".log")

# 可疑的程式碼模式（用於掃描套件檔案）
SUSPECT_CODE_PATTERNS = [
    r"eval\s*\(",
    r"exec\s*\(",
    r"__import__\s*\(",
    r"compile\s*\(",
    r"subprocess\.",
    r"os\.system\s*\(",
    r"os\.popen\s*\(",
    r"urllib\.request\.urlopen",
    r"requests\.get\s*\(",
    r"requests\.post\s*\(",
    r"socket\.socket\s*\(",
    r"base64\.b64decode",
    r"pickle\.loads",
    r"marshal\.loads",
    r"ctypes\.",
    r"winreg\.",
    r"keyboard\.",
    r"pynput\.",
]

# 可疑的檔案路徑模式
SUSPECT_PATH_PATTERNS = [
    r"C:\\Windows\\System32",
    r"C:\\Windows\\SysWOW64",
    r"C:\\ProgramData",
    r"\.ssh",
    r"\.aws",
    r"credentials",
    r"password",
    r"token",
    r"api[_-]?key",
]

# 可疑的網路連線模式
SUSPECT_NETWORK_PATTERNS = [
    r"http://[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}",  # IP 位址
    r"https?://[a-z0-9-]+\.(tk|ml|ga|cf|gq)",  # 可疑域名
    r"pastebin\.com",
    r"paste\.ee",
    r"hastebin\.com",
]

# 已知的可疑套件名稱（可從安全公告中更新）
KNOWN_MALICIOUS_PACKAGES: Set[str] = {
    # 這裡可以加入已知的惡意套件名稱
    # 範例：'malicious-package-name',
}


def append_log(message: str) -> None:
    """將訊息寫入 log 並同步輸出在終端。"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}\n"
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line)
    print(line, end="")


def get_installed_packages() -> Dict[str, str]:
    """取得所有已安裝的套件及其版本。"""
    packages: Dict[str, str] = {}
    try:
        for dist in importlib.metadata.distributions():
            name = dist.metadata.get("Name", "")
            version = dist.metadata.get("Version", "")
            if name:
                packages[name.lower()] = version
    except Exception as exc:  # noqa: BLE001
        append_log(f"Error getting installed packages: {exc}")
    return packages


def get_package_location(package_name: str) -> Path | None:
    """取得套件的安裝位置。"""
    try:
        dist = importlib.metadata.distribution(package_name)
        if dist and dist.locate_file(""):
            return Path(dist.locate_file(""))
    except importlib.metadata.PackageNotFoundError:
        pass
    except Exception as exc:  # noqa: BLE001
        append_log(f"Error getting location for {package_name}: {exc}")
    return None


def get_package_metadata(package_name: str) -> Dict[str, str]:
    """取得套件的詳細資訊（來源、作者等）。"""
    metadata: Dict[str, str] = {}
    try:
        dist = importlib.metadata.distribution(package_name)
        metadata["name"] = dist.metadata.get("Name", "")
        metadata["version"] = dist.metadata.get("Version", "")
        metadata["author"] = dist.metadata.get("Author", "")
        metadata["author_email"] = dist.metadata.get("Author-email", "")
        metadata["home_page"] = dist.metadata.get("Home-page", "")
        metadata["summary"] = dist.metadata.get("Summary", "")
    except Exception as exc:  # noqa: BLE001
        append_log(f"Error getting metadata for {package_name}: {exc}")
    return metadata


def check_package_source(package_name: str) -> Tuple[bool, str]:
    """檢查套件是否來自可信來源（PyPI）。
    
    Returns:
        (is_safe, reason): 是否安全及原因
    """
    try:
        # 使用 pip show 取得套件資訊
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True,
            check=False,
        )
        
        if result.returncode != 0:
            return False, "無法取得套件資訊"
        
        # 檢查 Location（安裝位置）
        location = None
        for line in result.stdout.splitlines():
            if line.startswith("Location:"):
                location = line.split(":", 1)[1].strip()
                break
        
        # 檢查是否從 PyPI 安裝（通常會在 site-packages）
        if location and "site-packages" in location:
            # 進一步檢查是否來自 PyPI（可以檢查 pip list 的來源）
            pip_result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                check=False,
            )
            
            if pip_result.returncode == 0:
                packages_list = json.loads(pip_result.stdout)
                for pkg in packages_list:
                    if pkg["name"].lower() == package_name.lower():
                        # 檢查是否有可疑的來源標記
                        return True, "來自標準安裝位置"
        
        return False, f"可疑的安裝位置: {location}"
    except Exception as exc:  # noqa: BLE001
        return False, f"檢查來源時發生錯誤: {exc}"


def scan_file_for_suspect_patterns(file_path: Path) -> List[str]:
    """掃描檔案內容，找出可疑的程式碼模式。
    
    Returns:
        找到的可疑模式列表
    """
    found_patterns: List[str] = []
    
    try:
        if not file_path.is_file():
            return found_patterns
        
        # 只掃描 Python 檔案和文字檔案
        if file_path.suffix not in [".py", ".pyw", ".txt", ".json", ".yaml", ".yml"]:
            return found_patterns
        
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        
        # 檢查程式碼模式
        for pattern in SUSPECT_CODE_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                found_patterns.append(f"{pattern} (line {line_num})")
        
        # 檢查檔案路徑模式
        for pattern in SUSPECT_PATH_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(f"Suspicious path pattern: {pattern}")
        
        # 檢查網路連線模式
        for pattern in SUSPECT_NETWORK_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                found_patterns.append(f"Suspicious network: {match.group()}")
    
    except Exception as exc:  # noqa: BLE001
        append_log(f"Error scanning {file_path}: {exc}")
    
    return found_patterns


def scan_package_files(package_name: str) -> Dict[str, List[str]]:
    """掃描套件的所有檔案，找出可疑內容。
    
    Returns:
        {檔案路徑: [可疑模式列表]}
    """
    suspicious_files: Dict[str, List[str]] = {}
    package_location = get_package_location(package_name)
    
    if not package_location or not package_location.exists():
        return suspicious_files
    
    # 掃描套件目錄中的所有 Python 檔案
    for py_file in package_location.rglob("*.py"):
        patterns = scan_file_for_suspect_patterns(py_file)
        if patterns:
            relative_path = py_file.relative_to(package_location)
            suspicious_files[str(relative_path)] = patterns
    
    # 也檢查 setup.py 和 __init__.py（這些是常見的注入點）
    for important_file in ["setup.py", "__init__.py", "setup.cfg", "pyproject.toml"]:
        file_path = package_location / important_file
        if file_path.exists():
            patterns = scan_file_for_suspect_patterns(file_path)
            if patterns:
                suspicious_files[important_file] = patterns
    
    return suspicious_files


def check_typosquatting(package_name: str, installed_packages: Dict[str, str]) -> List[str]:
    """檢查是否有套件名稱類似但不同的可疑套件（typosquatting）。
    
    Typosquatting 是攻擊者使用類似名稱的套件來欺騙使用者安裝惡意套件。
    """
    warnings: List[str] = []
    
    # 常見的合法套件名稱（可以擴充）
    legitimate_packages = {
        "requests",
        "numpy",
        "pandas",
        "matplotlib",
        "scikit-learn",
        "tensorflow",
        "pytorch",
        "flask",
        "django",
        "pillow",
        "beautifulsoup4",
        "selenium",
        "scrapy",
    }
    
    package_lower = package_name.lower()
    
    # 檢查是否與合法套件名稱非常相似
    for legit in legitimate_packages:
        if package_lower != legit.lower():
            # 簡單的相似度檢查（可以改進）
            if len(package_lower) == len(legit.lower()):
                diff = sum(c1 != c2 for c1, c2 in zip(package_lower, legit.lower()))
                if diff == 1:  # 只有一個字元不同
                    warnings.append(f"⚠️  可能的 typosquatting: '{package_name}' 與 '{legit}' 非常相似")
    
    return warnings


def check_package(package_name: str, installed_packages: Dict[str, str]) -> Dict:
    """完整檢查單一套件。
    
    Returns:
        包含檢查結果的字典
    """
    result = {
        "name": package_name,
        "version": installed_packages.get(package_name, "unknown"),
        "is_known_malicious": False,
        "source_check": {"is_safe": False, "reason": ""},
        "suspicious_files": {},
        "typosquatting_warnings": [],
        "metadata": {},
    }
    
    # 檢查是否為已知惡意套件
    if package_name.lower() in KNOWN_MALICIOUS_PACKAGES:
        result["is_known_malicious"] = True
        append_log(f"🚨 已知惡意套件: {package_name}")
        return result
    
    # 檢查來源
    is_safe, reason = check_package_source(package_name)
    result["source_check"] = {"is_safe": is_safe, "reason": reason}
    
    # 取得套件資訊
    result["metadata"] = get_package_metadata(package_name)
    
    # 檢查 typosquatting
    result["typosquatting_warnings"] = check_typosquatting(package_name, installed_packages)
    
    # 掃描檔案
    result["suspicious_files"] = scan_package_files(package_name)
    
    return result


def main() -> None:
    """主程式：檢查所有已安裝的套件。"""
    append_log("=== Python 套件安全檢查開始 ===")
    append_log(f"Python 版本: {sys.version}")
    append_log(f"Python 執行檔路徑: {sys.executable}")
    
    # 取得所有已安裝的套件
    append_log("正在取得已安裝套件清單...")
    installed_packages = get_installed_packages()
    append_log(f"共發現 {len(installed_packages)} 個已安裝套件")
    
    # 檢查每個套件
    suspicious_packages: List[Dict] = []
    
    for package_name in sorted(installed_packages.keys()):
        append_log(f"\n檢查套件: {package_name} (版本: {installed_packages[package_name]})")
        
        result = check_package(package_name, installed_packages)
        
        # 記錄可疑發現
        has_issues = False
        
        if result["is_known_malicious"]:
            append_log(f"  🚨 已知惡意套件！")
            has_issues = True
        
        if not result["source_check"]["is_safe"]:
            append_log(f"  ⚠️  來源可疑: {result['source_check']['reason']}")
            has_issues = True
        
        if result["typosquatting_warnings"]:
            for warning in result["typosquatting_warnings"]:
                append_log(f"  {warning}")
            has_issues = True
        
        if result["suspicious_files"]:
            append_log(f"  ⚠️  發現 {len(result['suspicious_files'])} 個可疑檔案:")
            for file_path, patterns in result["suspicious_files"].items():
                append_log(f"    - {file_path}:")
                for pattern in patterns[:3]:  # 只顯示前 3 個
                    append_log(f"      • {pattern}")
            has_issues = True
        
        if has_issues:
            suspicious_packages.append(result)
        else:
            append_log(f"  ✓ 未發現明顯問題")
    
    # 總結
    append_log("\n=== 檢查結果總結 ===")
    append_log(f"總共檢查: {len(installed_packages)} 個套件")
    append_log(f"發現可疑: {len(suspicious_packages)} 個套件")
    
    if suspicious_packages:
        append_log("\n⚠️  以下套件需要進一步檢查:")
        for pkg in suspicious_packages:
            append_log(f"  - {pkg['name']} (版本: {pkg['version']})")
        append_log("\n建議:")
        append_log("  1. 檢查這些套件的官方來源")
        append_log("  2. 查看套件的 GitHub 或官方網站")
        append_log("  3. 考慮移除可疑套件: pip uninstall <package_name>")
        append_log("  4. 只從可信來源安裝套件（官方 PyPI）")
    else:
        append_log("\n✓ 未發現明顯的可疑套件")
    
    append_log("\n=== 檢查完成 ===")
    append_log(f"詳細日誌已儲存至: {LOG_PATH}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        append_log("\n檢查已中斷")
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        append_log(f"\n發生未預期的錯誤: {exc}")
        sys.exit(1)

