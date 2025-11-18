import time
import twstock
from rich.console import Console
from rich.live import Live
from rich.table import Table
from datetime import datetime

def get_stock_info(stock_ids: list[str]) -> dict:
    """
    使用 twstock 取得多支股票的即時資訊。
    
    Args:
        stock_ids: 股票代號列表。

    Returns:
        一個包含成功查詢到的股票資訊的字典。
    """
    try:
        realtime_data = twstock.realtime.get(stock_ids)
        return realtime_data
    except Exception as e:
        print(f"抓取資料時發生錯誤: {e}")
        return {}

def generate_table(stock_data: dict) -> Table:
    """
    使用 rich library 產生一個漂亮的股票資訊表格。
    """
    table = Table(title=f"台灣股市即時報價 (更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    
    # 定義表格欄位
    table.add_column("代號", justify="center", style="cyan", no_wrap=True)
    table.add_column("名稱", justify="left", style="cyan")
    table.add_column("成交價", justify="right", style="white")
    table.add_column("漲跌", justify="right")
    table.add_column("漲跌幅(%)", justify="right")
    table.add_column("成交量", justify="right", style="magenta")
    table.add_column("最高", justify="right", style="white")
    table.add_column("最低", justify="right", style="white")
    
    for stock_id, data in stock_data.items():
        if not data.get('success', False):
            table.add_row(stock_id, "查無資料", "-", "-", "-", "-", "-", "-")
            continue

        info = data['info']
        realtime = data['realtime']
        
        price = float(realtime.get('latest_trade_price', 0))
        yesterday_close = float(info.get('yesterday_price', 0))
        
        if yesterday_close == 0: # 處理新上市或無昨日收盤價的情況
            change = 0
            change_percent = 0
        else:
            change = price - yesterday_close
            change_percent = (change / yesterday_close) * 100 if yesterday_close != 0 else 0

        # 根據漲跌設定顏色
        color = "white"
        if change > 0:
            color = "red"
            change_str = f"▲ {change:.2f}"
        elif change < 0:
            color = "green"
            change_str = f"▼ {abs(change):.2f}"
        else:
            change_str = f"{change:.2f}"

        table.add_row(
            info.get('code', stock_id),
            info.get('name', 'N/A'),
            f"[bold {color}]{price:.2f}[/bold {color}]",
            f"[{color}]{change_str}[/{color}]",
            f"[{color}]{change_percent:.2f}%[/{color}]",
            f"{int(realtime.get('accumulate_trade_volume', 0)):,}",
            f"{float(realtime.get('high', 0)):.2f}",
            f"{float(realtime.get('low', 0)):.2f}"
        )
        
    return table

if __name__ == "__main__":
    console = Console()
    
    # 讓使用者輸入股票代號
    stock_input = console.input("[bold yellow]請輸入您想追蹤的股票代號 (用空格分開，例如: 2330 2317 2454):[/bold yellow] ")
    target_stocks = stock_input.strip().split()

    if not target_stocks:
        console.print("[bold red]未輸入任何股票代號，程式即將結束。[/bold red]")
    else:
        # 使用 Live display 來即時更新表格
        with Live(generate_table({}), screen=True, transient=True) as live:
            while True:
                try:
                    stock_info = get_stock_info(target_stocks)
                    table = generate_table(stock_info)
                    live.update(table)
                    time.sleep(5) # 每 5 秒更新一次
                except KeyboardInterrupt:
                    console.print("\n[bold green]感謝使用，程式已結束！[/bold green]")
                    break
                except Exception as e:
                    console.print(f"[bold red]發生未預期的錯誤: {e}[/bold red]")
                    break