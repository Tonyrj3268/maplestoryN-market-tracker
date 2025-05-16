import os
import json
from decimal import Decimal

# 1 Ether = 10^18 Wei
WEI_PER_ETHER = Decimal("1000000000000000000")

# 合約地址
TOKEN_ADDRESS = "0x07E49Ad54FcD23F6e7B911C2068F0148d1827c08"
NFT_ADDRESS = "0x43DCff2A0cedcd5e10e6f1c18b503498dDCe60d5"

# 從設定檔讀取設定
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path) as f:
            config = json.load(f)
        
        # 讀取所有設定項，不提供預設值
        private_key = config.get('private_key')
        metamask_pasw = config.get('metamask_pasw')
        chrome_path = config.get('chrome_path')
        chromedriver_path = config.get('chromedriver_path')
        user_data_dir = config.get('user_data_dir')
        wallet = config.get('wallet')
        
        # 檢查必要設定項是否存在
        missing_configs = []
        if not private_key: missing_configs.append('private_key')
        if not metamask_pasw: missing_configs.append('metamask_pasw')
        if not chrome_path: missing_configs.append('chrome_path')
        if not chromedriver_path: missing_configs.append('chromedriver_path')
        if not user_data_dir: missing_configs.append('user_data_dir')
        if not wallet: missing_configs.append('wallet')
        
        if missing_configs:
            raise ValueError(f"缺少必要的設定項: {', '.join(missing_configs)}")
        
        return private_key, metamask_pasw, chrome_path, chromedriver_path, user_data_dir, wallet
    except FileNotFoundError:
        raise FileNotFoundError("找不到config.json檔案，請先建立該檔案並填入必要的設定項")
    except json.JSONDecodeError:
        raise ValueError("config.json檔案格式錯誤，請確保其為有效的JSON格式")
    except Exception as e:
        raise Exception(f"載入設定時發生錯誤: {e}")

try:
    # 載入設定
    PRIVATE_KEY, METAMASK_PASSWORD, CHROME_PATH, CHROMEDRIVER_PATH, USER_DATA_DIR, WALLET = load_config()
except Exception as e:
    print(f"錯誤: {e}")
    print("程式將結束")
    import sys
    sys.exit(1)

# 寵物篩選條件: [{技能}, 可接受最高價格]
PET_FILTERS = [
    [{"Magnet Effect"}, 385501],
    [{"Auto Buff"}, 385501],
    [{"Expanded Auto Move", "Auto Move"}, 100000],
    [set({}), 40000]  # 完全不符合
]

# 多裝備監控模式的預設價格上限
# 若EQUIPMENT_MONITOR_LIST中的裝備沒有指定價格，則使用此值
DEFAULT_EQUIPMENT_PRICE_LIMIT = 380000

# 多裝備監控列表：設定要監控的裝備名稱及對應的價格上限
# 格式: "裝備名稱": 價格上限
# 使用方式:
#   1. 使用 python main.py --mode multi_equipment 啟動多裝備監控模式
#   2. 系統會同時監控下列所有裝備
#   3. 當市場上出現包含下列名稱的裝備，且價格低於設定的上限時，將自動購買
#   4. 若某裝備的價格上限設為None，則會使用DEFAULT_EQUIPMENT_PRICE_LIMIT作為上限
EQUIPMENT_MONITOR_LIST = {
    "Golden Clover Belt": 200000,
    "Noble Ifia's Ring": None,
    "Crystal Ventus Badge": None,
    "Badge of": None,
    "Gold Maple Leaf": None,
    "Condensed Power Crystal": 100000,
    "Aquatic Letter Eye Accessory": 100000,
    "Black Bean Mark": None,
    "Will o' the Wisps": None,
    # 可以新增更多裝備和對應的價格上限
} 