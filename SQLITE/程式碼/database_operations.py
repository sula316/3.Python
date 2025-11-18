import sqlite3
import os

# --- 資料庫路徑設定 ---
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
db_folder = os.path.join(desktop_path, "python", "SQLITE")
db_name = "stock_strategy.db"
DB_PATH = os.path.join(db_folder, db_name) # 將路徑設為全域常數，方便其他模組使用

# 確保資料庫資料夾存在
if not os.path.exists(db_folder):
    os.makedirs(db_folder)
    print(f"資料夾 '{db_folder}' 已創建。")

# --- SQLite 資料庫初始化函式 ---
def initialize_database():
    """
    初始化資料庫，如果資料庫檔案不存在則創建，並建立台股策略資料表。
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print(f"成功連線到資料庫：{DB_PATH}")

        # 建立台股策略資料表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategies (
                strategy_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_date TEXT NOT NULL,
                status TEXT NOT NULL,
                win_rate REAL,
                avg_profit_loss REAL
            )
        ''')
        conn.commit()
        print("資料表 'strategies' 已成功建立或已存在。")
        return conn
    except sqlite3.Error as e:
        print(f"資料庫初始化錯誤：{e}")
        return None
    except Exception as e:
        print(f"發生未知錯誤：{e}")
        return None
    finally:
        pass # 連線由 main 函式管理