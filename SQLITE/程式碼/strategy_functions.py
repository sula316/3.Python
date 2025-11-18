import sqlite3
import datetime

# --- BBS 風格相關定義 (保持不變) ---
COLOR_RESET = "\033[0m"
COLOR_BLUE = "\033[94m"
COLOR_CYAN = "\033[96m"
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
BORDER_JOIN_LEFT = "╠"
BORDER_JOIN_RIGHT = "╣"
BORDER_JOIN_TOP = "╦"
BORDER_JOIN_BOTTOM = "╩"
BORDER_CROSS = "╬"

# --- 輔助函式：用於繪製 BBS 樣式框線 (保持不變) ---
def print_bbs_box(title, content_lines, width=60, title_color=COLOR_YELLOW, content_color=COLOR_CYAN):
    print(title_color + BORDER_TOP_LEFT + BORDER_HORIZONTAL * (width - 2) + BORDER_TOP_RIGHT + COLOR_RESET)
    print(title_color + BORDER_VERTICAL + COLOR_BOLD + f" {title.center(width - 4)} " + COLOR_RESET + title_color + BORDER_VERTICAL + COLOR_RESET)
    print(title_color + BORDER_JOIN_LEFT + BORDER_HORIZONTAL * (width - 2) + BORDER_JOIN_RIGHT + COLOR_RESET)

    for line in content_lines:
        print(content_color + BORDER_VERTICAL + f" {line.ljust(width - 4)}{COLOR_RESET} " + content_color + BORDER_VERTICAL + COLOR_RESET)

    print(title_color + BORDER_BOTTOM_LEFT + BORDER_HORIZONTAL * (width - 2) + BORDER_BOTTOM_RIGHT + COLOR_RESET)

# 驗證日期格式 (保持不變)
def validate_date():
    while True:
        date = input(COLOR_BLUE + "   輸入日期 (YYYY-MM-DD): " + COLOR_RESET)
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
            return date
        except ValueError:
            print(COLOR_RED + "⚠️ 日期格式錯誤，請重新輸入！" + COLOR_RESET)

# --- 功能實作 ---

# 1. 查看所有策略 (view_all_strategies)
def view_all_strategies(conn):
    print(COLOR_YELLOW + "\n╔══════════════════════════════════════╗" + COLOR_RESET)
    print(COLOR_YELLOW + "║" + COLOR_BOLD + f" {'[ 所有台股策略 ]'.center(36)} " + COLOR_RESET + COLOR_YELLOW + "║" + COLOR_RESET)
    print(COLOR_YELLOW + "╚══════════════════════════════════════╝" + COLOR_RESET)

    if conn is None:
        print(COLOR_RED + "錯誤：資料庫連線無效，無法顯示策略。請檢查資料庫連線設定。" + COLOR_RESET)
        return

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT strategy_id, name, description, created_date, status, win_rate, avg_profit_loss FROM strategies ORDER BY created_date DESC, name ASC")
        records = cursor.fetchall()

        if not records:
            print(COLOR_CYAN + "   目前沒有任何策略記錄。\n" + COLOR_RESET)
            return

        header_format = f"{COLOR_BOLD}{COLOR_BLUE}{'ID':<4} {'名稱':<15} {'狀態':<8} {'建立日期':<12} {'盈利率':<8} {'平均盈虧':<10}{COLOR_RESET}"
        print(header_format)
        print(COLOR_BLUE + "═" * 70 + COLOR_RESET)

        for record in records:
            win_rate_str = f"{record[5]*100:.2f}%" if record[5] is not None else "N/A"
            avg_profit_loss_str = f"{record[6]:.2f}" if record[6] is not None else "N/A"
            
            status_color = COLOR_GREEN if record[4] == '運行中' else \
                           (COLOR_YELLOW if record[4] == '回測中' else \
                           (COLOR_CYAN if record[4] == '開發中' else COLOR_RED))

            print(f"{record[0]:<4} {record[1]:<15} {status_color}{record[4]:<8}{COLOR_RESET} {record[3]:<12} {win_rate_str:<8} {avg_profit_loss_str:<10}")
        print(COLOR_BLUE + "═" * 70 + COLOR_RESET)
    except sqlite3.Error as e:
        print(f"{COLOR_RED}查詢策略失敗：{e}{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}發生未知錯誤：{e}{COLOR_RESET}")


# 2. 新增策略 (add_new_strategy)
def add_new_strategy(conn):
    print(COLOR_YELLOW + "\n╔══════════════════════════════════════╗" + COLOR_RESET)
    print(COLOR_YELLOW + "║" + COLOR_BOLD + f" {'[ 新增台股策略 ]'.center(36)} " + COLOR_RESET + COLOR_YELLOW + "║" + COLOR_RESET)
    print(COLOR_YELLOW + "╚══════════════════════════════════════╝" + COLOR_RESET)

    if conn is None:
        print(COLOR_RED + "錯誤：資料庫連線無效，無法新增策略。請檢查資料庫連線設定。" + COLOR_RESET)
        return

    name = input(COLOR_BLUE + "   策略名稱 (必填，唯一): " + COLOR_RESET).strip()
    if not name:
        print(COLOR_RED + "⚠️ 策略名稱不能為空！" + COLOR_RESET)
        return

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM strategies WHERE name = ?", (name,))
        if cursor.fetchone()[0] > 0:
            print(COLOR_RED + "⚠️ 錯誤：此策略名稱已存在，請使用不同名稱！" + COLOR_RESET)
            return
    except sqlite3.Error as e:
        print(COLOR_RED + f"檢查策略名稱時發生錯誤：{e}" + COLOR_RESET)
        return

    description = input(COLOR_BLUE + "   策略描述 (可留空): " + COLOR_RESET).strip()
    created_date = validate_date()

    print(COLOR_BLUE + "   選擇策略狀態:" + COLOR_RESET)
    print(COLOR_CYAN + "   1. 開發中\n   2. 回測中\n   3. 運行中\n   4. 已停用" + COLOR_RESET)
    status_choice = input(COLOR_BLUE + "   請輸入數字選擇狀態 (預設: 1): " + COLOR_RESET).strip()
    statuses = {"1": "開發中", "2": "回測中", "3": "運行中", "4": "已停用"}
    status = statuses.get(status_choice, "開發中")

    win_rate = None
    while True:
        rate_input = input(COLOR_BLUE + "   回測盈利率 (例如 0.65 代表 65%, 可留空): " + COLOR_RESET).strip()
        if not rate_input:
            break
        try:
            rate = float(rate_input)
            if 0 <= rate <= 1:
                win_rate = rate
                break
            else:
                print(COLOR_RED + "⚠️ 盈利率應介於 0 到 1 之間，請重新輸入！" + COLOR_RESET)
        except ValueError:
            print(COLOR_RED + "⚠️ 盈利率必須是數字，請重新輸入！" + COLOR_RESET)

    avg_profit_loss = None
    while True:
        profit_loss_input = input(COLOR_BLUE + "   平均單筆盈虧 (數字, 可留空): " + COLOR_RESET).strip()
        if not profit_loss_input:
            break
        try:
            avg_profit_loss = float(profit_loss_input)
            break
        except ValueError:
            print(COLOR_RED + "⚠️ 平均單筆盈虧必須是數字，請重新輸入！" + COLOR_RESET)

    try:
        cursor.execute(
            "INSERT INTO strategies (name, description, created_date, status, win_rate, avg_profit_loss) VALUES (?, ?, ?, ?, ?, ?)",
            (name, description, created_date, status, win_rate, avg_profit_loss)
        )
        conn.commit()
        print(COLOR_GREEN + f"✅ 策略 '{name}' 成功新增！{COLOR_RESET}")
    except sqlite3.Error as e:
        print(f"{COLOR_RED}新增策略失敗：{e}{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}發生未知錯誤：{e}{COLOR_RESET}")

# 3. 策略常見標的 (strategy_common_targets)
def strategy_common_targets(conn):
    print(COLOR_YELLOW + "\n╔══════════════════════════════════════╗" + COLOR_RESET)
    print(COLOR_YELLOW + "║" + COLOR_BOLD + f" {'[ 策略常見標的 ]'.center(36)} " + COLOR_RESET + COLOR_YELLOW + "║" + COLOR_RESET)
    print(COLOR_YELLOW + "╚══════════════════════════════════════╝" + COLOR_RESET)
    
    if conn is None:
        print(COLOR_RED + "錯誤：資料庫連線無效，無法執行此功能。請檢查資料庫連線設定。" + COLOR_RESET)
        return

    print(COLOR_CYAN + "   此功能需要進一步的資料庫設計，才能追蹤策略的常見標的。\n" + COLOR_RESET)
    print(COLOR_CYAN + "   例如：您可以在 strategies 表中增加 'target_stock_id' 欄位，" + COLOR_RESET)
    print(COLOR_CYAN + "   或者建立一個 'strategy_targets' 關聯表來記錄多個標的。\n" + COLOR_RESET)
    print(COLOR_CYAN + "   目前您可以手動記錄在 'description' 中。\n" + COLOR_RESET)

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT strategy_id, name, description FROM strategies LIMIT 5")
        recent_strategies = cursor.fetchall()
        if recent_strategies:
            print(COLOR_BLUE + "   近期策略範例 (可將標的寫入描述中):" + COLOR_RESET)
            for s_id, name, desc in recent_strategies:
                print(f"   ID: {s_id}, 名稱: {name}, 描述: {desc[:30]}...")
        else:
            print(COLOR_CYAN + "   請先新增一些策略紀錄。\n" + COLOR_RESET)
    except sqlite3.Error as e:
        print(f"{COLOR_RED}查詢策略範例失敗：{e}{COLOR_RESET}")


# 4. 個股查詢 (stock_individual_query)
def stock_individual_query(conn):
    print(COLOR_YELLOW + "\n╔══════════════════════════════════════╗" + COLOR_RESET)
    print(COLOR_YELLOW + "║" + COLOR_BOLD + f" {'[ 個股查詢 ]'.center(36)} " + COLOR_RESET + COLOR_YELLOW + "║" + COLOR_RESET)
    print(COLOR_YELLOW + "╚══════════════════════════════════════╝" + COLOR_RESET)

    if conn is None:
        print(COLOR_RED + "錯誤：資料庫連線無效，無法執行此功能。請檢查資料庫連線設定。" + COLOR_RESET)
        return

    stock_code = input(COLOR_BLUE + "   請輸入欲查詢的股票代碼 (例如 2330): " + COLOR_RESET).strip()
    if not stock_code:
        print(COLOR_RED + "⚠️ 股票代碼不能為空！" + COLOR_RESET)
        return
    
    print(COLOR_CYAN + f"   正在查詢股票代碼 {stock_code} 的資訊...\n" + COLOR_RESET)
    print(COLOR_CYAN + "   此功能通常需要連接外部股票資料 API。\n" + COLOR_RESET)
    print(COLOR_CYAN + "   例如，使用 'yfinance' 或台灣證券交易所提供的資料介面。\n" + COLOR_RESET)
    print(COLOR_CYAN + "   目前僅為示範，無實際數據。\n" + COLOR_RESET)


# 5. 資料查詢 (query_data) - 這是策略的篩選查詢
def query_data(conn):
    print(COLOR_YELLOW + "\n╔══════════════════════════════════════╗" + COLOR_RESET)
    print(COLOR_YELLOW + "║" + COLOR_BOLD + f" {'[ 策略資料查詢 (進階篩選) ]'.center(36)} " + COLOR_RESET + COLOR_YELLOW + "║" + COLOR_RESET)
    print(COLOR_YELLOW + "╚══════════════════════════════════════╝" + COLOR_RESET)

    if conn is None:
        print(COLOR_RED + "錯誤：資料庫連線無效，無法搜尋策略。請檢查資料庫連線設定。" + COLOR_RESET)
        return

    search_term = input(COLOR_BLUE + "   請輸入關鍵字 (策略名稱/描述, 留空則不篩選): " + COLOR_RESET).strip()
    print(COLOR_BLUE + "   狀態篩選選項:" + COLOR_RESET)
    print(COLOR_CYAN + "   1. 開發中\n   2. 回測中\n   3. 運行中\n   4. 已停用\n   (留空則不篩選)" + COLOR_RESET)
    status_filter_choice = input(COLOR_BLUE + "   請輸入數字選擇狀態: " + COLOR_RESET).strip()
    
    statuses_map = {"1": "開發中", "2": "回測中", "3": "運行中", "4": "已停用"}
    status_filter = statuses_map.get(status_filter_choice, "")

    cursor = conn.cursor()
    query = "SELECT strategy_id, name, description, created_date, status, win_rate, avg_profit_loss FROM strategies WHERE 1=1"
    params = []

    if search_term:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)

    query += " ORDER BY created_date DESC, name ASC"

    try:
        cursor.execute(query, tuple(params))
        filtered_records = cursor.fetchall()

        if not filtered_records:
            print(COLOR_RED + "⚠️ 找不到符合條件的策略紀錄！" + COLOR_RESET)
            return
        
        print(COLOR_YELLOW + f"\n📜 搜尋結果：" + COLOR_RESET)
        header_format = f"{COLOR_BOLD}{COLOR_BLUE}{'ID':<4} {'名稱':<15} {'狀態':<8} {'建立日期':<12} {'盈利率':<8} {'平均盈虧':<10}{COLOR_RESET}"
        print(header_format)
        print(COLOR_BLUE + "═" * 70 + COLOR_RESET)

        for record in filtered_records:
            win_rate_str = f"{record[5]*100:.2f}%" if record[5] is not None else "N/A"
            avg_profit_loss_str = f"{record[6]:.2f}" if record[6] is not None else "N/A"
            status_color = COLOR_GREEN if record[4] == '運行中' else (COLOR_YELLOW if record[4] == '回測中' else (COLOR_CYAN if record[4] == '開發中' else COLOR_RED))
            print(f"{record[0]:<4} {record[1]:<15} {status_color}{record[4]:<8}{COLOR_RESET} {record[3]:<12} {win_rate_str:<8} {avg_profit_loss_str:<10}")
        
        print(COLOR_BLUE + "═" * 70 + COLOR_RESET)

    except sqlite3.Error as e:
        print(f"{COLOR_RED}搜尋策略失敗：{e}{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}發生未知錯誤：{e}{COLOR_RESET}")

# 6. 顯示圖表 (plot_strategy_results)
def show_charts(conn):
    print(COLOR_YELLOW + "\n╔══════════════════════════════════════╗" + COLOR_RESET)
    print(COLOR_YELLOW + "║" + COLOR_BOLD + f" {'[ 策略盈利率分佈與單獨表現 ]'.center(36)} " + COLOR_RESET + COLOR_YELLOW + "║" + COLOR_RESET)
    print(COLOR_YELLOW + "╚══════════════════════════════════════╝" + COLOR_RESET)

    if conn is None:
        print(COLOR_RED + "錯誤：資料庫連線無效，無法繪製圖表。請檢查資料庫連線設定。" + COLOR_RESET)
        return

    cursor = conn.cursor()
    try:
        # 在函式內部匯入 matplotlib.pyplot 和 pandas
        # 這是為了解決循環引用問題，確保它們在需要時才被載入
        import pandas as pd
        import matplotlib.pyplot as plt
        import matplotlib # 雖然已在檔頭，但為了安全再次確保

        matplotlib.use("TkAgg") # 確保繪圖後端在這裡設定

        cursor.execute("SELECT name, win_rate, avg_profit_loss FROM strategies WHERE win_rate IS NOT NULL AND avg_profit_loss IS NOT NULL")
        results = cursor.fetchall()

        if not results:
            print(COLOR_RED + "⚠️ 沒有可供繪製圖表的策略記錄 (需有盈利率和平均盈虧數據)！" + COLOR_RESET)
            return
        
        strategy_names = [row[0] for row in results]
        win_rates = [row[1] for row in results]
        avg_profit_losses = [row[2] for row in results]

        # --- 繪製盈利率分佈直方圖 ---
        plt.figure(figsize=(10, 6))
        pd.Series(win_rates).hist(bins=5, edgecolor='black', color='lightgreen', alpha=0.7)
        plt.xlabel("回測盈利率 (0-1之間)")
        plt.ylabel("策略數量")
        plt.title("策略回測盈利率分佈直方圖")
        plt.grid(axis='y', alpha=0.75)
        plt.xticks([i/10 for i in range(11)])
        plt.tight_layout()
        plt.show()

        # --- 繪製各策略盈利率條形圖 ---
        if strategy_names:
            plt.figure(figsize=(12, 7))
            plt.bar(strategy_names, win_rates, color='teal')
            plt.xlabel("策略名稱")
            plt.ylabel("回測盈利率")
            plt.title("各策略回測盈利率")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.show()

        # --- 繪製各策略平均單筆盈虧條形圖 ---
        if strategy_names:
            plt.figure(figsize=(12, 7))
            colors = ['green' if apl >= 0 else 'red' for apl in avg_profit_losses]
            plt.bar(strategy_names, avg_profit_losses, color=colors)
            plt.xlabel("策略名稱")
            plt.ylabel("平均單筆盈虧")
            plt.title("各策略平均單筆盈虧")
            plt.xticks(rotation=45, ha='right')
            plt.axhline(0, color='grey', linestyle='--', linewidth=0.8)
            plt.tight_layout()
            plt.show()

    except ImportError as ie:
        print(f"{COLOR_RED}錯誤：繪圖所需模組未能匯入。請確認已安裝 pandas 和 matplotlib。詳細: {ie}{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}繪製策略結果圖表失敗：{e}{COLOR_RESET}")