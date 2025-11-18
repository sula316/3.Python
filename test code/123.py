import click
import requests
import pandas as pd
import io
from datetime import datetime

# 台灣證交所 API (股票代號)
TWSE_STOCK_LIST_URL = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&type=ALLBUT0999"

# 營收 & EPS API
MOPS_REVENUE_URL = "https://mops.twse.com.tw/nas/t21/sii/t21sc03_{year}_{month}_0.html" # 年和月需要格式化
MOPS_EPS_URL = "https://mops.twse.com.tw/nas/t21/sii/t21sc04_{year}_{season}.html" # 綜合損益表(EPS)

# 建立一個 Session，並設定 User-Agent 模擬瀏覽器，提高抓取成功率
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
})

# 取得台股上市公司清單
def get_stock_list():
    print("正在取得所有上市公司清單...")
    try:
        response = SESSION.get(TWSE_STOCK_LIST_URL, timeout=10)
        response.raise_for_status()  # 如果 status code 不是 200，就拋出錯誤
        data = response.json()
        
        if data['stat'] != 'OK':
            print(f"無法從 TWSE 取得股票清單: {data.get('stat')}")
            return pd.DataFrame()

        stocks = []
        for stock in data.get("data9", []):
            stock_id = stock[0].strip()
            stock_name = stock[1].strip()
            stocks.append({"公司代號": stock_id, "公司名稱": stock_name})

        df = pd.DataFrame(stocks)
        print(f"✅ 成功取得 {len(df)} 家上市公司。")
        return df
    except requests.exceptions.RequestException as e:
        print(f"抓取股票清單時發生網路錯誤: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"處理股票清單時發生未知錯誤: {e}")
        return pd.DataFrame()

# 取得歷史營收
def get_revenue(year, month):
    roc_year = year - 1911
    url = MOPS_REVENUE_URL.format(year=roc_year, month=f"{month:02d}")
    print(f"正在抓取 {year} 年 {month} 月營收資料...")
    try:
        response = SESSION.get(url, timeout=15)
        response.raise_for_status()
        
        # 檢查網頁內容是否包含「查無資料」
        if "查無資料" in response.text:
            print(f"⚠️ {year} 年 {month} 月營收資料尚未公佈或無資料。")
            return pd.DataFrame()

        # 使用 io.StringIO 將 html 文字轉換為 file-like object
        df = pd.read_html(io.StringIO(response.text), encoding='big5')[0]
        
        # 清理與選取欄位，更穩健的作法
        df = df.iloc[:, [0, 1, 2, 6]] # 根據 MOPS 網站結構選取欄位
        df.columns = ["公司代號", "公司名稱", "當月營收", "營收年增率(%)"]
        
        # 將營收相關欄位轉為數值，無法轉換的設為 NaN
        df["當月營收"] = pd.to_numeric(df["當月營收"], errors='coerce')
        df["營收年增率(%)"] = pd.to_numeric(df["營收年增率(%)"], errors='coerce')
        
        print(f"✅ 成功處理 {year} 年 {month} 月營收資料。")
        return df
    except requests.exceptions.RequestException as e:
        print(f"抓取營收資料時發生網路錯誤: {e}")
    except (ValueError, IndexError) as e:
        print(f"解析 {year} 年 {month} 月營收 HTML 表格失敗: {e}")
    except Exception as e:
        print(f"處理營收資料時發生未知錯誤: {e}")
    return pd.DataFrame()

# 取得歷史 EPS
def get_eps(year, season):
    roc_year = year - 1911
    url = MOPS_EPS_URL.format(year=roc_year, season=f"{season:02d}")
    print(f"正在抓取 {year} 年 Q{season} EPS 資料...")
    try:
        response = SESSION.get(url, timeout=15)
        response.raise_for_status()
        if "查無資料" in response.text:
            print(f"⚠️ {year} 年 Q{season} EPS 資料尚未公佈或無資料。")
            return pd.DataFrame()

        df = pd.read_html(io.StringIO(response.text), encoding='big5')[0]
        df = df.iloc[:, [0, 1, 18]] # 根據 MOPS 網站結構選取欄位
        df.columns = ["公司代號", "公司名稱", "EPS(元)"]
        df["EPS(元)"] = pd.to_numeric(df["EPS(元)"], errors='coerce')
        
        print(f"✅ 成功處理 {year} 年 Q{season} EPS 資料。")
        return df
    except requests.exceptions.RequestException as e:
        print(f"抓取 EPS 資料時發生網路錯誤: {e}")
    except (ValueError, IndexError) as e:
        print(f"解析 {year} 年 Q{season} EPS HTML 表格失敗: {e}")
    except Exception as e:
        print(f"處理 EPS 資料時發生未知錯誤: {e}")
        return pd.DataFrame()

# CLI 入口點
@click.command()
@click.option("--year", default=datetime.now().year, help="財報年份 (西元)")
@click.option("--month", default=datetime.now().month - 1, help="營收月份")
@click.option("--season", default=(datetime.now().month - 1) // 3, help="EPS 季度 (1-4)")
@click.option("--output", default="fundamentals.xlsx", help="輸出檔案名稱")
def main(year, month, season, output):
    # 取得股票清單
    stock_list = get_stock_list()
    
    # 取得營收 & EPS
    revenue_data = get_revenue(year, month)
    eps_data = get_eps(year - 1 if season == 4 else year, season) # Q4 財報通常在隔年公布

    # 合併資料
    if stock_list.empty:
        print("❌ 未能取得股票清單，無法繼續執行。")
        return

    # 使用 'left' merge，以股票清單為主，並只用 '公司代號' 作為 key
    final_df = stock_list
    if not revenue_data.empty:
        final_df = pd.merge(final_df, revenue_data.drop(columns=['公司名稱']), on="公司代號", how="left")
    if not eps_data.empty:
        final_df = pd.merge(final_df, eps_data.drop(columns=['公司名稱']), on="公司代號", how="left")

    # 儲存為 Excel
    final_df.to_excel(output, index=False, engine='openpyxl')
    print(f"\n🎉 任務完成！基本面資料已儲存至 {output}")

if __name__ == "__main__":
    main()
