import time
import json
import cloudscraper
import requests
from datetime import datetime, timedelta, timezone
from eth_account import Account
from eth_account.messages import encode_typed_data
import config
from driver import get_cookies_from_selenium

def fetch_url_using_cloudscraper(method: str, url: str, payload=None):
    """使用cloudscraper發送請求並處理錯誤"""
    scraper = cloudscraper.create_scraper()
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

def send_post_with_cookies(url, post_data, cookies):
    """使用 requests 發送帶有 Cookie 的 POST 請求"""
    scraper = cloudscraper.create_scraper()
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    response = scraper.post(url, json=post_data, cookies=cookies, headers=headers)
    return response

def get_transaction_result(transactionId, cookies):
    """取得交易結果"""
    transactionId = transactionId.replace(":", "%3A")
    url = f"https://msu.io/marketplace/api/marketplace/transaction/{transactionId}/result"

    scraper = cloudscraper.create_scraper()
    response = scraper.get(url, cookies=cookies)

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
    url = "https://msu.io/marketplace/api/marketplace/explore/items"
    fetch_amount = 7
    payload = {
        "filter": {
            "categoryNo": 1000401001,
            "price": {"min": 0, "max": 10000000000},
        },
        "sorting": "ExploreSorting_RECENTLY_LISTED",
        "paginationParam": {"pageNo": 1, "pageSize": fetch_amount},
    }

    return fetch_url_using_cloudscraper("post", url, payload)

def query_equipment(name = None):
    """查詢裝備列表"""
    url = "https://msu.io/marketplace/api/marketplace/explore/items"
    fetch_amount = 5
    payload = {
        "filter": {
            "name": name,
            "categoryNo": 0,
            "price": {"min": 0, "max": 10000000000},
            "level": {"min": 0, "max": 250},
            "starforce": {"min": 0, "max": 25},
            "potential": {"min": 0, "max": 4},
            "bonusPotential": {"min": 0, "max": 4},
        },
        "sorting": "ExploreSorting_LOWEST_PRICE",
        "paginationParam": {"pageNo": 1, "pageSize": fetch_amount},
    }

    return fetch_url_using_cloudscraper("post", url, payload)

def query_equipment_batch():
    """查詢所有最近上架的裝備"""
    url = "https://msu.io/marketplace/api/marketplace/explore/items"
    fetch_amount = 135  # 一次查詢的數量
    payload = {
        "filter": {
            "name": None,  # 不指定具體名稱
            "categoryNo": 0,
            "price": {"min": 0, "max": 10000000000},
            "level": {"min": 0, "max": 250},
            "starforce": {"min": 0, "max": 25},
            "potential": {"min": 0, "max": 4},
            "bonusPotential": {"min": 0, "max": 4},
        },
        "sorting": "ExploreSorting_RECENTLY_LISTED",  # 按最近上架排序
        "paginationParam": {"pageNo": 1, "pageSize": fetch_amount},
    }

    return fetch_url_using_cloudscraper("post", url, payload)

def get_singal_pet_skill_info(tokenId: int):
    """取得單個寵物技能資訊"""
    url = f"https://msu.io/marketplace/api/marketplace/items/{tokenId}"

    response = fetch_url_using_cloudscraper("get", url)
    if response is None:
        return None
    else:
        pet_skills = response["item"]["pet"]["petSkills"]
        return pet_skills

def buy_item_api(driver, tokenId, tokenAmount):
    """購買物品API"""
    # 計算時間戳記
    current_time = datetime.now(timezone.utc)
    listing_time = int(current_time.timestamp())  # 秒級時間戳記
    expiration_time = int((current_time + timedelta(days=1)).timestamp())  # 一天後
    salt = int(current_time.timestamp() * 1000)  # 毫秒級時間戳記

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
            "tokenAddress": config.TOKEN_ADDRESS.lower(),
            "tokenAmount": int(tokenAmount),
            "nftAddress": config.NFT_ADDRESS.lower(),
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
            "tokenAddress": config.TOKEN_ADDRESS,
            "tokenAmount": str(full_message["message"]["tokenAmount"]),
            "nftAddress": config.NFT_ADDRESS,
            "nftTokenId": str(full_message["message"]["nftTokenId"]),
            "salt": str(full_message["message"]["salt"]), 
        },
        "orderSign": "0x" + signature.signature.hex(),
    }

    url = f"https://msu.io/marketplace/api/marketplace/items/{tokenId}/buy" 

    cookies = get_cookies_from_selenium(driver)

    # 發送 POST 請求
    response = send_post_with_cookies(url, post_data, cookies)

    # 檢查 HTTP 狀態碼
    try:
        response.raise_for_status()
        # 將返回結果解析為 JSON
        result = response.json()
        transactionId = result["transactionId"]
        print(transactionId)

        transaction_result_code = get_transaction_result(transactionId, cookies)
        for _ in range(6):
            if transaction_result_code == 2:
                return True
            else:
                time.sleep(1.5)

        return False

    except json.JSONDecodeError as e:
        print("JSON解析錯誤:", e)
        return False
    except Exception as e:
        print(f"HTTP錯誤 {response.status_code}: {response.text}")
        return False 