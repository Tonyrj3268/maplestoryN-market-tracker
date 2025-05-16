import time
from decimal import Decimal
import config
from api import fetch_all_pets, get_singal_pet_skill_info, buy_item_api, query_equipment, query_equipment_batch
from driver import connect_wallet_to_website

def auto_buy_pet(driver):
    """自動購買寵物"""
    print("開始自動購買寵物模式")
    
    # 顯示篩選條件
    print("\n寵物篩選條件:")
    print("┌─────────────────────────────────┬───────────┐")
    print("│ 技能組合                        │ 價格上限  │")
    print("├─────────────────────────────────┼───────────┤")
    for filter_set in config.PET_FILTERS:
        skills = ", ".join(filter_set[0]) if filter_set[0] else "None"
        price_limit = filter_set[1]
        print(f"│ {skills:<31} │ {price_limit:<9} │")
    print("└─────────────────────────────────┴───────────┘\n")
    
    # 上次擷取到的寵物ID
    last_pet_token_id = None

    while True:
        all_pets_list = fetch_all_pets()
        # 沒有擷取到值時跳過當次迴圈
        if all_pets_list is None:
            continue
        else:
            all_pets_list = all_pets_list["items"]
            first_pet_id = all_pets_list[0]["tokenId"]

        for pet in all_pets_list:
            tokenId = pet["tokenId"]
            # 遇到上一次擷取過的寵物就停止
            if last_pet_token_id == tokenId:
                break

            skill_info = get_singal_pet_skill_info(tokenId)
            if skill_info is None:
                # 沒有擷取到值時跳過當次迴圈
                continue

            pet_skills = set(skill_info)
            # 格式化顯示寵物技能
            skills_text = ", ".join(pet_skills)
            if len(skills_text) > 40:
                skills_text = skills_text[:37] + "..."
            print(f"寵物ID: {tokenId:<10} | 技能: {skills_text:<40}")
            
            for filter_set in config.PET_FILTERS:
                # 檢查 filter_set 是否在 pet_skills 中
                if filter_set[0].issubset(pet_skills):
                    price = Decimal(pet["salesInfo"]["priceWei"]) / config.WEI_PER_ETHER
                    price_limit = filter_set[1]
                    print(f"匹配條件: {', '.join(filter_set[0]) if filter_set[0] else '無技能':<20} | 價格: {price:<8} | 上限: {price_limit:<8}")
                    
                    rounded_price = round(price, 1)
                    if rounded_price <= price_limit:
                        print("-" * 70)
                        print(f"發現高價值寵物!")
                        print(f"ID: {tokenId}")
                        print(f"價格: {price} (上限: {price_limit})")
                        print(f"技能: {', '.join(pet_skills)}")
                        print(f"連結: https://msu.io/marketplace/nft/{tokenId}")
                        print("-" * 70)
                
                        result = buy_item_api(driver, tokenId, pet["salesInfo"]["priceWei"])
                        if result:
                            print(f"已成功購買寵物 (ID: {tokenId})")
                            
                        driver.get(f"https://msu.io/marketplace/inventory/{config.WALLET}")
                        break

            time.sleep(0.1)

        last_pet_token_id = first_pet_id

        time.sleep(8)
        driver.refresh()
        connect_wallet_to_website(driver)

def auto_buy_multiple_equipment(driver):
    """自動監測多個裝備，使用config中的EQUIPMENT_MONITOR_LIST"""
    equipment_list = list(config.EQUIPMENT_MONITOR_LIST.keys())
    
    print(f"開始自動監測多裝備模式: 監測 {len(equipment_list)} 個裝備")
    
    # 顯示監控的裝備和價格上限
    equipment_price_limits = {
        name: price if price is not None else config.DEFAULT_EQUIPMENT_PRICE_LIMIT 
        for name, price in config.EQUIPMENT_MONITOR_LIST.items()
    }
    
    # 格式化顯示監控的裝備和價格上限
    print("\n監控裝備清單:")
    print("┌─────────────────────────────────┬───────────┐")
    print("│ 裝備名稱                        │ 價格上限  │")
    print("├─────────────────────────────────┼───────────┤")
    for name, price in equipment_price_limits.items():
        print(f"│ {name:<31} │ {price:<9} │")
    print("└─────────────────────────────────┴───────────┘\n")
    
    # 用於儲存已處理過的裝備ID
    processed_ids = set()
    last_token_id = None
    
    while True:
        # 獲取最新裝備列表
        all_items = query_equipment_batch()
        if all_items is None:
            time.sleep(3)
            continue
        
        all_items = all_items["items"]
        
        # 檢查是否有新裝備
        if all_items and last_token_id == all_items[0]["tokenId"]:
            # 沒有新裝備，等待下一次查詢
            time.sleep(8)
            driver.refresh()
            connect_wallet_to_website(driver)
            continue
        
        # 更新最新裝備ID
        if all_items:
            last_token_id = all_items[0]["tokenId"]
        
        # 處理每個新裝備
        for item in all_items:
            item_name = item.get("name", "")
            token_id = item["tokenId"]
            
            # 跳過已處理過的裝備ID
            if token_id in processed_ids:
                continue
            
            # 添加到已處理ID集合
            processed_ids.add(token_id)
            
            # 限制已處理ID集合大小
            if len(processed_ids) > 1000:
                processed_ids = set(list(processed_ids)[-500:])
            
            # 計算價格 (Wei → 遊戲幣)
            price_wei = item["salesInfo"]["priceWei"]
            price = int(int(price_wei) / config.WEI_PER_ETHER)
            
            # 檢查是否匹配任何監控的裝備
            for equip_name in equipment_list:
                if equip_name in item_name:
                    # 獲取價格上限
                    price_limit = equipment_price_limits[equip_name]
                    
                    # 使用固定寬度格式化輸出
                    print(f"裝備: {item_name:<30} | 價格: {price:<8} | 上限: {price_limit:<8}")
                    
                    # 如果價格低於上限，嘗試購買
                    if price <= price_limit:
                        print("-" * 70)
                        print(f"發現符合條件的裝備!")
                        print(f"名稱: {item_name}")
                        print(f"價格: {price} (上限: {price_limit})")
                        print(f"連結: https://msu.io/marketplace/nft/{token_id}")
                        print("-" * 70)
                        
                        if buy_item_api(driver, token_id, price_wei):
                            print(f"已成功購買 {item_name}")
                        
                        driver.get(f"https://msu.io/marketplace/inventory/{config.WALLET}")
                        break
            
        # 適當休息，避免頻繁API呼叫
        time.sleep(8)
        driver.refresh()
        connect_wallet_to_website(driver) 