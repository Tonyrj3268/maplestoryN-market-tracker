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