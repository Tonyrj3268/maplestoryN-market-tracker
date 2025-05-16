# 楓之谷N市集自動化交易工具

用於自動化監控和購買 MapleStory N Marketplace 中寵物和裝備的工具

## 功能特點

- 自動監控市集中的寵物，根據技能組合和價格自動購買
- 支援同時監控多種裝備，根據名稱關鍵字匹配和價格上限自動購買
- 減少API呼叫次數，提高監控效率
- 自動處理MetaMask錢包連接和簽名

## 安裝需求

1. Python 3.13 或更高版本
2. 安裝所需套件：
   ```
   pip install -r requirements.txt
   ```

## 設定說明

1. 建立 `config.json` 檔案並填入以下所有必要資訊：
   ```json
   {
     "private_key": "你的錢包私鑰",
     "wallet": "0x你的錢包地址"
   }
   ```
   > **注意**: 程式會在啟動時檢查這些設定項是否存在

2. 多裝備監控設定方法：
   
   在 `config.py` 中修改 `EQUIPMENT_MONITOR_LIST` 變數設定要監控的裝備及其價格上限：
   ```python
   EQUIPMENT_MONITOR_LIST = {
       "Golden Clover Belt": 200000,    # 裝備名稱: 價格上限（單位為遊戲幣）
       "Noble Ifia's Ring": 380000,
       "Crystal Ventus Badge": 380000,
       "Arcane Umbra Hat": None,        # 設為None表示使用預設價格上限
       # 可以新增更多裝備...
   }
   ```

   每個裝備都可以設定不同的價格上限，當市場出現名稱包含關鍵字且價格低於設定上限的裝備時，系統會自動購買。

3. 預設價格上限設定：
   
   如果某些裝備沒有特別指定價格上限（設為None），系統會使用 `DEFAULT_EQUIPMENT_PRICE_LIMIT` 的值作為預設上限：
   ```python
   # 多裝備監控模式的預設價格上限
   DEFAULT_EQUIPMENT_PRICE_LIMIT = 300000
   ```

4. 寵物篩選條件設定：
   
   如需調整寵物篩選條件，可編輯 `config.py` 中的 `PET_FILTERS` 變數：
   ```python
   PET_FILTERS = [
       [{"Magnet Effect"}, 385501],            # 技能集合, 價格上限
       [{"Auto Buff"}, 385501],
       [{"Expanded Auto Move", "Auto Move"}, 10000],
       # 可添加更多條件...
   ]
   ```

## 使用方法

### 監控寵物

```bash
python main.py --mode pet
```

### 監控多種裝備

```bash
python main.py --mode equipment
```

此模式會同時監控 `config.py` 中 `EQUIPMENT_MONITOR_LIST` 設定的所有裝備，大幅減少 API 呼叫次數，提高效率。對每個裝備使用其對應的價格上限進行判斷，如果沒有指定價格上限（設為None），則使用 `DEFAULT_EQUIPMENT_PRICE_LIMIT` 的值。