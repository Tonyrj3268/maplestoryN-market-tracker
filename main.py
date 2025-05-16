import os
import argparse
from driver import initialize_driver
from buyer import auto_buy_pet, auto_buy_multiple_equipment

def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(description='楓之谷N市集自動化交易工具')
    parser.add_argument('--mode', type=str, choices=['pet', 'multi_equipment'], 
                      default='pet', help='選擇執行模式: pet (寵物) 或 multi_equipment (多裝備同時監控)')
    
    args = parser.parse_args()
    
    # 確保設定檔存在
    if not os.path.exists('config.json'):
        print("錯誤: 找不到config.json檔案")
        print("請先建立設定檔 config.json，包含以下必要欄位")
        sample_config = '''{
            "private_key": "你的錢包私鑰",
            "metamask_pasw": "你的MetaMask密碼",
            "chrome_path": "C:\\Users\\你的使用者名稱\\路徑\\到\\chromium資料夾\\chrome執行檔",
            "chromedriver_path": "C:\\Users\\你的使用者名稱\\路徑\\到\\chromium資料夾\\chromedriver執行檔",
            "user_data_dir": "C:\\Users\\你的使用者名稱\\AppData\\Local\\Chromium\\User Data",
            "wallet": "0x你的錢包地址"
        }'''
        print(f"範例設定:\n{sample_config}")
        return

    # 初始化驅動程式
    driver = initialize_driver()
    if driver is None:
        print("初始化失敗，程式結束")
        return
    
    try:
        # 根據選擇的模式執行相應的功能
        if args.mode == 'pet':
            auto_buy_pet(driver)
        elif args.mode == 'multi_equipment':
            print("啟動多裝備監控模式")
            print("注意: 多裝備模式將同時監控 config.py 中 EQUIPMENT_MONITOR_LIST 設定的所有裝備")
            print("      每種裝備可以設定各自的價格上限")
            auto_buy_multiple_equipment(driver)
    except KeyboardInterrupt:
        print("程式被手動中斷")
    except Exception as e:
        print(f"執行時發生錯誤: {e}")
    finally:
        if driver:
            driver.quit()
        print("程式已結束")

if __name__ == "__main__":
    main() 