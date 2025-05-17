import time
import json
import cloudscraper
import requests
import threading
from datetime import datetime, timedelta, timezone
from eth_account import Account
from eth_account.messages import encode_typed_data, encode_defunct
import config

# 全局變數，保存已認證的scraper實例
_AUTHENTICATED_SCRAPER = None
_LAST_AUTH_TIME = None
_REGULAR_SCRAPER = None
_AUTH_LOCK = threading.Lock()  # 用於確保認證操作的線程安全

# 初始化認證（在程式啟動時調用）
def initialize_authentication():
    """初始化認證，預先獲取認證會話"""
    global _AUTHENTICATED_SCRAPER
    try:
        print("正在初始化認證會話...")
        _AUTHENTICATED_SCRAPER = create_authenticated_scraper()
        print("認證會話初始化完成")
        return True
    except Exception as e:
        print(f"初始化認證失敗: {e}")
        return False

# 檢查JWT是否有效
def is_jwt_valid(scraper):
    """檢查JWT憑證是否有效
    
    Args:
        scraper: 要檢查的scraper實例
        
    Returns:
        True: JWT有效
        False: JWT無效或丟失
    """
    if scraper is None:
        return False
        
    try:
        # 使用API檢查認證狀態
        test_url = "https://msu.io/api/bff/users/me"
        response = scraper.get(test_url, allow_redirects=False)
        
        # 檢查回應內容是否包含JWT錯誤
        response_text = response.text
        if "Jwt is missing" in response_text:
            print("JWT 憑證過期或丟失")
            return False
        else:
            # 其他情況認為認證有效
            return True
    except Exception as e:
        print(f"檢查JWT狀態時出錯: {e}")
        return False

# 檢查認證狀態並在需要時重新驗證
def check_and_refresh_authentication():
    """檢查認證狀態，如果過期則重新認證"""
    global _AUTHENTICATED_SCRAPER
    
    with _AUTH_LOCK:  # 使用鎖，確保同一時間只有一個線程修改認證狀態
        if _AUTHENTICATED_SCRAPER is None:
            print("認證會話不存在，正在創建新會話...")
            try:
                _AUTHENTICATED_SCRAPER = create_authenticated_scraper()
                print("已創建新的認證會話")
                return True
            except Exception as e:
                print(f"創建認證會話失敗: {e}")
                return False
        
        # 使用共用函數檢查JWT有效性
        if is_jwt_valid(_AUTHENTICATED_SCRAPER):
            return True
        else:
            print("重新認證中...")
            try:
                _AUTHENTICATED_SCRAPER = create_authenticated_scraper()
                return True
            except Exception:
                print("重新認證失敗")
                return False

# 創建或獲取普通scraper（不需認證）
def get_regular_scraper():
    """獲取普通的scraper實例（不需認證）"""
    global _REGULAR_SCRAPER
    if _REGULAR_SCRAPER is None:
        _REGULAR_SCRAPER = cloudscraper.create_scraper()
    return _REGULAR_SCRAPER

def create_authenticated_scraper():
    """創建已認證的scraper實例，或返回現有的有效實例"""
    global _AUTHENTICATED_SCRAPER, _LAST_AUTH_TIME
    
    # 檢查是否已有有效的scraper實例
    if _AUTHENTICATED_SCRAPER is not None:
        # 使用共用函數檢查JWT有效性
        if is_jwt_valid(_AUTHENTICATED_SCRAPER):
            return _AUTHENTICATED_SCRAPER
        else:
            print("重新登入中...")
    
    # 建立新的scraper實例並進行認證
    scraper = cloudscraper.create_scraper()
    
    # 使用config模組讀取設定，保持一致性
    WALLET_ADDRESS = config.WALLET
    PRIVATE_KEY = config.PRIVATE_KEY
    RPC_ENDPOINT = "https://msu.io/marketplace/api/gateway/v1"
    
    try:
        # 1. 拿 challenge message
        msg_res = scraper.post(f"{RPC_ENDPOINT}/web/message", json={"address": WALLET_ADDRESS})
        msg_res.raise_for_status()
        challenge = msg_res.json()["message"]
        print(f"收到挑戰訊息")
        
        # 2. 簽名
        eip191_msg = encode_defunct(text=challenge)
        signed = Account.sign_message(eip191_msg, private_key=PRIVATE_KEY)
        signature = signed.signature.hex()
        print(f"生成簽名: 0x{signature[:10]}...")
        
        # 3. 登入
        auth_payload = {
            "address": WALLET_ADDRESS,
            "signature": "0x" + signature,
            "walletType": "WALLET_TYPE_METAMASK"
        }
        auth_res = scraper.post(f"{RPC_ENDPOINT}/web/signin-wallet", json=auth_payload)
        
        # 顯示詳細錯誤
        if auth_res.status_code != 200:
            print(f"認證失敗: {auth_res.status_code}")
            print(f"錯誤內容: {auth_res.text}")
            raise Exception(f"認證失敗: {auth_res.status_code}")
            
        auth_res.raise_for_status()
        print("認證成功，已取得認證cookies")
        
        # 更新全局變數
        _AUTHENTICATED_SCRAPER = scraper
        _LAST_AUTH_TIME = datetime.now()
        
        return scraper
        
    except Exception as e:
        print(f"認證過程發生錯誤: {e}")
        raise

def fetch_url_using_cloudscraper(method: str, url: str, payload=None, need_auth=False):
    """使用cloudscraper發送請求並處理錯誤
    
    Args:
        method: 請求方法，"get" 或 "post"
        url: 請求URL
        payload: POST請求的數據
        need_auth: 是否需要認證，預設為False
    """
    # 根據是否需要認證選擇scraper
    scraper = create_authenticated_scraper() if need_auth else get_regular_scraper()
    
    try:
        if method == "post":
            response = scraper.post(url, json=payload)
        else:
            response = scraper.get(url)
        response.raise_for_status()  # 如果不是 200，會觸發 HTTPError
        return response.json()  # 成功時回傳資料
    except cloudscraper.exceptions.CloudflareChallengeError:
        print("遇到Cloudflare驗證。重試中...")
        return None
    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            print("403 拒絕存取。30秒後重試...")
            time.sleep(30)
        elif response.status_code == 429:
            print("請求過多。120秒後重試...")
            time.sleep(120)
        else:
            print(f"HTTP錯誤: {e}")
        return None
    except Exception as e:
        print(f"發生意外錯誤: {e}")
        return None

def get_transaction_result(transactionId):
    """取得交易結果"""
    transactionId = transactionId.replace(":", "%3A")
    url = f"https://msu.io/marketplace/api/marketplace/transaction/{transactionId}/result"

    # 交易結果查詢需要認證
    scraper = create_authenticated_scraper()
    response = scraper.get(url)

    try:
        response.raise_for_status()
        # 將返回結果解析為 JSON
        result = response.json()
        
        return result["code"]
    except json.JSONDecodeError as e:
        print("取得交易結果失敗")
        print("JSON解析錯誤:", e)
    except Exception as e:
        print("取得交易結果失敗")
        print(f"HTTP錯誤 {response.status_code}: {response.text}")

def fetch_all_pets():
    """取得所有寵物列表"""
    # 每次獲取前檢查認證狀態
    check_and_refresh_authentication()
    
    url = "https://msu.io/marketplace/api/marketplace/explore/items"
    fetch_amount = 15
    payload = {
        "filter": {
            "categoryNo": 1000401001,
            "price": {"min": 0, "max": 10000000000},
        },
        "sorting": "ExploreSorting_RECENTLY_LISTED",
        "paginationParam": {"pageNo": 1, "pageSize": fetch_amount},
    }

    # 瀏覽市場不需要認證
    return fetch_url_using_cloudscraper("post", url, payload, need_auth=False)

def query_equipment_batch():
    """查詢所有最近上架的裝備"""
    # 每次獲取前檢查認證狀態
    check_and_refresh_authentication()
    
    url = "https://msu.io/marketplace/api/marketplace/explore/items"
    fetch_amount = 135  # 一次查詢的數量
    payload = {
        "filter": {},
        "sorting": "ExploreSorting_RECENTLY_LISTED",  # 按最近上架排序
        "paginationParam": {"pageNo": 1, "pageSize": fetch_amount},
    }

    # 批量查詢不需要認證
    return fetch_url_using_cloudscraper("post", url, payload, need_auth=False)

def get_singal_pet_skill_info(tokenId: int):
    """取得單個寵物技能資訊"""
    url = f"https://msu.io/marketplace/api/marketplace/items/{tokenId}"

    # 查詢單品資訊不需要認證
    response = fetch_url_using_cloudscraper("get", url, need_auth=False)
    if response is None:
        return None
    else:
        pet_skills = response["item"]["pet"]["petSkills"]
        return pet_skills

def buy_item_api(tokenId, tokenAmount):
    """購買物品API"""
    # 計算時間戳記
    current_time = datetime.now(timezone.utc)
    listing_time = int(current_time.timestamp())  # 秒級時間戳記
    expiration_time = int((current_time + timedelta(days=1)).timestamp())  # 一天後
    salt = int(current_time.timestamp() * 1000)  # 毫秒級時間戳記
    # 合約地址
    TOKEN_ADDRESS = "0x07E49Ad54FcD23F6e7B911C2068F0148d1827c08"
    NFT_ADDRESS = "0x43DCff2A0cedcd5e10e6f1c18b503498dDCe60d5"

    # 建構 EIP-712 結構化資料
    full_message = {
        "domain": {
            "name": "Marketplace",
            "version": "1.0",
            "chainId": 68414,
            "verifyingContract": "0xf1c82c082af3de3614771105f01dc419c3163352",
        },
        "primaryType": "Order",
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "Order": [
                {"name": "isSeller", "type": "uint256"},  # 維持原狀
                {"name": "maker", "type": "address"},
                {"name": "listingTime", "type": "uint256"},
                {"name": "expirationTime", "type": "uint256"},
                {"name": "tokenAddress", "type": "address"},
                {"name": "tokenAmount", "type": "uint256"},
                {"name": "nftAddress", "type": "address"},
                {"name": "nftTokenId", "type": "uint256"},
                {"name": "salt", "type": "uint256"},
            ],
        },
        "message": {
            "isSeller": 0,  # 簽名時使用數值 0
            "maker": config.WALLET.lower(),
            "listingTime": listing_time,
            "expirationTime": expiration_time,
            "tokenAddress": TOKEN_ADDRESS.lower(),
            "tokenAmount": int(tokenAmount),
            "nftAddress": NFT_ADDRESS.lower(),
            "nftTokenId": int(tokenId),  # 轉換為整數
            "salt": salt,
        },
    }

    # 簽名
    encoded_message = encode_typed_data(full_message=full_message)
    signature = Account.sign_message(encoded_message, config.PRIVATE_KEY)

    # 組裝 POST 資料
    post_data = {
        "order": {
            "isSeller": False,  # 修改為bool False
            "maker": config.WALLET,
            "listingTime": str(full_message["message"]["listingTime"]),
            "expirationTime": str(full_message["message"]["expirationTime"]),
            "tokenAddress": TOKEN_ADDRESS,
            "tokenAmount": str(full_message["message"]["tokenAmount"]),
            "nftAddress": NFT_ADDRESS,
            "nftTokenId": str(full_message["message"]["nftTokenId"]),
            "salt": str(full_message["message"]["salt"]), 
        },
        "orderSign": "0x" + signature.signature.hex(),
    }

    url = f"https://msu.io/marketplace/api/marketplace/items/{tokenId}/buy" 

    # 購買需要認證
    scraper = create_authenticated_scraper()
    response = scraper.post(url, json=post_data)

    # 檢查 HTTP 狀態碼
    try:
        response.raise_for_status()
        # 將返回結果解析為 JSON
        result = response.json()
        transactionId = result["transactionId"]
        print(transactionId)

        for _ in range(6):
            transaction_result_code = get_transaction_result(transactionId)
            if transaction_result_code == 1:
                print("交易處理中...")
                time.sleep(1)
            elif transaction_result_code == 2:
                # Transaction status: 2 means success
                print("交易成功")
                return True
            else:
                print("交易失敗")
                return False

    except json.JSONDecodeError as e:
        print("JSON解析錯誤:", e)
        return False
    except Exception as e:
        print(f"HTTP錯誤 {response.status_code}: {response.text}")
        return False 

def get_wallet_balance():
    """獲取用戶錢包餘額
    
    返回：
        成功時返回餘額（以遊戲幣為單位）
        失敗時返回None
    """
    url = f"https://msu.io/marketplace/api/gateway/bcbackend/next-meso/balance/{config.WALLET}"
    
    try:
        # 使用無需認證的scraper
        scraper = get_regular_scraper()
        response = scraper.get(url)
        response.raise_for_status()
        
        # 解析返回的餘額
        result = response.json()
        balance_wei = result.get("balance", "0")
        
        # 轉換為遊戲幣單位
        balance = int(int(balance_wei) / config.WEI_PER_ETHER)
        
        return balance
    except Exception as e:
        print(f"獲取錢包餘額失敗: {e}")
        return None 