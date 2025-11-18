import os
import sys

# 為了確保能找到自定義模組，將當前目錄添加到 Python 路徑
# 這是確保 import database_operations 和 import strategy_functions 能成功的關鍵
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.append(current_dir)

import database_operations # 匯入資料庫操作模組
import strategy_functions # 匯入策略功能模組

# --- BBS 風格相關定義 (保留主程式必要的顏色和邊界字符) ---
COLOR_RESET = "\033[0m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_BOLD = "\033[1m"
COLOR_WHITE_BG_RED_TEXT = "\033[47;91m"

BORDER_TOP_LEFT = "╔"
BORDER_TOP_RIGHT = "╗"
BORDER_BOTTOM_LEFT = "╚"
BORDER_BOTTOM_RIGHT = "╝"
BORDER_HORIZONTAL = "═"
BORDER_VERTICAL = "║"

# --- 輔助函式：用於繪製 BBS 樣式框線 (主程式也需要此函式來繪製選單) ---
def print_bbs_box(title, content_lines, width=60, title_color=COLOR_YELLOW, content_color=COLOR_YELLOW):
    print(title_color + BORDER_TOP_LEFT + BORDER_HORIZONTAL * (width - 2) + BORDER_TOP_RIGHT + COLOR_RESET)
    print(title_color + BORDER_VERTICAL + COLOR_BOLD + f" {title.center(width - 4)} " + COLOR_RESET + title_color + BORDER_VERTICAL + COLOR_RESET)
    print(title_color + BORDER_HORIZONTAL * width + COLOR_RESET) # 分隔線在標題下方

    for line in content_lines:
        print(content_color + BORDER_VERTICAL + f" {line.ljust(width - 4)}{COLOR_RESET} " + content_color + BORDER_VERTICAL + COLOR_RESET)

    print(title_color + BORDER_BOTTOM_LEFT + BORDER_HORIZONTAL * (width - 2) + BORDER_BOTTOM_RIGHT + COLOR_RESET)


# --- 主程式 ---
def main():
    # 嘗試初始化資料庫並獲取連線物件
    conn = database_operations.initialize_database()
    if conn is None:
        # 如果資料庫連線失敗，則在終端機中列印錯誤訊息並終止程式
        print(f"{COLOR_WHITE_BG_RED_TEXT}{COLOR_BOLD}!!! 程式啟動失敗，請檢查上述資料庫錯誤訊息 !!!{COLOR_RESET}")
        return # 終止 main 函式執行

    while True:
        menu_content = [
            "1. 查看所有策略",
            "2. 新增策略",
            "3. 策略常見標的",
            "4. 個股查詢",
            "5. 資料查詢",
            "6. 顯示圖表",
            "7. 離開",
            "", # 空行
            f"{COLOR_BOLD}{COLOR_YELLOW}請選擇功能 (1-7):{COLOR_RESET}"
        ]
        print_bbs_box("《台股策略資料庫》(BBS Style)", menu_content)

        choice = input("").strip()

        if choice == "1":
            strategy_functions.view_all_strategies(conn)
        elif choice == "2":
            strategy_functions.add_new_strategy(conn)
        elif choice == "3":
            strategy_functions.strategy_common_targets(conn)
        elif choice == "4":
            strategy_functions.stock_individual_query(conn)
        elif choice == "5":
            strategy_functions.query_data(conn)
        elif choice == "6":
            strategy_functions.show_charts(conn) # 呼叫更新後的函式名
        elif choice == "7":
            print(COLOR_YELLOW + "\n" + BORDER_TOP_LEFT + BORDER_HORIZONTAL * 30 + BORDER_TOP_RIGHT + COLOR_RESET)
            print(COLOR_YELLOW + BORDER_VERTICAL + COLOR_BOLD + " 感謝使用台股策略資料庫！ ".center(28) + COLOR_RESET + COLOR_YELLOW + BORDER_VERTICAL + COLOR_RESET)
            print(COLOR_YELLOW + BORDER_BOTTOM_LEFT + BORDER_HORIZONTAL * 30 + BORDER_BOTTOM_RIGHT + COLOR_RESET)
            if conn: # 確保連線物件存在才關閉
                conn.close()
                print(COLOR_GREEN + "資料庫連線已關閉。" + COLOR_RESET)
            break
        else:
            print(COLOR_RED + "⚠️ 無效選擇，請輸入 1-7。" + COLOR_RESET)

if __name__ == "__main__":
    main()