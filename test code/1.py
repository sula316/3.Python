import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime
from termcolor import colored

# 記帳檔案名稱
FILE_NAME = "expenses.csv"

# 檢查是否已有記錄文件
if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
    if "ID" not in df.columns:
        df.insert(0, "ID", range(1, len(df) + 1))  # 確保有 ID 欄位
else:
    df = pd.DataFrame(columns=["ID", "日期", "類別", "金額", "備註"])

# 驗證日期格式
def validate_date():
    while True:
        date = input("輸入日期 (YYYY-MM-DD): ")
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
            return date
        except ValueError:
            print("⚠️ 日期格式錯誤，請重新輸入！")

# 記帳功能
def add_expense():
    date = validate_date()
    print("選擇類別:")
    print("1. 餐飲\n2. 交通\n3. 娛樂\n4. 購物\n5. 其他")
    category_choice = input("請輸入數字選擇類別: ")
    categories = {"1": "餐飲", "2": "交通", "3": "娛樂", "4": "購物", "5": "其他"}
    category = categories.get(category_choice, "其他")
    
    while True:
        try:
            amount = float(input("輸入金額: "))
            break
        except ValueError:
            print("⚠️ 金額必須是數字，請重新輸入！")
    
    note = input("備註 (可留空): ")
    
    global df
    new_id = int(df["ID"].max()) + 1 if not df.empty else 1
    new_data = pd.DataFrame([[new_id, date, category, amount, note]], columns=df.columns)
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(FILE_NAME, index=False)
    print(f"✅ 記錄成功！編號: {new_id}")

# 刪除記錄
def delete_expense():
    global df
    show_expenses()
    try:
        delete_id = int(input("輸入要刪除的記錄 ID: "))
        if delete_id in df["ID"].values:
            df = df[df["ID"] != delete_id]
            df.to_csv(FILE_NAME, index=False)
            print(f"✅ 記錄 {delete_id} 已刪除！")
        else:
            print("⚠️ 無效的 ID，請確認後再試！")
    except ValueError:
        print("⚠️ 請輸入有效的數字 ID！")

# 顯示記錄
def show_expenses():
    print("\n📜 所有記帳紀錄：")
    for _, row in df.iterrows():
        display_text = f"ID: {row['ID']} | 日期: {row['日期']} | 類別: {row['類別']} | 金額: {row['金額']} | 備註: {row['備註']}"
        if row["金額"] > 1000:
            print(colored(display_text, "red"))
        elif row["金額"] > 500:
            print(colored(display_text, "yellow"))
        else:
            print(display_text)

# 顯示每日總支出
def daily_summary():
    if df.empty:
        print("⚠️ 沒有記錄。"); return
    summary = df.groupby("日期")["金額"].sum()
    print("\n📊 每日總支出：")
    print(summary)

# 分類支出圖表
def category_analysis():
    if df.empty:
        print("⚠️ 沒有記錄。"); return
    df.groupby("類別")["金額"].sum().plot(kind="pie", autopct="%1.1f%%")
    plt.title("📊 支出類別分析")
    plt.ylabel("")
    plt.show()

# 主選單
def main():
    while True:
        print("\n💰 每日記帳系統")
        print("1. 新增記帳")
        print("2. 顯示所有記錄")
        print("3. 查看每日總支出")
        print("4. 分析支出類別")
        print("5. 刪除記帳記錄")
        print("6. 離開")
        choice = input("請選擇功能 (1-6): ")
        
        if choice == "1":
            add_expense()
        elif choice == "2":
            show_expenses()
        elif choice == "3":
            daily_summary()
        elif choice == "4":
            category_analysis()
        elif choice == "5":
            delete_expense()
        elif choice == "6":
            print("👋 感謝使用記帳系統！"); break
        else:
            print("⚠️ 無效選擇，請輸入 1-6。")

if __name__ == "__main__":
    main()
