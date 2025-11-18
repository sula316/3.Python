from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import re 
import os 

def get_stock_list_from_goodinfo(url, base_download_path, headless=False): 
    """
    使用 Selenium 爬取 Goodinfo! 股票列表頁面，提取股票數據並儲存到 CSV。

    Args:
        url (str): 目標 Goodinfo! 頁面的 URL。
        base_download_path (str): 檔案下載和儲存的基礎路徑。
        headless (bool): 是否使用無頭模式 (不顯示瀏覽器視窗)。預設為 False。

    Returns:
        pd.DataFrame: 包含股票數據的 DataFrame，如果失敗則返回 None。
    """
    if not os.path.exists(base_download_path):
        os.makedirs(base_download_path)
        print(f"已創建資料夾: {base_download_path}")

    options = Options()
    if headless:
        options.add_argument("--headless")  
    
    options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0")
    
    FIREFOX_BINARY_LOCATION = r"C:\Program Files\Mozilla Firefox\firefox.exe" # 保持此路徑
    
    if not os.path.exists(FIREFOX_BINARY_LOCATION):
        print(f"錯誤：找不到 Firefox 瀏覽器執行檔在 '{FIREFOX_BINARY_LOCATION}'。")
        print("請確認 Firefox 瀏覽器已安裝在上述路徑。")
        print("程式終止。")
        return None
    
    options.binary_location = FIREFOX_BINARY_LOCATION 

    GECKO_DRIVER_PATH = "geckodriver.exe" # 保持此檔案與 .py 程式在同一目錄
    
    if not os.path.exists(GECKO_DRIVER_PATH):
        print(f"錯誤：找不到 GeckoDriver 執行檔在 '{GECKO_DRIVER_PATH}'。")
        print("請確認您已下載與您 Firefox 瀏覽器版本兼容的 64 位元 GeckoDriver，並將其放置在與此程式碼相同的資料夾中。")
        print("程式終止。")
        return None

    service = Service(GECKO_DRIVER_PATH) 

    driver = None
    data = [] 

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

        # 獲取目標表格的 outerHTML，這部分用於除錯並確認 HTML 內容
        stock_table_element = driver.find_element(By.ID, "tblStockList")
        table_outer_html = stock_table_element.get_attribute('outerHTML')

        debug_table_html_path = os.path.join(base_download_path, "debug_tblStockList_content.html")
        with open(debug_table_html_path, "w", encoding="utf-8") as f:
            f.write(table_outer_html)
        print(f"已將 'tblStockList' 表格的完整 HTML 內容儲存到：{debug_table_html_path}")

        # 使用表格的 HTML 內容來建立 BeautifulSoup 物件，進行精確解析
        soup = BeautifulSoup(table_outer_html, 'html.parser')

        # --- **** 表頭提取邏輯：根據最新 HTML，表頭在 tbody 裡，class='bg_h2 fw_bold' **** ---
        headers = []
        # 直接在 soup (即 tblStockList 的內容) 中尋找表頭行
        header_row = soup.find('tr', class_='bg_h2 fw_bold') 
        if header_row:
            for th in header_row.find_all('th'):
                # 表頭文字在 nobr 標籤內
                nobr_tag = th.find('nobr')
                if nobr_tag:
                    headers.append(nobr_tag.get_text(strip=True).replace('\n', '')) # 移除換行符
                else: # 如果沒有 nobr，直接取 th 文字
                    headers.append(th.get_text(strip=True).replace('\n', ''))
        
        if not headers:
            print("警告：未能成功提取表頭。DataFrame 將使用預設數值欄位名。")

        # --- **** 數據行提取邏輯：根據最新 HTML，數據行在 tbody 裡，class 為 'row0' 或 'row1' **** ---
        processed_data_rows = []
        
        # 遍歷所有 id 包含 'row' 的 tr，這是數據行的通用特徵
        # 或者直接找 class=['row0', 'row1']
        data_rows_elements = soup.find_all('tr', id=re.compile(r'row\d+')) # 尋找 id='rowX' 的行
        
        # 或者，如果更簡單，直接找 class="row0" 或 "row1" 的行：
        # data_rows_elements = soup.find_all('tr', class_=['row0', 'row1']) 

        for row in data_rows_elements:
            row_data = []
            # 數據在 th (股票代號名稱) 和 td 中
            # 遍歷當前行所有的 th 和 td
            for cell in row.find_all(['th', 'td']):
                # 數據文字通常在 nobr 標籤內
                nobr_tag = cell.find('nobr')
                if nobr_tag:
                    row_data.append(nobr_tag.get_text(strip=True).replace('\n', ''))
                else: # 如果沒有 nobr，直接取 cell 文字
                    row_data.append(cell.get_text(strip=True).replace('\n', ''))
            
            # 確保這是一條有效的數據行，例如，第一列不為空
            if row_data and row_data[0].strip(): # 檢查第一列是否為空字串或只包含空白
                 processed_data_rows.append(row_data)

        data = processed_data_rows 

        if headers and data and len(headers) == len(data[0]):
            df = pd.DataFrame(data, columns=headers)
        else:
            df = pd.DataFrame(data)
            print("警告：表頭提取不匹配或失敗，DataFrame 將使用預設數值欄位名。")
            
            if not df.empty and 0 in df.columns:
                df.rename(columns={0: '股票代號_名稱'}, inplace=True)


        if not df.empty:
            if '股票代號_名稱' in df.columns:
                # 由於股票代號和名稱是合併在一個欄位中，且代號在 <nobr><a> 中，名稱在另一個 <nobr><a> 中，
                # 我們需要從第一列的原始 HTML 中提取兩者。
                # 圖片顯示第一列是 <th style="mso-number-format:\@;"><nobr><a ...>1313</a></nobr></th>
                # 和第二列是 <th class="divR1"><nobr><a ...>聯成</a></nobr></th>
                # 這表示原始數據行的提取是成功的，問題在於後續的 re 分離是基於 "1313聯成" 這種單一字串。
                # 我們需要修改數據提取部分，讓它直接抓取代號和名稱為獨立的兩列。

                # 重寫這部分邏輯：直接在 data 列表中處理，而不是在 DataFrame 處理。
                # 或者，調整上面遍歷 cells 的邏輯，讓它將前兩個 th 拆開。
                # 考慮到現在代號和名稱分別在兩個獨立的 th 中，那麼我們修改 data_rows_elements 的提取邏輯。
                # 在 cell.find_all(['th', 'td']) 時，它會按照順序抓取。
                # 所以，第一列和第二列已經是分開的了。
                # 這裡的 '股票代號_名稱' 應該不會再被創建，除非 headers 是空的。
                
                # 如果 headers 是空的，或者 pandas 給了數字索引，我們手動指定前兩列為 '代號' 和 '名稱'
                if not headers and len(df.columns) >= 2: # 如果沒有表頭且至少有2列
                    df.rename(columns={df.columns[0]: '代號', df.columns[1]: '名稱'}, inplace=True)
                
                # 最終的股票代號和股票名稱應當是第一列和第二列
                # 移除這段基於 '股票代號_名稱' 的處理，因為現在我們希望它直接是分開的
                pass # 這裡不再需要 re 分割，因為 th 已經是分開的了。
            
            # 由於 Goodinfo 的表頭通常有數十個，這裡只印出部分欄位名以便預覽
            print(f"已成功提取 {len(df)} 筆股票數據。")
            print("DataFrame 欄位：", df.columns.tolist())
            print("前5筆數據預覽：")
            print(df.head())

            output_csv_filename = "goodinfo_stock_list.csv"
            output_csv_path = os.path.join(base_download_path, output_csv_filename) 
            
            print(f"正在儲存數據到 {output_csv_path}...")
            df.to_csv(output_csv_path, index=False, encoding='utf-8-sig') 
            print("數據儲存成功！")
            return df
        else:
            print("未提取到任何股票數據。")
            return None

    except Exception as e:
        print(f"發生錯誤： {e}")
        return None
    finally:
        if driver:
            print("關閉瀏覽器。")
            driver.quit() 

# --- 如何導入和使用 ---
if __name__ == "__main__":
    target_url = "https://goodinfo.tw/tw2/StockList.asp?RPT_TIME=&MARKET_CAT=%E6%99%BA%E6%85%A7%E9%81%B8%E8%82%A1&INDUSTRY_CAT=%E9%95%B7%E7%B4%85%28%E6%A3%92%E5%B9%85%3E3%2E5%25%29%E2%80%93%E7%95%B6%E6%97%A5%40%40%E5%96%AE%E4%B8%80K%E7%B7%9A%E5%9E%8B%E6%85%8B%E2%80%93%E6%97%A5%E7%B7%9A%40%40%E7%95%B6%E6%97%A5%EF%BC%9A%E9%95%B7%E7%B4%85%28%E6%A3%92%E5%B9%85%3E3%2E5%25%29"
    
    download_folder = "C:/Users/user/Desktop/新增資料夾 (3)"
    
    print("--- 開始執行 Goodinfo! 網站股票列表爬蟲 (使用 Firefox) ---")
    
    stock_df = get_stock_list_from_goodinfo(target_url, download_folder, headless=False) 

    if stock_df is not None:
        print(f"\n股票數據已成功抓取並儲存到 {os.path.join(download_folder, 'goodinfo_stock_list.csv')}。")
    else:
        print("\n未能成功抓取股票數據。請檢查上述錯誤訊息。")

    print("--- 爬蟲結束 ---")