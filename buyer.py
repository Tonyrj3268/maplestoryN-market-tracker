import time
from decimal import Decimal
import config
from api import fetch_all_pets, get_singal_pet_skill_info, buy_item_api, query_equipment_batch

def auto_buy_pet():
    """自動購買寵物"""
    print("開始自動購買寵物模式")

    # 更新並顯示當前錢包餘額
    config.update_wallet_balance()
    
    # 顯示篩選條件
    print("\n寵物篩選條件:")
    print("┌─────────────────────────────────┬───────────┐")
    print("│ 技能組合                        │ 價格上限  │")
    print("├─────────────────────────────────┼───────────┤")
    for filter_set in config.PET_FILTERS:
        skills = ", ".join(filter_set[0]) if filter_set[0] else "None"
        price_limit = filter_set[1] if filter_set[1] is not None else config.WALLET_BALANCE
        print(f"│ {skills:<31} │ {price_limit:<9} │")
    print("└─────────────────────────────────┴───────────┘\n")
    
    # 上次擷取到的寵物ID集合，用於追蹤已處理過的寵物
    processed_pet_ids = set()

    while True:
        try:
            all_pets_list = fetch_all_pets()
            # 沒有擷取到值時跳過當次迴圈
            if all_pets_list is None:
                continue
            else:
                all_pets_list = all_pets_list["items"]
                
            # 檢查是否有新寵物
            has_new_pets = False
            current_pet_ids = {pet["tokenId"] for pet in all_pets_list}
            
            # 找出新寵物（當前批次中但不在已處理集合中的寵物）
            new_pet_ids = current_pet_ids - processed_pet_ids
            if new_pet_ids:
                has_new_pets = True
            
            # 如果沒有新寵物，等待下一次查詢
            if not has_new_pets:
                time.sleep(8)
                continue
                
            for pet in all_pets_list:
                tokenId = pet["tokenId"]
                
                # 跳過已處理的寵物
                if tokenId in processed_pet_ids:
                    continue
                    
                # 將當前寵物ID添加到已處理集合
                processed_pet_ids.add(tokenId)
                
                skill_info = get_singal_pet_skill_info(tokenId)
                if skill_info is None:
                    # 沒有擷取到值時跳過當前寵物
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
                        # 使用指定價格上限或當前錢包餘額
                        price_limit = filter_set[1] if filter_set[1] is not None else config.WALLET_BALANCE
                        
                        print(f"匹配條件: {', '.join(filter_set[0]) if filter_set[0] else '無技能':<20} | 價格: {price:<8} | 上限: {price_limit:<8}")
                        
                        rounded_price = round(price, 1)
                        if rounded_price <= price_limit:
                            print("-" * 70)
                            print(f"發現高價值寵物!")
                            print(f"ID: {tokenId}")
                            print(f"價格: {price} (上限: {price_limit})")
                            print(f"技能: {', '.join(pet_skills)}")
                            print(f"連結: https://msu.io/marketplace/nft/{tokenId}")
                            
                            # 檢查餘額是否足夠
                            if config.WALLET_BALANCE < price:
                                print(f"餘額不足！當前餘額: {config.WALLET_BALANCE:,}，需要: {price:,}")
                                print("交易已跳過")
                                print("-" * 70)
                                break
                                
                            print("-" * 70)
                    
                            result = buy_item_api(tokenId, pet["salesInfo"]["priceWei"])
                            if result:
                                print(f"已成功購買寵物 (ID: {tokenId})")
                                # 購買成功後更新錢包餘額
                                config.update_wallet_balance()
                            break

                time.sleep(0.1)
            
            # 控制已處理寵物ID集合大小，避免無限增長
            if len(processed_pet_ids) > 1000:
                # 只保留最近500個處理過的ID
                processed_pet_ids = set(list(processed_pet_ids)[-500:])
                
            time.sleep(8)
        except KeyboardInterrupt:
            print("程式被手動中斷")
            break
        except Exception as e:
            print(f"發生錯誤: {e}")
            time.sleep(5)
            continue

def auto_buy_multiple_equipment():
    """自動監測多個裝備，使用config中的EQUIPMENT_MONITOR_LIST"""
    equipment_list = list(config.EQUIPMENT_MONITOR_LIST.keys())
    
    print(f"開始自動監測多裝備模式: 監測 {len(equipment_list)} 個裝備")
    
    # 更新並顯示當前錢包餘額
    config.update_wallet_balance()
    
    # 顯示監控的裝備和價格上限
    equipment_price_limits = {
        name: price if price is not None else config.WALLET_BALANCE 
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
    
    # 已處理裝備ID集合，用於追蹤已處理過的裝備
    processed_item_ids = set()
    
    while True:
        try:
            # 獲取最新裝備列表
            all_items = query_equipment_batch()
            if all_items:
                all_items = all_items["items"]
            else:
                # 如果沒有裝備，則等待下一次查詢
                time.sleep(8)
                continue
                
            # 檢查是否有新裝備
            has_new_items = False
            current_item_ids = {item["tokenId"] for item in all_items}
            
            # 找出新裝備（當前批次中但不在已處理集合中的裝備）
            new_item_ids = current_item_ids - processed_item_ids
            if new_item_ids:
                has_new_items = True
            
            # 如果沒有新裝備，等待下一次查詢
            if not has_new_items:
                time.sleep(8)
                continue
            
            for item in all_items:
                item_name = item.get("name", "")
                token_id = item["tokenId"]
                
                # 跳過已處理的裝備
                if token_id in processed_item_ids:
                    continue
                    
                # 將當前裝備ID添加到已處理集合
                processed_item_ids.add(token_id)
                
                # 計算價格 (Wei → 遊戲幣)
                price_wei = item["salesInfo"]["priceWei"]
                price = int(int(price_wei) / config.WEI_PER_ETHER)
                
                # 檢查是否匹配任何監控的裝備
                for equip_name in equipment_list:
                    if equip_name in item_name:
                        # 獲取價格上限，如果是None則使用當前錢包餘額
                        config_price = config.EQUIPMENT_MONITOR_LIST[equip_name]
                        price_limit = config_price if config_price is not None else config.WALLET_BALANCE
                        
                        # 使用固定寬度格式化輸出
                        print(f"裝備: {item_name:<30} | 價格: {price:<8} | 上限: {price_limit:<8}")
                        
                        # 如果價格低於上限，嘗試購買
                        if price <= price_limit:
                            print("-" * 70)
                            print(f"發現符合條件的裝備!")
                            print(f"名稱: {item_name}")
                            print(f"價格: {price} (上限: {price_limit})")
                            print(f"連結: https://msu.io/marketplace/nft/{token_id}")
                            
                            # 檢查餘額是否足夠
                            if config.WALLET_BALANCE < price:
                                print(f"餘額不足！當前餘額: {config.WALLET_BALANCE:,}，需要: {price:,}")
                                print("交易已跳過")
                                print("-" * 70)
                                break
                                
                            print("-" * 70)
                            
                            if buy_item_api(token_id, price_wei):
                                print(f"已成功購買 {item_name}")
                                # 購買成功後更新錢包餘額
                                config.update_wallet_balance()
                            break
            
            # 控制已處理裝備ID集合大小，避免無限增長
            if len(processed_item_ids) > 1000:
                # 只保留最近500個處理過的ID
                processed_item_ids = set(list(processed_item_ids)[-500:])
            
            # 適當休息，避免頻繁API呼叫
            time.sleep(8)
        except KeyboardInterrupt:
            print("程式被手動中斷")
            break
        except Exception as e:
            print(f"發生錯誤: {e}")
            time.sleep(5)
            continue 