import tkinter as tk
from tkinter import ttk, font
import twstock
from datetime import datetime
import threading

def get_stock_info(stock_ids: list[str]) -> dict:
    """
    在背景執行緒中，使用 twstock 取得多支股票的即時資訊。
    """
    try:
        realtime_data = twstock.realtime.get(stock_ids)
        return realtime_data
    except Exception as e:
        # 在背景執行緒中，印出錯誤有助於除錯
        print(f"抓取資料時發生錯誤: {e}")
        return {}

class StockMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("即時股票看盤")
        self.root.geometry("850x400") # 加寬視窗以容納所有欄位

        # --- 設定樣式 ---
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Microsoft JhengHei UI", 12, 'bold'))
        style.configure("Treeview", font=("Microsoft JhengHei UI", 11), rowheight=28)

        # --- 建立介面元件 ---
        self.setup_ui()

        # --- 資料與狀態 ---
        self.target_stocks = []
        self.is_running = False
        self.update_job = None # 用來儲存 after() 排程的 ID

    def setup_ui(self):
        # --- 上方控制項框架 ---
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="股票代號 (用空格分開):").pack(side=tk.LEFT, padx=(0, 5))
        
        self.stock_input = ttk.Entry(top_frame, font=("Arial", 11))
        self.stock_input.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.stock_input.insert(0, "2330 2317 2454 0050 00878") # 預設值

        self.start_button = ttk.Button(top_frame, text="開始監控", command=self.toggle_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)

        # --- 中間的表格框架 ---
        tree_frame = ttk.Frame(self.root, padding="0 10 0 10")
        tree_frame.pack(expand=True, fill=tk.BOTH)

        columns = ("code", "name", "price", "change", "change_percent", "volume", "high", "low")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        # 定義欄位標題
        headings = {"code": "代號", "name": "名稱", "price": "成交價", "change": "漲跌", 
                    "change_percent": "漲跌幅(%)", "volume": "成交量", "high": "最高", "low": "最低"}
        for col, text in headings.items():
            self.tree.heading(col, text=text)

        # 設定欄位寬度與對齊
        self.tree.column("code", width=80, anchor=tk.CENTER)
        self.tree.column("name", width=100, anchor=tk.W)
        self.tree.column("price", width=100, anchor=tk.E)
        self.tree.column("change", width=100, anchor=tk.E)
        self.tree.column("change_percent", width=120, anchor=tk.E)
        self.tree.column("volume", width=120, anchor=tk.E)
        self.tree.column("high", width=100, anchor=tk.E)
        self.tree.column("low", width=100, anchor=tk.E)

        # 設定顏色標籤
        self.tree.tag_configure("red", foreground="#d32f2f", font=("Microsoft JhengHei UI", 11, 'bold'))
        self.tree.tag_configure("green", foreground="#388e3c", font=("Microsoft JhengHei UI", 11, 'bold'))
        self.tree.tag_configure("white", foreground="black")

        self.tree.pack(expand=True, fill=tk.BOTH)

        # --- 底部狀態列 ---
        self.status_bar = ttk.Label(self.root, text="準備就緒", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def toggle_monitoring(self):
        if self.is_running:
            # --- 停止監控 ---
            self.is_running = False
            if self.update_job:
                self.root.after_cancel(self.update_job)
                self.update_job = None
            self.start_button.config(text="開始監控")
            self.status_bar.config(text="監控已停止。")
        else:
            # --- 開始監控 ---
            self.target_stocks = self.stock_input.get().strip().split()
            if not self.target_stocks or self.target_stocks == ['']:
                self.status_bar.config(text="錯誤：請輸入至少一個股票代號。")
                return
            
            self.is_running = True
            self.start_button.config(text="停止監控")
            self.run_update_cycle()

    def run_update_cycle(self):
        """啟動一個更新週期"""
        if not self.is_running:
            return
        
        self.status_bar.config(text="正在更新資料...")
        # 使用執行緒抓取資料，避免凍結 GUI
        thread = threading.Thread(target=self.fetch_data_in_background, daemon=True)
        thread.start()

    def fetch_data_in_background(self):
        """(在背景執行緒中執行) 抓取資料"""
        stock_data = get_stock_info(self.target_stocks)
        # 抓取完畢後，將更新 UI 的任務交回給主執行緒
        self.root.after(0, self.update_ui_with_data, stock_data)

    def update_ui_with_data(self, stock_data):
        """(在主執行緒中執行) 用新資料更新 Treeview"""
        if not self.is_running:
            return

        self.tree.delete(*self.tree.get_children()) # 更簡潔的清空方式

        for stock_id in self.target_stocks:
            data = stock_data.get(stock_id)
            if not data or not data.get('success', False):
                self.tree.insert("", "end", values=(stock_id, "查無資料", "-", "-", "-", "-", "-", "-"))
                continue

            info = data['info']
            realtime = data['realtime']
            
            price = float(realtime.get('latest_trade_price', 0))
            yesterday_close = float(info.get('yesterday_price', 0))
            
            change = price - yesterday_close
            change_percent = (change / yesterday_close) * 100 if yesterday_close != 0 else 0

            color_tag = "white"
            if change > 0:
                color_tag = "red"
                change_str = f"▲ {change:.2f}"
            elif change < 0:
                color_tag = "green"
                change_str = f"▼ {abs(change):.2f}"
            else:
                change_str = f"{change:.2f}"

            values = (
                info.get('code', stock_id), info.get('name', 'N/A'),
                f"{price:.2f}", change_str, f"{change_percent:.2f}%",
                f"{int(realtime.get('accumulate_trade_volume', 0)):,}",
                f"{float(realtime.get('high', 0)):.2f}", f"{float(realtime.get('low', 0)):.2f}"
            )
            self.tree.insert("", "end", values=values, tags=(color_tag,))

        now = datetime.now()
        self.root.title(f"即時股票看盤 (更新時間: {now.strftime('%H:%M:%S')})")
        self.status_bar.config(text=f"上次更新: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 安排 5 秒後再次執行更新週期
        self.update_job = self.root.after(5000, self.run_update_cycle)

if __name__ == "__main__":
    root = tk.Tk()
    app = StockMonitorApp(root)
    # 監聽視窗關閉事件，確保程式能乾淨地結束
    root.protocol("WM_DELETE_WINDOW", lambda: (app.is_running and app.toggle_monitoring(), root.destroy()))
    root.mainloop()
