import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from datetime import datetime, timedelta
import threading
import io

# 匯入繪圖相關函式庫
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import mplfinance as mpf
import yfinance as yf

# 匯入 FinMind 資料庫 API
from FinMind.data import FinMindApi

# --- 設定 Matplotlib 使用支援中文的字體 ---
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] # 微軟正黑體
plt.rcParams['axes.unicode_minus'] = False  # 解決負號顯示問題

class StockAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("股票歷史數據分析")
        self.root.geometry("900x700")

        # --- FinMind API 初始化 (已整合您的 Token) ---
        self.api_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNS0wOC0wNCAwMDo0Mzo1NSIsInVzZXJfaWQiOiJzdWxhMzE2MTAiLCJpcCI6IjEuMTY4LjUyLjE3MSIsImV4cCI6MTc1NDg0NDIzNX0.WFE90jWTiH1WnNNFyVEAUpvjrueJ2NmfAfBM-EU5fsU"
        self.api = FinMindApi()
        
        # 檢查 Token 是否為預設值，如果不是，則自動登入
        if self.api_token == "YOUR_FINMIND_TOKEN":
            messagebox.showwarning("提示", "請記得在程式碼中填入您的 FinMind API Token！")
        else:
            self.api.login_by_token(api_token=self.api_token)

        self.canvas_widget = None
        self.toolbar = None
        self.setup_ui()

    def setup_ui(self):
        # --- 上方控制項框架 ---
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)

        ttk.Label(control_frame, text="股票代號:").pack(side=tk.LEFT, padx=5)
        self.stock_input = ttk.Entry(control_frame, width=10)
        self.stock_input.pack(side=tk.LEFT, padx=5)
        self.stock_input.insert(0, "2330")

        # --- 按鈕們 ---
        ttk.Button(control_frame, text="10年K線圖", command=self.plot_kline).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="5年營收圖", command=self.plot_revenue).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="20季EPS圖", command=self.plot_eps).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="20季ROE圖", command=self.plot_roe).pack(side=tk.LEFT, padx=5)

        # --- 圖表顯示區 ---
        self.plot_frame = ttk.Frame(self.root, padding="10")
        self.plot_frame.pack(expand=True, fill=tk.BOTH)

    def start_task(self, target_function, *args):
        """使用執行緒來執行耗時的任務，避免介面卡死"""
        stock_id = self.stock_input.get().strip()
        if not stock_id:
            messagebox.showerror("錯誤", "請輸入股票代號！")
            return
        
        # 清空舊圖表
        self._clear_plot()
        ttk.Label(self.plot_frame, text=f"正在抓取 {stock_id} 的資料並繪圖，請稍候...").pack()

        # 將 stock_id 和其他參數一起傳遞給目標函式
        thread_args = (stock_id,) + args
        thread = threading.Thread(target=target_function, args=thread_args, daemon=True)
        thread.start()

    def plot_kline(self):
        self.start_task(self._fetch_and_plot_kline)

    def plot_revenue(self):
        self.start_task(self._fetch_and_plot_revenue)

    def plot_eps(self):
        self.start_task(self._fetch_and_plot_eps_roe, "EPS")

    def plot_roe(self):
        self.start_task(self._fetch_and_plot_eps_roe, "ROE")

    def _fetch_and_plot_kline(self, stock_id):
        try:
            # --- 使用 yfinance 獲取資料 ---
            # Yahoo Finance 需要在台股代號後加上市場別：.TW (上市) 或 .TWO (上櫃)
            # 這裡我們先簡單預設為 .TW
            yf_stock_id = f"{stock_id}.TW"
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=10*365)
            
            # 下載資料
            df = yf.download(yf_stock_id, start=start_date, end=end_date)
            
            if df.empty:
                raise ValueError(f"查無 {yf_stock_id} 的K線資料，請確認代號與市場別(.TW 或 .TWO)")

            # 使用 mplfinance 繪製K線圖
            fig, _ = mpf.plot(df, type='candle', style='yahoo',
                              title=f'{stock_id} 過去10年K線圖 (資料來源: Yahoo Finance)',
                              volume=True, returnfig=True)
            self.root.after(0, self._embed_plot, fig)
        except Exception as e:
            self.root.after(0, messagebox.showerror, "錯誤", f"繪製K線圖失敗: {e}")

    def _fetch_and_plot_revenue(self, stock_id):
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
            df = self.api.get_data("TaiwanStockMonthRevenue", stock_id=stock_id, start_date=start_date)
            if df.empty:
                raise ValueError("查無營收資料")

            df['date'] = pd.to_datetime(df['date'])
            df['year'] = df['date'].dt.year
            yearly_revenue = df.groupby('year')['revenue'].sum() / 1e8 # 單位轉為億

            fig = Figure(figsize=(8, 6), dpi=100)
            ax = fig.add_subplot(111)
            yearly_revenue.plot(kind='bar', ax=ax, color='skyblue')
            ax.set_title(f'{stock_id} 過去5年年營收')
            ax.set_xlabel('年份')
            ax.set_ylabel('營收 (億元)')
            ax.tick_params(axis='x', rotation=45)
            fig.tight_layout()
            self.root.after(0, self._embed_plot, fig)
        except Exception as e:
            self.root.after(0, messagebox.showerror, "錯誤", f"繪製營收圖失敗: {e}")

    def _fetch_and_plot_eps_roe(self, stock_id, plot_type):
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
            df = self.api.get_data("TaiwanStockFinancialStatements", stock_id=stock_id, start_date=start_date)
            if df.empty:
                raise ValueError(f"查無 {plot_type} 資料")

            df = df.drop_duplicates(subset=['date', 'type'], keep='last')
            df = df[df['type'] == plot_type].tail(20)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            fig = Figure(figsize=(8, 6), dpi=100)
            ax = fig.add_subplot(111)
            df['value'].plot(kind='bar', ax=ax, color='lightgreen' if plot_type == 'EPS' else 'coral')
            
            title = f'{stock_id} 過去20季 {plot_type}'
            ylabel = '每股盈餘 (元)' if plot_type == 'EPS' else '股東權益報酬率 (%)'
            ax.set_title(title)
            ax.set_xlabel('季度')
            ax.set_ylabel(ylabel)
            
            # 格式化X軸標籤
            labels = [f"{d.year}Q{(d.month-1)//3+1}" for d in df.index]
            ax.set_xticklabels(labels)
            
            fig.tight_layout()
            self.root.after(0, self._embed_plot, fig)
        except Exception as e:
            self.root.after(0, messagebox.showerror, "錯誤", f"繪製 {plot_type} 圖失敗: {e}")

    def _clear_plot(self):
        """清除畫布上的舊圖表和工具列"""
        if self.canvas_widget:
            self.canvas_widget.destroy()
        if self.toolbar:
            self.toolbar.destroy()
        # 清除 "載入中" 的提示文字
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

    def _embed_plot(self, fig):
        """將 Matplotlib 圖表嵌入到 Tkinter 視窗中"""
        self._clear_plot()
        
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas_widget = canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # 加入 Matplotlib 的導覽工具列 (縮放、平移等)
        self.toolbar = NavigationToolbar2Tk(canvas, self.plot_frame)
        self.toolbar.update()
        canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = StockAnalyzerApp(root)
    root.mainloop()
