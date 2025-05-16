from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import config

def setup_driver():
    """設定 Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.binary_location = config.CHROME_PATH
    chrome_options.add_argument(f"--user-data-dir={config.USER_DATA_DIR}")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--start-maximized")
    prefs = {
        "profile.managed_default_content_settings.images": 2,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    # chrome_options.add_argument("--headless")  

    service = Service(executable_path=config.CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def connect_wallet_to_website(driver):
    """連接錢包到網站"""
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//a[text()='Inventory']"))
        )                          
        return True
    except:
        print("目前未連線到網站...開始自動連線")

        try:
            connect_button = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Connect']"))
            )
            print("找到連線按鈕")
            connect_button.click()

            connect_metamask_btn = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div/div[2]/div/div/button"))
            )
            connect_metamask_btn.click()

            while True:
                if(len(driver.window_handles) > 2):
                    break

            driver.switch_to.window(driver.window_handles[-1])
            driver.maximize_window()
        except:
            return True
        
        # 找密碼輸入框
        try:
            pas_input = WebDriverWait(driver, 6).until(
                    EC.element_to_be_clickable((By.ID, 'password'))
                )
            pas_input.send_keys(config.METAMASK_PASSWORD) 
            pas_input.send_keys(Keys.ENTER)
            print("密碼輸入完成")
        except:
            print("未找到密碼輸入框")

            # 找確認按鈕
            try:
                connect_button = WebDriverWait(driver, 6).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='確認']"))
                )
                connect_button.click()
                print("找到確認按鈕")
            except:
                print("未找到確認按鈕")

        try:
            while True:
                try:
                    WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, "//h2[text()='Signature request']"))
                    )
                    break
                except:
                    driver.switch_to.window(driver.window_handles[-1])
                
            driver.maximize_window()
            confirm_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='確認']"))
                )
            confirm_button.click()
            print("連線網站成功")
            driver.switch_to.window(driver.window_handles[0])
            return True
        except Exception as e:
            print(e)
            print("連線網站失敗")
            return False

def get_cookies_from_selenium(driver):
    """從 Selenium 取得 Cookie，並轉換為 requests 可用的格式"""
    cookies = driver.get_cookies()
    cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    return cookie_dict

def initialize_driver():
    """初始化 ChromeDriver 並連接到網站"""
    driver = setup_driver()
    driver.switch_to.window(driver.window_handles[0])
    driver.get(f"https://msu.io/marketplace/inventory/{config.WALLET}?tab=onsale")

    if connect_wallet_to_website(driver):
        print("初始化完成")
        return driver
    else:
        print("初始化失敗")
        driver.quit()
        return None 