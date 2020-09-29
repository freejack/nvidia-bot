import time
import hashlib

from chromedriver_py import binary_path  # this will get you the path variable
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

from notifications.notifications import NotificationHandler
from utils.logger import log
from utils import selenium_utils
from utils.selenium_utils import options, enable_headless, wait_for_element


BASE_URL = "https://www.amazon.com/"
LOGIN_URL = "https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F%3Fref_%3Dnav_custrec_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&"
CART_URL = "https://www.amazon.com/gp/aod/ajax/ref=dp_olp_NEW_mbc?asin="

class AmazonThird:
    def __init__(self, username, password, item_url, headless=False):
        self.notification_handler = NotificationHandler()
        if headless:
            enable_headless()
        h = hashlib.md5(item_url.encode()).hexdigest()
        options.add_argument(f"user-data-dir=.profile-amz-{h}")
        self.driver = webdriver.Chrome(executable_path=binary_path, options=options)
        self.wait = WebDriverWait(self.driver, 10)
        self.username = username
        self.password = password
        self.driver.get(BASE_URL)
        if self.is_logged_in():
            log.info("Already logged in")
        else:
            self.login()
            time.sleep(15)

    def is_logged_in(self):
        try:
            text = wait_for_element(self.driver, "nav-link-accountList").text
            return "Hello, Sign in" not in text
        except Exception:
            return False

    def login(self):
        self.driver.get(LOGIN_URL)
        self.driver.find_element_by_xpath('//*[@id="ap_email"]').send_keys(
            self.username + Keys.RETURN
        )
        self.driver.find_element_by_xpath('//*[@id="ap_password"]').send_keys(
            self.password + Keys.RETURN
        )

        log.info(f"Logged in as {self.username}")

    def run_item(self, item_url, price_limit=1000, delay=3):
        log.info(f"Loading page: {CART_URL + item_url}")
        self.driver.get(CART_URL + item_url)
        item = ""
        in_stock = False
        try:
            product_title = self.wait.until(
                presence_of_element_located((By.ID, "aod-asin-title-text"))
            )
            log.info(f"Loaded page for {product_title.text}")
            item = product_title.text[:100].strip()
        except:
            log.error(self.driver.current_url)

        try:
            availability = self.driver.find_element_by_xpath("//*[contains(text(), 'from seller Amazon')]").text
            in_stock = True
            log.info(f"Initial availability message is: {availability}")
        except:
            log.info("not found")

        while not in_stock:
            try:
                self.driver.refresh()
                log.info(f"Refreshing for {item}...")

                try:
                    availability = self.driver.find_element_by_xpath("//*[contains(text(), 'from seller Amazon')]").text
                    in_stock = True
                    log.info(f"Initial availability message is: {availability}")
                except:
                    log.info("not found")

                time.sleep(delay)
            except TimeoutException as _:
                log.warn("A polling request timed out. Retrying.")

        log.info("Item in stock!")
        
        self.notification_handler.send_notification(
            f"Item was found:" + item_url
        )
        self.buy_now()

#        try:
#            price_str = self.driver.find_element_by_id("priceblock_ourprice").text
#        except NoSuchElementException as _:
#            price_str = self.driver.find_element_by_id("priceblock_dealprice").text
#        price_int = int(round(float(price_str.strip("$"))))
#        if price_int < price_limit:
#            log.info(f"Attempting to buy item for {price_int}")
#            self.buy_now()
#        else:
#        self.notification_handler.send_notification(
#            f"Item was found, but price is at {price_int} so we did not buy it."
#        )
#        log.info(f"Price was too high {price_int}")

    def buy_now(self):
        log.info("Clicking 'Buy Now'.")
                                #product_link = price_str2.find_element(
                       #     By.XPATH, (".//preceding-sibling::td[2]//a")
                        #)
        text_element = self.driver.find_element_by_xpath("//*[contains(text(), 'from seller Amazon')]")
        log.info(text_element)
        #self.driver.find_element_by_xpath(
        #    './/*[@id="buy-now-button"]').click()
        #)
        atc_button = text_element.find_element(
            By.XPATH, ("./../../input")
        )
        log.info("text:" + atc_button.text)
        atc_button.click()

        selenium_utils.wait_for_any_title(self.driver, ["Amazon.com Shopping Cart"], 10)        
        #self.wait.until(ExpectedConditions.titleContains("Amazon.com Shopping Cart"));
        log.info("Shopping Cart Loaded!")

        self.driver.find_element_by_id(
            'hlb-ptc-btn-native'
        ).click()

        selenium_utils.wait_for_any_title(self.driver, ["Amazon.com Checkout", "Amazon Sign-In"], 10)    
        if self.driver.title == "Amazon Sign-In":
            time.sleep(2)
            self.driver.find_element_by_xpath('//input[@id="ap_password"]').send_keys(
                self.password + Keys.RETURN
            )

        selenium_utils.wait_for_any_title(self.driver, ["Amazon.com Checkout"], 10)  
# <input type="password" maxlength="1024" id="ap_password" name="password" tabindex="2" class="a-input-text a-span12 auth-autofocus auth-required-field">
# <input id="signInSubmit" tabindex="4" class="a-button-input" type="submit" aria-labelledby="auth-signin-button-announce">
        
        # Allow time for button to appear
        time.sleep(.5)
        log.info("Clicking 'Place Your Order'.")
        self.driver.find_element_by_name(
            "placeYourOrder1"
        ).click()

        self.notification_handler.send_notification(
            f"Item was purchased! Check your Amazon account."
        )

    def force_stop(self):
        self.driver.stop_client()
