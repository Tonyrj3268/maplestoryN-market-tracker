import time
from decimal import Decimal
import config
from api import fetch_all_pets, get_singal_pet_skill_info, buy_item_api, query_equipment, query_equipment_batch
from driver import connect_wallet_to_website

def auto_buy_pet(driver):
    """自動購買寵物"""
    print("開始自動購買寵物模式")
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
            print(f"寵物 {tokenId} 技能: {pet_skills}")
            
            for filter_set in config.PET_FILTERS:
                # 檢查 filter_set 是否在 pet_skills 中
                if filter_set[0].issubset(pet_skills):
                    price = Decimal(pet["salesInfo"]["priceWei"]) / config.WEI_PER_ETHER
                    print(f"價格: {price}")
                    rounded_price = round(price, 1)
                    if rounded_price <= filter_set[1]:
                        formatted_skills = "\\n".join(filter_set[0])
                        message = f"\\n發現高價值寵物\\n價格: ${price}\\n技能:\\n{formatted_skills}\\nhttps://msu.io/marketplace/nft/{tokenId}"
                        print(message)
                
                        result = buy_item_api(driver, tokenId, pet["salesInfo"]["priceWei"])
                        if result:
                            print("已購買成功")
                            
                        driver.get(f"https://msu.io/marketplace/inventory/{config.WALLET}")
                        break

            time.sleep(0.1)

        last_pet_token_id = first_pet_id

        time.sleep(8)
        driver.refresh()
        connect_wallet_to_website(driver)

def auto_buy_multiple_equipment(driver):
    """自動購買多個裝備，使用config中的EQUIPMENT_MONITOR_LIST"""
    equipment_list = list(config.EQUIPMENT_MONITOR_LIST.keys())
    
    print(f"開始自動購買多裝備模式: 監測 {len(equipment_list)} 個裝備")
    
    # 顯示監控的裝備和價格上限
    equipment_price_limits = {
        name: price if price is not None else config.DEFAULT_EQUIPMENT_PRICE_LIMIT 
        for name, price in config.EQUIPMENT_MONITOR_LIST.items()
    }
    
    for name, price in equipment_price_limits.items():
        print(f"  - {name}: 價格上限 {price}")
    
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
                    
                    print(f"裝備: '{item_name}' | 價格: {price} | 上限: {price_limit}")
                    
                    # 如果價格低於上限，嘗試購買
                    if price <= price_limit:
                        print(f"發現符合條件的裝備 | {item_name} | 價格: {price} | https://msu.io/marketplace/nft/{token_id}")
                        
                        if buy_item_api(driver, token_id, price_wei):
                            print(f"已成功購買 {item_name}")
                        
                        driver.get(f"https://msu.io/marketplace/inventory/{config.WALLET}")
                        break
            
        # 適當休息，避免頻繁API呼叫
        time.sleep(8)
        driver.refresh()
        connect_wallet_to_website(driver) 