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
        tuple: (pd.DataFrame, list, str) 包含股票數據的 DataFrame, 表頭列表, 和用於 debug 檔名的頁面描述。
               如果失敗則返回 (None, None, None)。
    """
    # 確保下載路徑存在，如果不存在則創建
    if not os.path.exists(base_download_path):
        os.makedirs(base_download_path)
        print(f"已創建資料夾: {base_download_path}")

    options = Options()
    if headless:
        options.add_argument("--headless")
    
    options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0")
    
    FIREFOX_BINARY_LOCATION = r"C:\Program Files\Mozilla Firefox\firefox.exe" 
    
    if not os.path.exists(FIREFOX_BINARY_LOCATION):
        print(f"錯誤：找不到 Firefox 瀏覽器執行檔在 '{FIREFOX_BINARY_LOCATION}'。")
        print("請確認 Firefox 瀏覽器已安裝在上述路徑。")
        return None, None, None 
    options.binary_location = FIREFOX_BINARY_LOCATION 

    GECKO_DRIVER_PATH = "geckodriver.exe" 
    
    if not os.path.exists(GECKO_DRIVER_PATH):
        print(f"錯誤：找不到 GeckoDriver 執行檔在 '{GECKO_DRIVER_PATH}'。")
        print("請確認您已下載與您 Firefox 瀏覽器版本兼容的 64 位元 GeckoDriver，並將其放置在與此程式碼相同的資料夾中。")
        return None, None, None 

    service = Service(GECKO_DRIVER_PATH) 

    driver = None
    df = None 
    
    # 這裡的 page_description_for_debug_html 僅用於初始 debug HTML 檔案名，後續會被重命名
    page_description_for_debug_html = "中紅棒_原始抓取" 

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

        # 生成初始的 debug HTML 檔案，之後可能會被重命名
        debug_table_html_path = os.path.join(base_download_path, f"debug_tblStockList_content_{page_description_for_debug_html}.html") 
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
                    text_content = nobr_tag.get_text(strip=True).replace('\n', '')
                else:
                    text_content = cell.get_text(strip=True).replace('\n', '')
                
                # 處理圖片欄位，嘗試從 title 屬性提取數據
                img_link_tag = cell.find('a', title=re.compile(r'查看 .*K線圖')) 
                if img_link_tag and 'title' in img_link_tag.attrs:
                    title_text = img_link_tag['title']
                    price_match = re.search(r'成交價\s*:\s*([\d.]+)', title_text)
                    if price_match:
                        row_data.append(price_match.group(1).strip()) 
                    else:
                        row_data.append("") 
                elif img_link_tag and 'title' in img_link_tag.attrs and '走勢圖' in img_link_tag['title']:
                    row_data.append("") 
                else:
                    row_data.append(text_content)
            
            if row_data and row_data[0].strip():
                 processed_data_rows.append(row_data)

        if headers and processed_data_rows and len(headers) == len(processed_data_rows[0]):
            df = pd.DataFrame(processed_data_rows, columns=headers)
        else:
            df = pd.DataFrame(processed_data_rows)
            print("警告：表頭提取不匹配或失敗，DataFrame 將使用預設數值欄位名。")
            
            if not df.empty:
                if 0 in df.columns and 1 in df.columns:
                    first_col_val = df.iloc[0, 0]
                    if re.match(r'^\d{4,5}[A-Z]*$', str(first_col_val)): 
                        df.rename(columns={0: '代號', 1: '名稱'}, inplace=True)
                
                if '股票代號_名稱' in df.columns:
                    df['代號'] = df['股票代號_名稱'].apply(lambda x: re.search(r'^\d{4,5}[A-Z]*', x).group(0) if re.search(r'^\d{4,5}[A-Z]*', x) else '')
                    df['名稱'] = df['股票代號_名稱'].apply(lambda x: re.sub(r'^\d{4,5}[A-Z]*\s*', '', x) if re.search(r'^\d{4,5}[A-Z]*', x) else x)
                    df.drop(columns=['股票代號_名稱'], inplace=True)
                    
                    cols = ['代號', '名稱'] + [col for col in df.columns if col not in ['代號', '名稱']]
                    df = df[cols]

        if not df.empty:
            # 1. CSV 內排序：依照「代號」欄位由小到大做排列
            if '代號' in df.columns:
                df['代號'] = df['代號'].astype(str) 
                df.sort_values(by='代號', ascending=True, inplace=True)
                print("\n數據已依照 '代號' 欄位由小到大排序。")
            else:
                print("\n警告：未找到 '代號' 欄位，跳過排序。")
            
            print(f"已成功提取 {len(df)} 筆股票數據。")
            print("DataFrame 欄位：", df.columns.tolist())
            print("前5筆數據預覽：")
            print(df.head())

            return df, headers, debug_table_html_path # 返回 DataFrame, 表頭, 和初始 debug HTML 路徑
        else:
            print("未提取到任何股票數據。")
            return None, None, None 

    except Exception as e:
        print(f"在爬蟲過程中發生錯誤：{e}")
        return None, None, None 
    finally:
        if driver:
            print("關閉瀏覽器。")
            driver.quit() 

# --- 2. 這是數據保存函數 (不包含清洗邏輯，只負責命名和儲存) ---
def save_raw_data(df, base_download_path, headers, initial_debug_html_path):
    """
    將股票數據 DataFrame 儲存為 CSV 檔案，並處理檔名及 Debug HTML 檔案的重命名。

    Args:
        df (pd.DataFrame): 包含股票數據的 DataFrame。
        base_download_path (str): 檔案儲存的基礎路徑。
        headers (list): 爬取到的原始表頭列表。
        initial_debug_html_path (str): 初始 Debug HTML 檔案的完整路徑。
    """
    if df is None or df.empty:
        print("沒有數據可供儲存。")
        return

    try:
        print("\n--- 開始儲存 DataFrame ---")
        
        current_date = datetime.now()
        date_str = datetime.now().strftime("%Y%m%d") # 使用最新日期
        
        # 獲取最右欄位的名稱 (例如 '25W30收盤價')
        rightmost_col_full_name = headers[-1]
        # 移除「收盤價」和 HTML 換行標籤 (<br>)
        processed_rightmost_col_name = rightmost_col_full_name.replace('收盤價', '').replace('<br>', '').strip()
        
        # 構造最終的檔案基底名稱 (不含副檔名)
        final_file_base_name = f"中紅棒_上週_日線_{processed_rightmost_col_name}_{date_str}"

        # 構造 CSV 檔案的完整路徑
        output_csv_filename = f"{final_file_base_name}.csv"
        output_csv_path = os.path.join(base_download_path, output_csv_filename)

        print(f"\n正在儲存數據到：{output_csv_path}")
        df.to_csv(output_csv_path, index=False, encoding='utf-8-sig') 
        print("數據儲存成功 (CSV 檔案)！")

        # --- HTML 檔名：同上 (與 CSV 檔名一致，只改副檔名) ---
        new_debug_html_filename = f"{final_file_base_name}.html"
        new_debug_html_path = os.path.join(base_download_path, new_debug_html_filename)

        if os.path.exists(initial_debug_html_path):
            os.rename(initial_debug_html_path, new_debug_html_path)
            print(f"Debug HTML 檔名已更新為：{new_debug_html_path}")
        else:
            print(f"原始 Debug HTML 檔案 '{initial_debug_html_path}' 不存在，無法更名。")

    except Exception as e:
        print(f"在儲存過程中發生錯誤：{e}")

# --- 主執行區塊 ---
if __name__ == "__main__":
    # 目標網址：中紅(棒幅>5%且<=10%)–上週
    target_url = "https://goodinfo.tw/tw2/StockList.asp?RPT_TIME=&MARKET_CAT=%E6%99%BA%E6%85%A7%E9%81%B8%E8%82%A1&INDUSTRY_CAT=%E4%B8%AD%E7%B4%85%28%E6%A3%92%E5%B9%85%3E5%25%E4%B8%94%3C%3D10%25%29%E2%80%93%E4%B8%8A%E9%80%B1%40%40%E5%96%AE%E4%B8%80K%E7%B7%9A%E5%9E%8B%E6%85%8B%E2%80%93%E9%80%B1%E7%B7%9A%40%40%E4%B8%8A%E9%80%B1%EF%BC%9A%E4%B8%AD%E7%B4%85%28%E6%A3%92%E5%B9%85%3E5%25%E4%B8%94%3C%3D10%25%29"
    
    # 下載路徑 (已更新為您指定的新路徑)
    download_folder = r"C:\Users\user\Desktop\交易\營收&eps創史高&股價&股淨比小於1\16.週紅K大於5" 
    
    print("--- 開始執行 Goodinfo! 網站股票數據抓取 (中紅棒) ---") 
    
    raw_stock_df, headers_from_fetch, initial_debug_html_path = fetch_stock_list_from_goodinfo(target_url, download_folder, headless=False) 

    if raw_stock_df is not None:
        save_raw_data(raw_stock_df.copy(), download_folder, headers_from_fetch, initial_debug_html_path) 
    else:
        print("\n未能成功抓取原始數據。")

    print("--- 數據抓取過程結束 ---")