import pandas as pd
import os
import re
from datetime import datetime

# Selenium 相關導入
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# --- 1. 股票數據爬蟲函數 ---
def fetch_stock_list_from_goodinfo(url, base_download_path, headless=False):
    """
    使用 Selenium 爬取 Goodinfo! 股票列表頁面，提取股票數據並返回 DataFrame。

    Args:
        url (str): 目標 Goodinfo! 頁面的 URL。
        base_download_path (str): 檔案下載和儲存的基礎路徑 (用於 debug 檔案)。
        headless (bool): 是否使用無頭模式 (不顯示瀏覽器視窗)。預設為 False。

    Returns:
        pd.DataFrame: 包含股票數據的 DataFrame，如果失敗則返回 None。
    """
    # 確保下載路徑存在，如果不存在則創建
    if not os.path.exists(base_download_path):
        os.makedirs(base_download_path)
        print(f"已創建資料夾: {base_download_path}")

    # 設定 Firefox 選項
    options = Options()
    if headless:
        options.add_argument("--headless")
    
    options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0")
    
    # 指定 Firefox 瀏覽器執行檔路徑 (請務必確認此路徑與您的電腦一致)
    FIREFOX_BINARY_LOCATION = r"C:\Program Files\Mozilla Firefox\firefox.exe" 
    
    if not os.path.exists(FIREFOX_BINARY_LOCATION):
        print(f"錯誤：找不到 Firefox 瀏覽器執行檔在 '{FIREFOX_BINARY_LOCATION}'。")
        print("請確認 Firefox 瀏覽器已安裝在上述路徑。")
        return None
    options.binary_location = FIREFOX_BINARY_LOCATION 

    # 指定 GeckoDriver 路徑 (請務必確認 geckodriver.exe 放在與此腳本相同的目錄)
    GECKO_DRIVER_PATH = "geckodriver.exe" 
    
    if not os.path.exists(GECKO_DRIVER_PATH):
        print(f"錯誤：找不到 GeckoDriver 執行檔在 '{GECKO_DRIVER_PATH}'。")
        print("請確認您已下載與您 Firefox 瀏覽器版本兼容的 64 位元 GeckoDriver，並將其放置在與此程式碼相同的資料夾中。")
        return None

    service = Service(GECKO_DRIVER_PATH) 

    driver = None
    df = None # 初始化 df

    try:
        print(f"正在啟動 Firefox 瀏覽器 (無頭模式: {headless})...")
        driver = webdriver.Firefox(service=service, options=options) 

        if not headless: 
            driver.set_window_size(1920, 1080)

        print(f"正在前往網站: {url}")
        driver.get(url)

        print("等待股票列表表格載入中...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "tblStockList")) 
        )
        print("表格已載入！")

        stock_table_element = driver.find_element(By.ID, "tblStockList")
        table_outer_html = stock_table_element.get_attribute('outerHTML')

        debug_table_html_path = os.path.join(base_download_path, "debug_tblStockList_content_週KD金叉.html") # 更改 debug 檔名
        with open(debug_table_html_path, "w", encoding="utf-8") as f:
            f.write(table_outer_html)
        print(f"已將 'tblStockList' 表格的完整 HTML 內容儲存到：{debug_table_html_path}")

        soup = BeautifulSoup(table_outer_html, 'html.parser')

        # 表頭提取邏輯
        headers = []
        header_row = soup.find('tr', class_='bg_h2 fw_bold') 
        if header_row:
            for th in header_row.find_all('th'):
                nobr_tag = th.find('nobr')
                if nobr_tag:
                    headers.append(nobr_tag.get_text(strip=True).replace('\n', ''))
                else:
                    headers.append(th.get_text(strip=True).replace('\n', ''))
        
        if not headers:
            print("警告：未能成功提取表頭。DataFrame 將使用預設數值欄位名。")

        # 數據行提取邏輯
        processed_data_rows = []
        data_rows_elements = soup.find_all('tr', id=re.compile(r'row\d+')) 
        
        for row in data_rows_elements:
            row_data = []
            for cell in row.find_all(['th', 'td']):
                nobr_tag = cell.find('nobr')
                if nobr_tag:
                    row_data.append(nobr_tag.get_text(strip=True).replace('\n', ''))
                else:
                    row_data.append(cell.get_text(strip=True).replace('\n', ''))
            
            if row_data and row_data[0].strip():
                 processed_data_rows.append(row_data)

        if headers and processed_data_rows and len(headers) == len(processed_data_rows[0]):
            df = pd.DataFrame(processed_data_rows, columns=headers)
        else:
            df = pd.DataFrame(processed_data_rows)
            print("警告：表頭提取不匹配或失敗，DataFrame 將使用預設數值欄位名。")
            
            if not df.empty and 0 in df.columns:
                df.rename(columns={0: '股票代號_名稱'}, inplace=True)


        if not df.empty:
            if '股票代號_名稱' in df.columns:
                df['股票代號'] = df['股票代號_名稱'].apply(lambda x: re.search(r'^\d{4,5}', x).group(0) if re.search(r'^\d{4,5}', x) else '')
                df['股票名稱'] = df['股票代號_名稱'].apply(lambda x: re.sub(r'^\d{4,5}\s*', '', x) if re.search(r'^\d{4,5}', x) else x)
                df.drop(columns=['股票代號_名稱'], inplace=True)
                
                cols = ['股票代號', '股票名稱'] + [col for col in df.columns if col not in ['股票代號', '股票名稱']]
                df = df[cols]
            
            print(f"已成功提取 {len(df)} 筆股票數據。")
            print("DataFrame 欄位：", df.columns.tolist())
            print("前5筆數據預覽：")
            print(df.head())

            return df
        else:
            print("未提取到任何股票數據。")
            return None

    except Exception as e:
        print(f"在爬蟲過程中發生錯誤：{e}")
        return None
    finally:
        if driver:
            print("關閉瀏覽器。")
            driver.quit() 

# --- 2. CSV 清洗函數 ---
def clean_and_save_goodinfo_csv(df, base_download_path, prefix_name="cleaned_goodinfo_stock_list"):
    """
    清洗股票數據 DataFrame 並儲存為以日期命名的 CSV 檔案。

    清洗步驟：
    1. 刪除 'E', 'S', 'T', 'U', 'V', 'W' 欄位。
    2. 以 '成交張數' 欄位進行降序排序。
    3. 輸出檔案以日期命名 (例如 cleaned_goodinfo_stock_list_20250716.csv)。

    Args:
        df (pd.DataFrame): 包含股票數據的 DataFrame。
        base_download_path (str): 檔案儲存的基礎路徑。
        prefix_name (str): 輸出 CSV 檔案的前綴名稱。
    """
    if df is None or df.empty:
        print("沒有數據可供清洗或儲存。")
        return

    try:
        print("\n--- 開始清洗 DataFrame ---")
        print("原始數據欄位：")
        print(df.columns.tolist())

        # 1. 刪除指定欄位
        columns_to_drop = ['E', 'S', 'T', 'U', 'V', 'W']
        existing_columns_to_drop = [col for col in columns_to_drop if col in df.columns]

        if existing_columns_to_drop:
            print(f"\n正在刪除欄位：{existing_columns_to_drop}")
            df.drop(columns=existing_columns_to_drop, inplace=True)
            print("欄位刪除成功！")
            print("刪除後的數據欄位：")
            print(df.columns.tolist())
        else:
            print("\n未找到指定刪除的欄位，跳過刪除步驟。")

        # 2. 以「成交張數」做降冪排序
        sort_column = "成交張數"
        if sort_column in df.columns:
            print(f"\n正在以 '{sort_column}' 欄位進行降冪排序...")
            df[sort_column] = pd.to_numeric(df[sort_column].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df.sort_values(by=sort_column, ascending=False, inplace=True)
            print("排序成功！")
        else:
            print(f"\n錯誤：未找到排序欄位 '{sort_column}'。請確認欄位名稱是否正確。")
            
        print("\n清洗並排序後數據前5行：")
        print(df.head())

        # 以當前日期命名輸出檔案
        current_date = datetime.now()
        date_str = current_date.strftime("%Y%m%d")
        
        output_file_name = f"{prefix_name}_{date_str}.csv"
        output_csv_full_path = os.path.join(base_download_path, output_file_name)

        print(f"\n正在儲存清洗後的數據到：{output_csv_full_path}")
        df.to_csv(output_csv_full_path, index=False, encoding='utf-8-sig') 
        print("清洗後的數據儲存成功！")

    except Exception as e:
        print(f"在清洗過程中發生錯誤：{e}")

# --- 主執行區塊 ---
if __name__ == "__main__":
    # 新的目標網址：週KD金叉
    target_url = "https://goodinfo.tw/tw2/StockList.asp?RPT_TIME=&MARKET_CAT=%E6%99%BA%E6%85%A7%E9%81%B8%E8%82%A1&INDUSTRY_CAT=%E9%80%B1KD%E9%BB%83%E9%87%91%E4%BA%A4%E5%8F%89%40%40%E9%80%B1KD%E7%9B%B8%E4%BA%92%E4%BA%A4%E5%8F%89%40%40KD%E9%BB%83%E9%87%91%E4%BA%A4%E5%8F%89"
    
    # 新的下載路徑
    download_folder = r"C:\Users\user\Desktop\交易\營收&eps創史高&股價&股淨比小於1\12.週KD金叉\週KD金叉" 
    
    print("--- 開始執行 Goodinfo! 網站股票數據抓取與清洗 (週KD金叉) ---")
    
    # 執行爬蟲，獲取原始 DataFrame
    raw_stock_df = fetch_stock_list_from_goodinfo(target_url, download_folder, headless=False) 

    if raw_stock_df is not None:
        # 將原始 DataFrame 儲存為 CSV (中間檔案，可選)
        raw_output_file_name = os.path.join(download_folder, "goodinfo_stock_list_週KD金叉.csv") # 更改原始數據檔名
        print(f"\n正在儲存原始爬取數據到：{raw_output_file_name}")
        raw_stock_df.to_csv(raw_output_file_name, index=False, encoding='utf-8-sig')
        print("原始數據儲存成功！")

        # 執行數據清洗並儲存最終 CSV
        # 更改清洗後檔案的前綴名稱
        clean_and_save_goodinfo_csv(raw_stock_df.copy(), download_folder, prefix_name="cleaned_goodinfo_stock_list_週KD金叉") 
    else:
        print("\n由於未能成功抓取原始數據，無法進行清洗。請檢查上述錯誤訊息。")

    print("--- 數據抓取與清洗過程結束 ---")