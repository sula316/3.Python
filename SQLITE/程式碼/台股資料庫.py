def main_menu_frame():
    """
    顯示台股策略資料庫的 CLI 主選單框架。
    """
    while True:
        print("\n" + "="*40)
        print("     台股策略資料庫 - 主選單")
        print("="*40)
        print("1. 查看所有策略")
        print("2. 新增策略")
        print("3. 策略常見標的")
        print("4. 個股查詢")
        print("5. 資料查詢")
        print("6. 離開")
        print("="*40)

        choice = input("請選擇功能 (1-6): ").strip()

        if choice == '1':
            print("\n>>> 進入 '查看所有策略' 功能...")
            # 將來這裡會呼叫查看所有策略的函式
            pass
        elif choice == '2':
            print("\n>>> 進入 '新增策略' 功能...")
            # 將來這裡會呼叫新增策略的函式
            pass
        elif choice == '3':
            print("\n>>> 進入 '策略常見標的' 功能...")
            # 將來這裡會呼叫策略常見標的函式
            pass
        elif choice == '4':
            print("\n>>> 進入 '個股查詢' 功能...")
            # 將來這裡會呼叫個股查詢函式
            pass
        elif choice == '5':
            print("\n>>> 進入 '資料查詢' 功能...")
            # 將來這裡會呼叫資料查詢函式
            pass
        elif choice == '6':
            print("\n感謝使用台股策略資料庫！")
            break # 退出迴圈，結束程式
        else:
            print("無效的選擇，請輸入 1-6 之間的數字。")

if __name__ == "__main__":
    main_menu_frame()