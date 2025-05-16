# 楓之谷N市集自動化交易工具

用於自動化監控和購買 MapleStory N Marketplace 中寵物和裝備的工具

## 功能特點

- 自動監控市集中的寵物，根據技能組合和價格自動購買
- 支援同時監控多種裝備，根據名稱關鍵字匹配和價格上限自動購買
- 減少API呼叫次數，提高監控效率
- 自動處理MetaMask錢包連接和簽名

## 安裝需求

1. Python 3.11 或更高版本
2. Chromium 瀏覽器 (建議使用特定版本) 及對應的 ChromeDriver
3. 安裝所需套件：
   ```
   pip install -r requirements.txt
   ```

## Chromium 瀏覽器設定

本專案使用特定版本的 Chromium 瀏覽器以確保穩定性。請依照以下步驟設定：

1. 前往 [Chromium Downloads](https://commondatastorage.googleapis.com/chromium-browser-snapshots/index.html)
2. 根據您的作業系統選擇對應的資料夾：
   - Windows: `Win64`
   - macOS: `Mac`
3. 搜尋並下載 `1345935` 版本的 Chromium
4. 在相同版本號頁面中，同時下載 `chromedriver`
5. 解壓縮兩個壓縮檔，將 `chromedriver` 執行檔複製到 Chromium 應用程式所在資料夾中
6. 手動開啟 Chromium，進入擴充功能頁面
7. 開啟開發人員模式，選擇`載入未封裝功能`，選擇專案資料夾中的`metamask`
8. 手動設定錢包
9. 到 Marketplace 手動測試連結錢包

## 設定說明

1. 建立 `config.json` 檔案並填入以下所有必要資訊（缺一不可）：
   ```json
   {
     "private_key": "你的錢包私鑰",
     "metamask_pasw": "你的MetaMask密碼",
     "chrome_path": "C:\\Users\\你的使用者名稱\\路徑\\到\\chromium資料夾\\chrome執行檔",
     "chromedriver_path": "C:\\Users\\你的使用者名稱\\路徑\\到\\chromium資料夾\\chromedriver執行檔",
     "user_data_dir": "C:\\Users\\你的使用者名稱\\AppData\\Local\\Chromium\\User Data",
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
python main.py --mode multi_equipment
```

此模式會同時監控 `config.py` 中 `EQUIPMENT_MONITOR_LIST` 設定的所有裝備，大幅減少 API 呼叫次數，提高效率。對每個裝備使用其對應的價格上限進行判斷，如果沒有指定價格上限（設為None），則使用 `DEFAULT_EQUIPMENT_PRICE_LIMIT` 的值。

## 注意事項

1. 請確保您已經在 MetaMask 中登入了正確的帳號，且擁有足夠的資金。
2. 初次啟動時，程式會開啟瀏覽器並進行 MetaMask 連接，可能需要您手動確認幾次。
3. 如果遇到連線問題，請確保您使用的是指定版本的 Chromium 瀏覽器。
4. 程式運行過程中請勿手動操作已開啟的瀏覽器視窗，以免干擾自動化流程。